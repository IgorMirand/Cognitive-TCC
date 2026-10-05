import { useEffect, useState } from "react"
import { useAuth } from "../../context/AuthContext"
import { psicologoAPI } from "../../api/api"
import "./PsicologoAtividades.css"

// Aceita tupla [id, titulo, descricao] ou objeto { id, titulo, descricao }.
// Ajuste aqui conforme o retorno real de GET /atividades.
function normalizar(a) {
  if (Array.isArray(a)) return { id: a[0], titulo: a[1], descricao: a[2] ?? "" }
  return { id: a.id, titulo: a.titulo ?? a.nome ?? "", descricao: a.descricao ?? "" }
}

export default function PsicologoAtividades() {
  const { user } = useAuth()

  const [atividades, setAtividades] = useState([])
  const [loading,    setLoading]    = useState(true)
  const [busca,      setBusca]      = useState("")
  const [erro,       setErro]       = useState("")

  const [form,     setForm]     = useState({ titulo: "", descricao: "" })
  const [salvando, setSalvando] = useState(false)
  const [formAberto, setFormAberto] = useState(false)

  const [removendo, setRemovendo] = useState(null)

  async function carregar() {
    try {
      const r = await psicologoAPI.listarAtividades()
      const lista = Array.isArray(r) ? r : (r.atividades || [])
      setAtividades(lista.map(normalizar))
    } catch {
      setErro("Não foi possível carregar as atividades.")
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { carregar() }, [])

  function handleChange(e) {
    setForm(f => ({ ...f, [e.target.name]: e.target.value }))
  }

  async function handleCriar(e) {
    e.preventDefault()
    if (!form.titulo.trim()) return
    setErro("")
    setSalvando(true)
    try {
      // TODO: confirmar o schema de POST /atividades
      await psicologoAPI.criarAtividade({
        titulo:       form.titulo.trim(),
        descricao:    form.descricao.trim(),
        psicologo_id: user?.id,
      })
      setForm({ titulo: "", descricao: "" })
      setFormAberto(false)
      await carregar()
    } catch (err) {
      setErro(err?.detail || "Erro ao criar atividade.")
    } finally {
      setSalvando(false)
    }
  }

  async function handleDeletar(a) {
    if (!window.confirm(`Excluir a atividade "${a.titulo}"?`)) return
    setErro("")
    setRemovendo(a.id)
    try {
      await psicologoAPI.deletarAtividade(a.id)
      setAtividades(prev => prev.filter(x => x.id !== a.id))
    } catch (err) {
      setErro(err?.detail || "Erro ao excluir atividade.")
    } finally {
      setRemovendo(null)
    }
  }

  const filtradas = atividades.filter(a =>
    `${a.titulo} ${a.descricao}`.toLowerCase().includes(busca.toLowerCase())
  )

  if (loading) return <div className="loading-screen">Carregando atividades...</div>

  return (
    <div className="ativ-page">
      <header className="ativ-header">
        <div>
          <h1 className="ativ-titulo">🏃 Atividades</h1>
          <p className="ativ-sub">
            {atividades.length} atividade{atividades.length !== 1 ? "s" : ""} cadastrada{atividades.length !== 1 ? "s" : ""}
          </p>
        </div>
        <button className="btn btn-primary" onClick={() => setFormAberto(v => !v)}>
          {formAberto ? "Cancelar" : "+ Nova atividade"}
        </button>
      </header>

      {formAberto && (
        <form className="card ativ-form" onSubmit={handleCriar}>
          <h2 className="secao-titulo">Nova atividade</h2>
          <div className="input-group">
            <label>Título</label>
            <input className="input" name="titulo" value={form.titulo}
              onChange={handleChange} placeholder="Ex.: Respiração diafragmática" required />
          </div>
          <div className="input-group">
            <label>Descrição</label>
            <textarea className="input" name="descricao" rows={3} value={form.descricao}
              onChange={handleChange} placeholder="Como o paciente deve realizar..."
              style={{ resize: "vertical" }} />
          </div>
          <button className="btn btn-primary" disabled={salvando || !form.titulo.trim()}>
            {salvando ? "Salvando..." : "💾 Salvar"}
          </button>
        </form>
      )}

      {erro && <p className="error-msg">{erro}</p>}

      {atividades.length > 0 && (
        <div className="busca-wrapper">
          <span className="busca-icon">🔍</span>
          <input className="input busca-input" placeholder="Buscar atividade..."
            value={busca} onChange={e => setBusca(e.target.value)} />
        </div>
      )}

      {atividades.length === 0 ? (
        <div className="card ativ-empty">
          <p style={{ fontSize: "3rem" }}>🏃</p>
          <h3>Nenhuma atividade cadastrada</h3>
          <p>Crie atividades para indicar aos seus pacientes.</p>
        </div>
      ) : filtradas.length === 0 ? (
        <p className="empty-text">Nenhuma atividade encontrada.</p>
      ) : (
        <div className="ativ-grid">
          {filtradas.map(a => (
            <article key={a.id} className="card ativ-card">
              <div className="ativ-card-corpo">
                <h3 className="ativ-card-titulo">{a.titulo}</h3>
                {a.descricao && <p className="ativ-card-desc">{a.descricao}</p>}
              </div>
              <button className="ativ-del" onClick={() => handleDeletar(a)}
                disabled={removendo === a.id} aria-label={`Excluir ${a.titulo}`}>
                {removendo === a.id ? "..." : "🗑️"}
              </button>
            </article>
          ))}
        </div>
      )}
    </div>
  )
}