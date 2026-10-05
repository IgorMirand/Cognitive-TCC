import { useEffect, useState } from "react"
import { useNavigate } from "react-router-dom"
import { useAuth } from "../../context/AuthContext"
import { psicologoAPI } from "../../api/api"
import "./PsicologoDashboard.css"

function formatarData(str) {
  if (!str) return ""
  const d = new Date(str)
  return isNaN(d) ? str : d.toLocaleDateString("pt-BR", {
    weekday: "long", day: "numeric", month: "long",
  })
}

function formatarHora(str) {
  if (!str) return ""
  const d = new Date(str)
  return isNaN(d) ? str : d.toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" })
}

export default function PsicologoDashboard() {
  const { user } = useAuth()
  const navigate  = useNavigate()

  const [stats,     setStats]     = useState(null)
  const [pacientes, setPacientes] = useState([])
  const [loading,   setLoading]   = useState(true)

  useEffect(() => {
    if (!user) return
    Promise.all([
      psicologoAPI.stats(user.id),
      psicologoAPI.pacientes(user.id),
    ]).then(([s, p]) => {
      setStats(s)
      setPacientes((p.pacientes || []).slice(0, 5))
    }).finally(() => setLoading(false))
  }, [user])

  const hora = new Date().getHours()
  const saudacao = hora < 12 ? "Bom dia" : hora < 18 ? "Boa tarde" : "Boa noite"

  if (loading) return <div className="loading-screen">Carregando...</div>

  const proximaConsulta = stats?.proxima_consulta

  return (
    <div className="psi-dashboard">

      {/* ── Header ── */}
      <header className="psi-header">
        <div>
          <h1 className="psi-greeting">{saudacao}, Dr(a). {user?.username?.split(" ")[0]}! 👋</h1>
          <p className="psi-date">
            {new Date().toLocaleDateString("pt-BR", { weekday: "long", day: "numeric", month: "long" })}
          </p>
        </div>
        <button className="btn btn-primary" onClick={() => navigate("/psicologo/agenda")}>
          + Abrir horário
        </button>
      </header>

      {/* ── Stats ── */}
      <div className="psi-stats">
        <div className="psi-stat-card psi-stat-card--green">
          <div className="psi-stat-icon">👥</div>
          <div>
            <p className="psi-stat-valor">{stats?.pacientes_count ?? 0}</p>
            <p className="psi-stat-label">Pacientes ativos</p>
          </div>
        </div>

        <div className="psi-stat-card">
          <div className="psi-stat-icon">📅</div>
          <div>
            <p className="psi-stat-valor">{proximaConsulta ? formatarHora(proximaConsulta[0]) : "—"}</p>
            <p className="psi-stat-label">
              {proximaConsulta ? `Próxima — ${formatarData(proximaConsulta[0])}` : "Sem consultas agendadas"}
            </p>
          </div>
        </div>

        <div className="psi-stat-card" style={{ cursor: "pointer" }}
          onClick={() => navigate("/psicologo/agenda")}>
          <div className="psi-stat-icon">🕐</div>
          <div>
            <p className="psi-stat-valor">Agenda</p>
            <p className="psi-stat-label">Ver horários disponíveis</p>
          </div>
        </div>
      </div>

      <div className="psi-grid">

        {/* ── Próxima consulta destaque ── */}
        {proximaConsulta && (
          <section className="card psi-proxima">
            <h2 className="secao-titulo">📅 Próxima consulta</h2>
            <div className="proxima-info">
              <div className="proxima-hora">{formatarHora(proximaConsulta[0])}</div>
              <div>
                <p className="proxima-paciente">👤 {proximaConsulta[1]}</p>
                <p className="proxima-data" style={{ textTransform: "capitalize" }}>
                  {formatarData(proximaConsulta[0])}
                </p>
              </div>
            </div>
          </section>
        )}

        {/* ── Pacientes recentes ── */}
        <section className="card psi-pacientes">
          <div className="secao-header">
            <h2 className="secao-titulo">👥 Meus pacientes</h2>
            <button className="link-btn" onClick={() => navigate("/psicologo/pacientes")}>
              Ver todos
            </button>
          </div>
          {pacientes.length === 0 ? (
            <div className="psi-empty">
              <p>Nenhum paciente vinculado.</p>
              <button className="btn btn-outline" style={{ marginTop: 12 }}
                onClick={() => navigate("/psicologo/vinculos")}>
                Gerar código de vínculo
              </button>
            </div>
          ) : (
            <ul className="pacientes-lista">
              {pacientes.map(([id, nome]) => (
                <li key={id} className="paciente-item"
                  onClick={() => navigate(`/psicologo/pacientes/${id}`)}>
                  <div className="paciente-avatar">
                    {nome?.[0]?.toUpperCase()}
                  </div>
                  <span className="paciente-nome">{nome}</span>
                  <span className="paciente-arrow">→</span>
                </li>
              ))}
            </ul>
          )}
        </section>

        {/* ── Atalhos ── */}
        <section className="card psi-atalhos">
          <h2 className="secao-titulo">⚡ Atalhos</h2>
          <div className="psi-atalhos-grid">
            {[
              { icon: "📅", label: "Agenda",       rota: "/psicologo/agenda"    },
              { icon: "👥", label: "Pacientes",     rota: "/psicologo/pacientes" },
              { icon: "🔗", label: "Vínculos",      rota: "/psicologo/vinculos"  },
              { icon: "🏃", label: "Atividades",    rota: "/psicologo/atividades"},
              { icon: "📊", label: "Relatórios",    rota: "/psicologo/pacientes" },
              { icon: "👤", label: "Meu perfil",    rota: "/psicologo/perfil"    },
            ].map(({ icon, label, rota }) => (
              <button key={label} className="psi-atalho-btn" onClick={() => navigate(rota)}>
                <span>{icon}</span>
                <span>{label}</span>
              </button>
            ))}
          </div>
        </section>

      </div>
    </div>
  )
}