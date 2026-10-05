import { useEffect, useMemo, useState } from "react"
import { useAuth } from "../../context/AuthContext"
import { agendaAPI } from "../../api/api"
import "./PsicologoAgenda.css"

// Aceita tupla [id, data_hora, reservado_por] ou objeto.
// Ajuste aqui conforme o retorno real de GET /agenda/psicologo/{id}.
function normalizar(s) {
  if (Array.isArray(s)) {
    const quem = s[2]
    return {
      id: s[0],
      dataHora: s[1],
      ocupado: !!quem,
      paciente: typeof quem === "string" ? quem : "",
    }
  }
  const paciente = s.paciente_nome ?? s.paciente ?? ""
  const status = String(s.status ?? "").toLowerCase()
  return {
    id: s.id,
    dataHora: s.data_hora ?? s.data_hora_iso ?? s.horario,
    ocupado:
      s.disponivel === false || !!s.paciente_id || !!paciente ||
      ["reservado", "ocupado", "agendado"].includes(status),
    paciente: typeof paciente === "string" ? paciente : "",
  }
}

function paraData(str) {
  const d = new Date(str)
  return isNaN(d) ? null : d
}

function chaveDia(d) {
  return d.toLocaleDateString("pt-BR", { weekday: "long", day: "numeric", month: "long" })
}

function horaFmt(d) {
  return d.toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" })
}

export default function PsicologoAgenda() {
  const { user } = useAuth()

  const [slots,    setSlots]    = useState([])
  const [loading,  setLoading]  = useState(true)
  const [erro,     setErro]     = useState("")
  const [passados, setPassados] = useState(false)

  const [dataHora, setDataHora] = useState("")
  const [salvando, setSalvando] = useState(false)
  const [removendo, setRemovendo] = useState(null)

  async function carregar() {
    if (!user) return
    try {
      const r = await agendaAPI.getPsicologo(user.id)
      const lista = Array.isArray(r) ? r : (r.agenda ?? r.horarios ?? r.slots ?? [])
      setSlots(lista.map(normalizar))
    } catch {
      setErro("Não foi possível carregar a agenda.")
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { carregar() }, [user?.id])

  async function handleAdicionar(e) {
    e.preventDefault()
    if (!dataHora) return
    setErro("")

    if (new Date(dataHora) < new Date()) {
      return setErro("Escolha um horário no futuro.")
    }

    setSalvando(true)
    try {
      // TODO: confirmar o schema de POST /agenda/disponibilidade
      // datetime-local já vem como "YYYY-MM-DDTHH:mm" (horário local)
      await agendaAPI.addSlot({
        psicologo_id:  user.id,
        data_hora_iso: `${dataHora}:00`,
      })
      setDataHora("")
      await carregar()
    } catch (err) {
      setErro(err?.detail || "Erro ao abrir horário.")
    } finally {
      setSalvando(false)
    }
  }

  async function handleRemover(s, d) {
    const msg = s.ocupado
      ? `Este horário (${chaveDia(d)}, ${horaFmt(d)}) já está reservado. Remover mesmo assim?`
      : `Remover o horário de ${horaFmt(d)}?`
    if (!window.confirm(msg)) return
    setErro("")
    setRemovendo(s.id)
    try {
      await agendaAPI.deleteSlot(s.id)
      setSlots(prev => prev.filter(x => x.id !== s.id))
    } catch (err) {
      setErro(err?.detail || "Erro ao remover horário.")
    } finally {
      setRemovendo(null)
    }
  }

  const dias = useMemo(() => {
    const agora = new Date()
    const validos = slots
      .map(s => ({ ...s, d: paraData(s.dataHora) }))
      .filter(s => s.d && (passados || s.d >= agora))
      .sort((a, b) => a.d - b.d)

    const mapa = new Map()
    for (const s of validos) {
      const k = chaveDia(s.d)
      if (!mapa.has(k)) mapa.set(k, [])
      mapa.get(k).push(s)
    }
    return [...mapa.entries()]
  }, [slots, passados])

  const livres   = slots.filter(s => !s.ocupado).length
  const ocupados = slots.length - livres

  if (loading) return <div className="loading-screen">Carregando agenda...</div>

  return (
    <div className="agenda-page">
      <header className="agenda-header">
        <div>
          <h1 className="agenda-titulo">📅 Agenda</h1>
          <p className="agenda-sub">{livres} livre{livres !== 1 ? "s" : ""} · {ocupados} reservado{ocupados !== 1 ? "s" : ""}</p>
        </div>
      </header>

      <form className="card agenda-form" onSubmit={handleAdicionar}>
        <h2 className="secao-titulo">Abrir novo horário</h2>
        <div className="agenda-form-row">
          <input className="input" type="datetime-local" value={dataHora}
            onChange={e => setDataHora(e.target.value)} required />
          <button className="btn btn-primary" disabled={salvando || !dataHora}>
            {salvando ? "Abrindo..." : "+ Abrir horário"}
          </button>
        </div>
      </form>

      {erro && <p className="error-msg">{erro}</p>}

      <label className="agenda-toggle">
        <input type="checkbox" checked={passados} onChange={e => setPassados(e.target.checked)} />
        Mostrar horários passados
      </label>

      {dias.length === 0 ? (
        <div className="card agenda-empty">
          <p style={{ fontSize: "3rem" }}>📅</p>
          <h3>Nenhum horário {passados ? "" : "futuro "}cadastrado</h3>
          <p>Abra horários para que seus pacientes possam agendar.</p>
        </div>
      ) : (
        dias.map(([dia, lista]) => (
          <section key={dia} className="card">
            <h2 className="secao-titulo agenda-dia">{dia}</h2>
            <ul className="agenda-lista">
              {lista.map(s => (
                <li key={s.id} className={`agenda-slot ${s.ocupado ? "agenda-slot--ocupado" : ""}`}>
                  <span className="agenda-hora">{horaFmt(s.d)}</span>
                  <span className="agenda-status">
                    {s.ocupado ? `Reservado${s.paciente ? ` — ${s.paciente}` : ""}` : "Livre"}
                  </span>
                  <button className="agenda-del" onClick={() => handleRemover(s, s.d)}
                    disabled={removendo === s.id} aria-label="Remover horário">
                    {removendo === s.id ? "..." : "🗑️"}
                  </button>
                </li>
              ))}
            </ul>
          </section>
        ))
      )}
    </div>
  )
}