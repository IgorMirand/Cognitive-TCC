import { useEffect, useState } from "react"
import { useAuth } from "../../context/AuthContext"
import { notificacoesAPI } from "../../api/api"
import "./PacienteNotificacoes.css"

export default function PacienteNotificacoes() {
  const { user } = useAuth()

  const [notificacoes, setNotificacoes] = useState([])
  const [loading,      setLoading]      = useState(true)
  const [deletando,    setDeletando]    = useState(null)

  useEffect(() => {
    if (!user) return
    carregarNotificacoes()
  }, [user])

  async function carregarNotificacoes() {
    setLoading(true)
    try {
      const d = await notificacoesAPI.get(user.id)
      setNotificacoes(d.notificacoes || [])
    } catch {
      setNotificacoes([])
    } finally {
      setLoading(false)
    }
  }

  async function handleMarcarLidas() {
    try {
      await notificacoesAPI.marcarLidas(user.id)
      setNotificacoes(prev => prev.map(n => ({ ...n, lida: true })))
    } catch {}
  }

  async function handleDeletar(id) {
    setDeletando(id)
    try {
      await notificacoesAPI.deletar(id)
      setNotificacoes(prev => prev.filter(n => n.id !== id))
    } catch {}
    finally { setDeletando(null) }
  }

  async function handleDeletarTodas() {
    if (!confirm("Deseja apagar todas as notificações?")) return
    try {
      await Promise.all(notificacoes.map(n => notificacoesAPI.deletar(n.id)))
      setNotificacoes([])
    } catch {}
  }

  const naoLidas = notificacoes.filter(n => !n.lida).length

  if (loading) return <div className="loading-screen">Carregando notificações...</div>

  return (
    <div className="notif-page">

      <header className="notif-header">
        <div>
          <h1 className="notif-titulo">🔔 Notificações</h1>
          {naoLidas > 0 && (
            <p className="notif-subtitulo">{naoLidas} não lida{naoLidas > 1 ? "s" : ""}</p>
          )}
        </div>
        {notificacoes.length > 0 && (
          <div className="notif-acoes">
            {naoLidas > 0 && (
              <button className="btn btn-outline" onClick={handleMarcarLidas}>
                ✓ Marcar todas como lidas
              </button>
            )}
            <button className="btn btn-danger" onClick={handleDeletarTodas}>
              🗑 Apagar todas
            </button>
          </div>
        )}
      </header>

      {notificacoes.length === 0 ? (
        <div className="card notif-empty">
          <p className="notif-empty-icon">🔕</p>
          <h3>Nenhuma notificação</h3>
          <p>Você está em dia! Novas notificações aparecerão aqui.</p>
        </div>
      ) : (
        <div className="notif-lista">
          {notificacoes.map(n => (
            <div key={n.id} className={`card notif-card ${!n.lida ? "notif-card--nova" : ""}`}>
              <div className="notif-card-conteudo">
                {!n.lida && <span className="notif-dot" />}
                <div className="notif-textos">
                  <p className="notif-card-titulo">{n.titulo}</p>
                  <p className="notif-card-msg">{n.mensagem}</p>
                </div>
              </div>
              <button
                className="notif-deletar"
                onClick={() => handleDeletar(n.id)}
                disabled={deletando === n.id}
                title="Apagar"
              >
                {deletando === n.id ? "..." : "✕"}
              </button>
            </div>
          ))}
        </div>
      )}

    </div>
  )
}