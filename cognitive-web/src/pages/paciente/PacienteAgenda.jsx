import { useEffect, useState } from "react"
import { useAuth } from "../../context/AuthContext"
import { agendaAPI, psicologoAPI } from "../../api/api"
import "./PacienteAgenda.css"

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

function agruparPorDia(slots) {
  const grupos = {}
  for (const slot of slots) {
    const dia = new Date(slot[1]).toLocaleDateString("pt-BR")
    if (!grupos[dia]) grupos[dia] = []
    grupos[dia].push(slot)
  }
  return grupos
}

export default function PacienteAgenda() {
  const { user } = useAuth()

  const [psicologoId,   setPsicologoId]   = useState(null)
  const [slots,         setSlots]         = useState([])
  const [minhasConsultas, setMinhasConsultas] = useState([])
  const [loading,       setLoading]       = useState(true)
  const [reservando,    setReservando]    = useState(null)
  const [sucesso,       setSucesso]       = useState("")
  const [erro,          setErro]          = useState("")

  useEffect(() => {
    if (!user) return
    carregarDados()
  }, [user])

  async function carregarDados() {
    setLoading(true)
    try {
      // Busca psicólogo vinculado
      const vinculo = await psicologoAPI.getPsicologoDoPaciente(user.id)
      const pid = vinculo.psicologo_id

      if (!pid) { setLoading(false); return }
      setPsicologoId(pid)

      // Busca agenda do psicólogo
      const ag = await agendaAPI.getPsicologo(pid)
      const todos = ag.agenda || []

      // Separa livres e minhas consultas
      setSlots(todos.filter(s => s[2] === null))
      setMinhasConsultas(todos.filter(s => s[2] === user.id))
    } catch {
      setErro("Erro ao carregar agenda.")
    } finally {
      setLoading(false)
    }
  }

  async function handleReservar(slotId) {
    setReservando(slotId)
    setSucesso(""); setErro("")
    try {
      await agendaAPI.reservar(slotId, { paciente_id: user.id })
      setSucesso("Consulta agendada com sucesso! 🎉")
      setTimeout(() => setSucesso(""), 4000)
      carregarDados()
    } catch (e) {
      setErro(e?.detail || "Erro ao reservar horário.")
    } finally {
      setReservando(null)
    }
  }

  if (loading) return <div className="loading-screen">Carregando agenda...</div>

  const gruposLivres = agruparPorDia(slots)
  const gruposMinhas = agruparPorDia(minhasConsultas)

  return (
    <div className="agenda-page">
      <header className="agenda-header">
        <div>
          <h1 className="agenda-titulo">📅 Agenda</h1>
          <p className="agenda-subtitulo">Reserve horários com seu psicólogo</p>
        </div>
      </header>

      {sucesso && <div className="agenda-banner agenda-banner--sucesso">{sucesso}</div>}
      {erro    && <div className="agenda-banner agenda-banner--erro">{erro}</div>}

      {!psicologoId ? (
        <div className="card agenda-empty">
          <p style={{ fontSize: "2.5rem" }}>🔗</p>
          <h3>Nenhum psicólogo vinculado</h3>
          <p>Insira um código de vínculo no seu perfil para ver a agenda.</p>
        </div>
      ) : (
        <div className="agenda-grid">

          {/* Minhas consultas */}
          <section>
            <h2 className="secao-titulo">✅ Minhas consultas</h2>
            {minhasConsultas.length === 0 ? (
              <div className="card agenda-empty-small">
                <p>Nenhuma consulta agendada ainda.</p>
              </div>
            ) : (
              Object.entries(gruposMinhas).map(([dia, slotsdia]) => (
                <div key={dia} className="dia-grupo">
                  <p className="dia-label" style={{ textTransform: "capitalize" }}>
                    {formatarData(slotsdia[0][1])}
                  </p>
                  {slotsdia.map(slot => (
                    <div key={slot[0]} className="card slot-card slot-card--reservado">
                      <div className="slot-info">
                        <span className="slot-hora">{formatarHora(slot[1])}</span>
                        <span className="slot-badge slot-badge--confirmado">✓ Confirmado</span>
                      </div>
                    </div>
                  ))}
                </div>
              ))
            )}
          </section>

          {/* Horários disponíveis */}
          <section>
            <h2 className="secao-titulo">🕐 Horários disponíveis</h2>
            {slots.length === 0 ? (
              <div className="card agenda-empty-small">
                <p>Nenhum horário disponível no momento.</p>
                <p style={{ fontSize: "0.82rem", color: "var(--text-light)", marginTop: 4 }}>
                  Seu psicólogo ainda não abriu novos horários.
                </p>
              </div>
            ) : (
              Object.entries(gruposLivres).map(([dia, slotsdia]) => (
                <div key={dia} className="dia-grupo">
                  <p className="dia-label" style={{ textTransform: "capitalize" }}>
                    {formatarData(slotsdia[0][1])}
                  </p>
                  <div className="slots-lista">
                    {slotsdia.map(slot => (
                      <div key={slot[0]} className="card slot-card">
                        <div className="slot-info">
                          <span className="slot-hora">{formatarHora(slot[1])}</span>
                          <span className="slot-badge slot-badge--livre">Disponível</span>
                        </div>
                        <button
                          className="btn btn-primary slot-btn"
                          onClick={() => handleReservar(slot[0])}
                          disabled={reservando === slot[0]}
                        >
                          {reservando === slot[0] ? "Reservando..." : "Agendar"}
                        </button>
                      </div>
                    ))}
                  </div>
                </div>
              ))
            )}
          </section>

        </div>
      )}
    </div>
  )
}