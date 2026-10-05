import { useEffect, useState } from "react"
import { useAuth } from "../../context/AuthContext"
import { userAPI, psicologoAPI } from "../../api/api"
import "./PacientePerfil.css"

function formatarDataParaInput(str) {
  if (!str) return ""
  // Banco retorna YYYY-MM-DD, input espera DD/MM/YYYY
  const [ano, mes, dia] = str.split("-")
  return dia && mes && ano ? `${dia}/${mes}/${ano}` : str
}

export default function PacientePerfil() {
  const { user, logout } = useAuth()

  // Dados pessoais
  const [dados,       setDados]       = useState({ username: "", email: "", data_nascimento: "" })
  const [salvandoDados, setSalvandoDados] = useState(false)
  const [sucessoDados,  setSucessoDados]  = useState("")
  const [erroDados,     setErroDados]     = useState("")

  // Senha
  const [senha,        setSenha]        = useState({ old_password: "", new_password: "", confirmar: "" })
  const [salvandoSenha, setSalvandoSenha] = useState(false)
  const [sucessoSenha,  setSucessoSenha]  = useState("")
  const [erroSenha,     setErroSenha]     = useState("")

  // Vínculo
  const [codigo,         setCodigo]         = useState("")
  const [vinculando,     setVinculando]      = useState(false)
  const [sucessoVinculo, setSucessoVinculo]  = useState("")
  const [erroVinculo,    setErroVinculo]     = useState("")
  const [psicologoId,    setPsicologoId]     = useState(null)

  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!user) return
    Promise.all([
      userAPI.get(user.id),
      psicologoAPI.getPsicologoDoPaciente(user.id).catch(() => ({ psicologo_id: null })),
    ]).then(([u, v]) => {
      setDados({
        username:        u.username || "",
        email:           u.email || "",
        data_nascimento: formatarDataParaInput(u.data_nascimento),
      })
      setPsicologoId(v.psicologo_id)
    }).finally(() => setLoading(false))
  }, [user])

  // ── Salvar dados pessoais ──
  async function handleSalvarDados(e) {
    e.preventDefault()
    setErroDados(""); setSucessoDados(""); setSalvandoDados(true)
    try {
      await userAPI.update(user.id, dados)
      setSucessoDados("Dados atualizados com sucesso!")
      setTimeout(() => setSucessoDados(""), 3000)
    } catch (err) {
      setErroDados(err?.detail || "Erro ao atualizar dados.")
    } finally {
      setSalvandoDados(false)
    }
  }

  // ── Alterar senha ──
  async function handleSalvarSenha(e) {
    e.preventDefault()
    setErroSenha(""); setSucessoSenha("")
    if (senha.new_password !== senha.confirmar) {
      setErroSenha("As senhas não coincidem."); return
    }
    if (senha.new_password.length < 6) {
      setErroSenha("A nova senha deve ter pelo menos 6 caracteres."); return
    }
    setSalvandoSenha(true)
    try {
      await userAPI.changePassword(user.id, {
        old_password: senha.old_password,
        new_password: senha.new_password,
      })
      setSucessoSenha("Senha alterada com sucesso!")
      setSenha({ old_password: "", new_password: "", confirmar: "" })
      setTimeout(() => setSucessoSenha(""), 3000)
    } catch (err) {
      setErroSenha(err?.detail || "Erro ao alterar senha.")
    } finally {
      setSalvandoSenha(false)
    }
  }

  // ── Vincular psicólogo ──
  async function handleVincular(e) {
    e.preventDefault()
    if (!codigo.trim()) { setErroVinculo("Digite o código de vínculo."); return }
    setErroVinculo(""); setSucessoVinculo(""); setVinculando(true)
    try {
      await psicologoAPI.vincular({ paciente_id: user.id, codigo: codigo.trim() })
      setSucessoVinculo("Vinculado com sucesso! 🎉")
      setCodigo("")
      const v = await psicologoAPI.getPsicologoDoPaciente(user.id)
      setPsicologoId(v.psicologo_id)
    } catch (err) {
      setErroVinculo(err?.detail || "Código inválido ou já utilizado.")
    } finally {
      setVinculando(false)
    }
  }

  if (loading) return <div className="loading-screen">Carregando perfil...</div>

  return (
    <div className="perfil-page">
      <h1 className="perfil-titulo">👤 Meu Perfil</h1>

      {/* Avatar */}
      <div className="perfil-avatar-section">
        <div className="perfil-avatar">
          {dados.username?.[0]?.toUpperCase() || "U"}
        </div>
        <div>
          <p className="perfil-nome">{dados.username}</p>
          <p className="perfil-tipo">Paciente</p>
        </div>
      </div>

      <div className="perfil-grid">

        {/* ── Dados pessoais ── */}
        <section className="card">
          <h2 className="secao-titulo">📝 Dados pessoais</h2>
          <form onSubmit={handleSalvarDados}>
            <div className="input-group">
              <label>Nome</label>
              <input className="input" value={dados.username}
                onChange={e => setDados(d => ({ ...d, username: e.target.value }))}
                placeholder="Seu nome" required />
            </div>
            <div className="input-group">
              <label>Email</label>
              <input className="input" type="email" value={dados.email}
                onChange={e => setDados(d => ({ ...d, email: e.target.value }))}
                placeholder="seu@email.com" required />
            </div>
            <div className="input-group">
              <label>Data de nascimento</label>
              <input className="input" value={dados.data_nascimento}
                onChange={e => setDados(d => ({ ...d, data_nascimento: e.target.value }))}
                placeholder="DD/MM/AAAA" required />
            </div>

            {erroDados   && <p className="error-msg">{erroDados}</p>}
            {sucessoDados && <p className="sucesso-msg">{sucessoDados}</p>}

            <button className="btn btn-primary" style={{ width: "100%" }} disabled={salvandoDados}>
              {salvandoDados ? "Salvando..." : "Salvar alterações"}
            </button>
          </form>
        </section>

        {/* ── Alterar senha ── */}
        <section className="card">
          <h2 className="secao-titulo">🔒 Alterar senha</h2>
          <form onSubmit={handleSalvarSenha}>
            <div className="input-group">
              <label>Senha atual</label>
              <input className="input" type="password" value={senha.old_password}
                onChange={e => setSenha(s => ({ ...s, old_password: e.target.value }))}
                placeholder="••••••••" required />
            </div>
            <div className="input-group">
              <label>Nova senha</label>
              <input className="input" type="password" value={senha.new_password}
                onChange={e => setSenha(s => ({ ...s, new_password: e.target.value }))}
                placeholder="Mínimo 6 caracteres" required />
            </div>
            <div className="input-group">
              <label>Confirmar nova senha</label>
              <input className="input" type="password" value={senha.confirmar}
                onChange={e => setSenha(s => ({ ...s, confirmar: e.target.value }))}
                placeholder="Repita a nova senha" required />
            </div>

            {erroSenha   && <p className="error-msg">{erroSenha}</p>}
            {sucessoSenha && <p className="sucesso-msg">{sucessoSenha}</p>}

            <button className="btn btn-primary" style={{ width: "100%" }} disabled={salvandoSenha}>
              {salvandoSenha ? "Alterando..." : "Alterar senha"}
            </button>
          </form>
        </section>

        {/* ── Vínculo com psicólogo ── */}
        <section className="card perfil-vinculo">
          <h2 className="secao-titulo">🔗 Psicólogo vinculado</h2>
          {psicologoId ? (
            <div className="vinculo-ativo">
              <span className="vinculo-icon">✅</span>
              <div>
                <p className="vinculo-label">Você está vinculado a um psicólogo</p>
                <p className="vinculo-sub">Para desvincular, entre em contato com seu psicólogo.</p>
              </div>
            </div>
          ) : (
            <>
              <p className="vinculo-info">
                Insira o código fornecido pelo seu psicólogo para vincular sua conta e acessar a agenda.
              </p>
              <form onSubmit={handleVincular} style={{ marginTop: 16 }}>
                <div className="input-group">
                  <label>Código de vínculo</label>
                  <input className="input codigo-input" value={codigo}
                    onChange={e => setCodigo(e.target.value.toUpperCase())}
                    placeholder="Ex: ABC-123" maxLength={7} required />
                </div>
                {erroVinculo   && <p className="error-msg">{erroVinculo}</p>}
                {sucessoVinculo && <p className="sucesso-msg">{sucessoVinculo}</p>}
                <button className="btn btn-primary" style={{ width: "100%" }} disabled={vinculando}>
                  {vinculando ? "Vinculando..." : "Vincular"}
                </button>
              </form>
            </>
          )}
        </section>

      </div>
    </div>
  )
}