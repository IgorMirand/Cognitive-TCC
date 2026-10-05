import { useEffect, useState } from "react"
import { useNavigate } from "react-router-dom"
import { useAuth } from "../../context/AuthContext"
import { agendaAPI, notificacoesAPI, diarioAPI } from "../../api/api"
import "./PacienteDashboard.css"

const EMOCOES = {
  1: { label: "Feliz",        emoji: "😊" },
  2: { label: "Triste",       emoji: "😢" },
  3: { label: "Medo",         emoji: "😨" },
  4: { label: "Surpreso",     emoji: "😮" },
  5: { label: "Raiva",        emoji: "😠" },
  6: { label: "Envergonhado", emoji: "😳" },
  7: { label: "Constrangido", emoji: "😅" },
  8: { label: "Receoso",      emoji: "😟" },
  9: { label: "Apático",      emoji: "😑" },
  10:{ label: "Deprimido",    emoji: "😞" },
  11:{ label: "Irritado",     emoji: "😤" },
}

export default function PacienteDashboard() {
  const { user } = useAuth()
  const navigate  = useNavigate()

  const [agenda,        setAgenda]        = useState([])
  const [notificacoes,  setNotificacoes]  = useState([])
  const [historico,     setHistorico]     = useState([])
  const [loading,       setLoading]       = useState(true)

  useEffect(() => {
    if (!user) return
    Promise.all([
      agendaAPI.getPsicologo(user.id).catch(() => ({ agenda: [] })),
      notificacoesAPI.get(user.id).catch(() => ({ notificacoes: [] })),
      diarioAPI.historico(user.id).catch(() => ({ historico: [] })),
    ]).then(([ag, nt, hi]) => {
      setAgenda(ag.agenda || [])
      setNotificacoes((nt.notificacoes || []).filter(n => !n.lida).slice(0, 3))
      setHistorico((hi.historico || []).slice(0, 3))
    }).finally(() => setLoading(false))
  }, [user])

  const hora = new Date().getHours()
  const saudacao = hora < 12 ? "Bom dia" : hora < 18 ? "Boa tarde" : "Boa noite"

  const proximaConsulta = agenda.find(a => a[2] === user?.id)

  if (loading) return <div className="loading-screen">Carregando...</div>

  return (
    <div className="dashboard">

      {/* Cabeçalho */}
      <header className="dashboard-header">
        <div>
          <h1 className="dashboard-greeting">{saudacao}, {user?.username?.split(" ")[0]}! 👋</h1>
          <p className="dashboard-date">
            {new Date().toLocaleDateString("pt-BR", { weekday: "long", day: "numeric", month: "long" })}
          </p>
        </div>
        <button className="btn btn-primary" onClick={() => navigate("/paciente/diario")}>
          + Registrar hoje
        </button>
      </header>

      {/* Cards de resumo */}
      <div className="dashboard-stats">
        <div className="stat-card">
          <span className="stat-icon">📓</span>
          <div>
            <p className="stat-value">{historico.length}</p>
            <p className="stat-label">Registros recentes</p>
          </div>
        </div>
        <div className="stat-card">
          <span className="stat-icon">🔔</span>
          <div>
            <p className="stat-value">{notificacoes.length}</p>
            <p className="stat-label">Notificações novas</p>
          </div>
        </div>
        <div className="stat-card">
          <span className="stat-icon">📅</span>
          <div>
            <p className="stat-value">{proximaConsulta ? "Agendada" : "Livre"}</p>
            <p className="stat-label">Próxima consulta</p>
          </div>
        </div>
      </div>

      <div className="dashboard-grid">

        {/* Próxima consulta */}
        <section className="card dashboard-consulta">
          <h2 className="section-title">📅 Próxima consulta</h2>
          {proximaConsulta ? (
            <div className="consulta-info">
              <p className="consulta-data">
                {new Date(proximaConsulta[1]).toLocaleDateString("pt-BR", {
                  weekday: "long", day: "numeric", month: "long",
                })}
              </p>
              <p className="consulta-hora">
                {new Date(proximaConsulta[1]).toLocaleTimeString("pt-BR", {
                  hour: "2-digit", minute: "2-digit",
                })}
              </p>
            </div>
          ) : (
            <div className="empty-state">
              <p>Nenhuma consulta agendada.</p>
              <button className="btn btn-outline" onClick={() => navigate("/paciente/agenda")}>
                Ver agenda
              </button>
            </div>
          )}
        </section>

        {/* Notificações recentes */}
        <section className="card dashboard-notificacoes">
          <div className="section-header">
            <h2 className="section-title">🔔 Notificações</h2>
            {notificacoes.length > 0 && (
              <button className="link-btn" onClick={() => navigate("/paciente/notificacoes")}>
                Ver todas
              </button>
            )}
          </div>
          {notificacoes.length === 0 ? (
            <p className="empty-text">Nenhuma notificação nova.</p>
          ) : (
            <ul className="notif-list">
              {notificacoes.map(n => (
                <li key={n.id} className="notif-item">
                  <p className="notif-titulo">{n.titulo}</p>
                  <p className="notif-msg">{n.mensagem}</p>
                </li>
              ))}
            </ul>
          )}
        </section>

        {/* Últimos registros do diário */}
        <section className="card dashboard-diario">
          <div className="section-header">
            <h2 className="section-title">📓 Diário recente</h2>
            <button className="link-btn" onClick={() => navigate("/paciente/diario")}>
              Ver tudo
            </button>
          </div>
          {historico.length === 0 ? (
            <div className="empty-state">
              <p>Nenhum registro ainda.</p>
              <button className="btn btn-outline" onClick={() => navigate("/paciente/diario")}>
                Fazer primeiro registro
              </button>
            </div>
          ) : (
            <ul className="diario-list">
              {historico.map(h => {
                const emocao = EMOCOES[h[2]] || { emoji: "❓", label: "Outro" }
                return (
                  <li key={h[0]} className="diario-item">
                    <span className="diario-emoji">{emocao.emoji}</span>
                    <div>
                      <p className="diario-emocao">{emocao.label}</p>
                      <p className="diario-data">
                        {new Date(h[1]).toLocaleDateString("pt-BR", {
                          day: "numeric", month: "short",
                        })}
                      </p>
                    </div>
                    {h[3] && <p className="diario-nota">{h[3].slice(0, 60)}{h[3].length > 60 ? "..." : ""}</p>}
                  </li>
                )
              })}
            </ul>
          )}
        </section>

      </div>
    </div>
  )
}