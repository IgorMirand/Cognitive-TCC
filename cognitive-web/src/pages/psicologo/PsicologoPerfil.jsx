import { useEffect, useState } from "react"
import { useAuth } from "../../context/AuthContext"
import { userAPI } from "../../api/api"
import "./PsicologoPerfil.css"

export default function PsicologoPerfil() {
  const { user, updateUser } = useAuth() // updateUser é opcional, veja handleSalvar

  const [form, setForm] = useState({ username: "", email: "", data_nascimento: "" })
  const [loading,  setLoading]  = useState(true)
  const [salvando, setSalvando] = useState(false)
  const [msg,      setMsg]      = useState({ tipo: "", texto: "" })

  const [senhaForm, setSenhaForm] = useState({ atual: "", nova: "", confirmar: "" })
  const [trocando,  setTrocando]  = useState(false)
  const [senhaMsg,  setSenhaMsg]  = useState({ tipo: "", texto: "" })

  useEffect(() => {
    if (!user) return
    userAPI.get(user.id)
      .then(r => {
        // ajuste se o backend retornar outro formato
        const u = r.user ?? r
        setForm({
          username:        u.username ?? "",
          email:           u.email ?? "",
          data_nascimento: u.data_nascimento ?? "",
        })
      })
      .catch(() => setMsg({ tipo: "erro", texto: "Não foi possível carregar o perfil." }))
      .finally(() => setLoading(false))
  }, [user?.id])

  function handleChange(e) {
    setForm(f => ({ ...f, [e.target.name]: e.target.value }))
  }

  function handleSenhaChange(e) {
    setSenhaForm(f => ({ ...f, [e.target.name]: e.target.value }))
  }

  async function handleSalvar(e) {
    e.preventDefault()
    setMsg({ tipo: "", texto: "" })
    setSalvando(true)
    try {
      await userAPI.update(user.id, form)
      if (typeof updateUser === "function") updateUser(form)
      setMsg({ tipo: "ok", texto: "Perfil atualizado!" })
    } catch (err) {
      setMsg({ tipo: "erro", texto: err?.detail || "Erro ao atualizar perfil." })
    } finally {
      setSalvando(false)
    }
  }

  async function handleTrocarSenha(e) {
    e.preventDefault()
    setSenhaMsg({ tipo: "", texto: "" })

    if (senhaForm.nova.length < 6)
      return setSenhaMsg({ tipo: "erro", texto: "A nova senha deve ter ao menos 6 caracteres." })
    if (senhaForm.nova !== senhaForm.confirmar)
      return setSenhaMsg({ tipo: "erro", texto: "As senhas não coincidem." })

    setTrocando(true)
    try {
      // TODO: confirmar nomes dos campos esperados por PUT /users/{id}/password
      await userAPI.changePassword(user.id, {
        senha_atual: senhaForm.atual,
        nova_senha:  senhaForm.nova,
      })
      setSenhaForm({ atual: "", nova: "", confirmar: "" })
      setSenhaMsg({ tipo: "ok", texto: "Senha alterada!" })
    } catch (err) {
      setSenhaMsg({ tipo: "erro", texto: err?.detail || "Erro ao alterar senha." })
    } finally {
      setTrocando(false)
    }
  }

  if (loading) return <div className="loading-screen">Carregando...</div>

  return (
    <div className="perfil-page">
      <header className="perfil-header">
        <div className="perfil-avatar">{form.username?.[0]?.toUpperCase() || "P"}</div>
        <div>
          <h1 className="perfil-titulo">{form.username || "Meu perfil"}</h1>
          <p className="perfil-sub">Psicólogo</p>
        </div>
      </header>

      <section className="card">
        <h2 className="secao-titulo">Dados pessoais</h2>
        <form onSubmit={handleSalvar}>
          <div className="input-group">
            <label>Nome</label>
            <input className="input" name="username" value={form.username}
              onChange={handleChange} required />
          </div>
          <div className="input-group">
            <label>Email</label>
            <input className="input" type="email" name="email" value={form.email}
              onChange={handleChange} required />
          </div>
          <div className="input-group">
            <label>Data de nascimento</label>
            <input className="input" name="data_nascimento" placeholder="DD/MM/AAAA"
              value={form.data_nascimento} onChange={handleChange} required />
          </div>

          {msg.texto && (
            <p className={msg.tipo === "erro" ? "error-msg" : "perfil-ok"}>{msg.texto}</p>
          )}

          <button className="btn btn-primary" style={{ marginTop: 8 }} disabled={salvando}>
            {salvando ? "Salvando..." : "💾 Salvar alterações"}
          </button>
        </form>
      </section>

      <section className="card">
        <h2 className="secao-titulo">Alterar senha</h2>
        <form onSubmit={handleTrocarSenha}>
          <div className="input-group">
            <label>Senha atual</label>
            <input className="input" type="password" name="atual" value={senhaForm.atual}
              onChange={handleSenhaChange} autoComplete="current-password" required />
          </div>
          <div className="input-group">
            <label>Nova senha</label>
            <input className="input" type="password" name="nova" value={senhaForm.nova}
              onChange={handleSenhaChange} autoComplete="new-password" required />
          </div>
          <div className="input-group">
            <label>Confirmar nova senha</label>
            <input className="input" type="password" name="confirmar" value={senhaForm.confirmar}
              onChange={handleSenhaChange} autoComplete="new-password" required />
          </div>

          {senhaMsg.texto && (
            <p className={senhaMsg.tipo === "erro" ? "error-msg" : "perfil-ok"}>{senhaMsg.texto}</p>
          )}

          <button className="btn btn-outline" style={{ marginTop: 8 }} disabled={trocando}>
            {trocando ? "Alterando..." : "🔒 Alterar senha"}
          </button>
        </form>
      </section>
    </div>
  )
}