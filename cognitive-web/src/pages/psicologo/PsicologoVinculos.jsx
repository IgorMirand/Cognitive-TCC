import { useEffect, useState } from "react"
import { useAuth } from "../../context/AuthContext"
import { psicologoAPI } from "../../api/api"
import "./PsicologoVinculos.css"

export default function PsicologoVinculos() {
  const { user } = useAuth()

  const [codigo,    setCodigo]    = useState("")
  const [gerando,   setGerando]   = useState(false)
  const [copiado,   setCopiado]   = useState(false)
  const [erro,      setErro]      = useState("")

  const [email,     setEmail]     = useState("")
  const [enviando,  setEnviando]  = useState(false)
  const [conviteMsg, setConviteMsg] = useState({ tipo: "", texto: "" })

  const [pacientes, setPacientes] = useState([])
  const [loading,   setLoading]   = useState(true)

  useEffect(() => {
    if (!user) return
    psicologoAPI.pacientes(user.id)
      .then(d => setPacientes(d.pacientes || []))
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [user])

  async function handleGerar() {
    setErro("")
    setCopiado(false)
    setGerando(true)
    try {
      const r = await psicologoAPI.gerarCodigo(user.id)
      // ajuste aqui se o backend retornar outro formato
      const c = typeof r === "string" ? r : (r.codigo ?? r.code ?? "")
      if (!c) throw new Error("Resposta sem código")
      setCodigo(c)
    } catch (err) {
      setErro(err?.detail || "Não foi possível gerar o código.")
    } finally {
      setGerando(false)
    }
  }

  async function handleCopiar() {
    try {
      await navigator.clipboard.writeText(codigo)
      setCopiado(true)
      setTimeout(() => setCopiado(false), 2000)
    } catch {
      setErro("Não foi possível copiar. Selecione e copie manualmente.")
    }
  }

  function mensagemConvite() {
    return `Olá! Use o código ${codigo} no Cognitive para se vincular a mim como seu(sua) psicólogo(a).`
  }

  async function handleEnviarConvite(e) {
    e.preventDefault()
    if (!email.trim() || !codigo) return
    setEnviando(true)
    setConviteMsg({ tipo: "", texto: "" })
    try {
      // TODO: confirmar o payload esperado por /email/enviar_convite
      await psicologoAPI.enviarConvite({
        psicologo_id: user.id,
        email_destino: email.trim(),
        codigo,
      })
      setConviteMsg({ tipo: "ok", texto: "Convite enviado!" })
      setEmail("")
    } catch (err) {
      setConviteMsg({ tipo: "erro", texto: err?.detail || "Erro ao enviar convite." })
    } finally {
      setEnviando(false)
    }
  }

  return (
    <div className="vinc-page">
      <header className="vinc-header">
        <h1 className="vinc-titulo">🔗 Vínculos</h1>
        <p className="vinc-sub">Gere um código e compartilhe com o paciente para vinculá-lo a você.</p>
      </header>

      <section className="card vinc-codigo-card">
        <h2 className="secao-titulo">Código de vínculo</h2>

        {codigo ? (
          <>
            <div className="vinc-codigo">{codigo}</div>
            <div className="vinc-acoes">
              <button className="btn btn-outline" onClick={handleCopiar}>
                {copiado ? "✅ Copiado!" : "📋 Copiar"}
              </button>
              <a className="btn btn-outline"
                href={`https://wa.me/?text=${encodeURIComponent(mensagemConvite())}`}
                target="_blank" rel="noreferrer">
                💬 WhatsApp
              </a>
              <button className="btn btn-primary" onClick={handleGerar} disabled={gerando}>
                {gerando ? "Gerando..." : "🔄 Gerar novo"}
              </button>
            </div>
          </>
        ) : (
          <button className="btn btn-primary" onClick={handleGerar} disabled={gerando}>
            {gerando ? "Gerando..." : "Gerar código"}
          </button>
        )}

        {erro && <p className="error-msg" style={{ marginTop: 12 }}>{erro}</p>}
      </section>

      {codigo && (
        <section className="card">
          <h2 className="secao-titulo">Enviar convite por e-mail</h2>
          <form className="vinc-form" onSubmit={handleEnviarConvite}>
            <input className="input" type="email" placeholder="email@paciente.com"
              value={email} onChange={e => setEmail(e.target.value)} required />
            <button className="btn btn-primary" disabled={enviando || !email.trim()}>
              {enviando ? "Enviando..." : "Enviar"}
            </button>
          </form>
          {conviteMsg.texto && (
            <p className={conviteMsg.tipo === "erro" ? "error-msg" : "vinc-ok"} style={{ marginTop: 10 }}>
              {conviteMsg.texto}
            </p>
          )}
        </section>
      )}

      <section className="card">
        <h2 className="secao-titulo">Pacientes vinculados ({pacientes.length})</h2>
        {loading ? (
          <p className="empty-text">Carregando...</p>
        ) : pacientes.length === 0 ? (
          <p className="empty-text">Nenhum paciente vinculado ainda.</p>
        ) : (
          <ul className="pacientes-lista">
            {pacientes.map(([id, nome]) => (
              <li key={id} className="paciente-item" style={{ cursor: "default" }}>
                <div className="paciente-avatar">{nome?.[0]?.toUpperCase()}</div>
                <span className="paciente-nome">{nome}</span>
              </li>
            ))}
          </ul>
        )}
      </section>
    </div>
  )
}