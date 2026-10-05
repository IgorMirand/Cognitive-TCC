import { useEffect, useState } from "react"
import { useAuth } from "../../context/AuthContext"
import { diarioAPI, psicologoAPI } from "../../api/api"
import "./PacienteDiario.css"

const EMOCOES = [
  { id: 1,  emoji: "😊", label: "Feliz"        },
  { id: 2,  emoji: "😢", label: "Triste"       },
  { id: 3,  emoji: "😨", label: "Medo"         },
  { id: 4,  emoji: "😮", label: "Surpreso"     },
  { id: 5,  emoji: "😠", label: "Raiva"        },
  { id: 6,  emoji: "😳", label: "Envergonhado" },
  { id: 7,  emoji: "😅", label: "Constrangido" },
  { id: 8,  emoji: "😟", label: "Receoso"      },
  { id: 9,  emoji: "😑", label: "Apático"      },
  { id: 10, emoji: "😞", label: "Deprimido"    },
  { id: 11, emoji: "😤", label: "Irritado"     },
]
const EMOCOES_MAP = Object.fromEntries(EMOCOES.map(e => [e.id, e]))

function toISOLocal() {
  const now = new Date()
  return new Date(now - now.getTimezoneOffset() * 60000).toISOString().slice(0, 19)
}

function formatarData(str) {
  if (!str) return ""
  const d = new Date(str)
  return isNaN(d) ? str : d.toLocaleDateString("pt-BR", {
    day: "numeric", month: "long", year: "numeric",
    hour: "2-digit", minute: "2-digit",
  })
}

export default function PacienteDiario() {
  const { user } = useAuth()

  const [emocaoSelecionada, setEmocaoSelecionada] = useState(null)
  const [bemEstar,          setBemEstar]          = useState(5)
  const [anotacao,          setAnotacao]          = useState("")
  const [atividadesSel,     setAtividadesSel]     = useState([])
  const [atividades,        setAtividades]        = useState([])
  const [salvando,          setSalvando]          = useState(false)
  const [sucesso,           setSucesso]           = useState(false)
  const [erroForm,          setErroForm]          = useState("")
  const [historico,         setHistorico]         = useState([])
  const [loadingHist,       setLoadingHist]       = useState(true)

  useEffect(() => {
    if (!user) return
    psicologoAPI.listarAtividades().then(d => setAtividades(d.atividades || [])).catch(() => {})
    carregarHistorico()
  }, [user])

  async function carregarHistorico() {
    setLoadingHist(true)
    try {
      const d = await diarioAPI.historico(user.id)
      setHistorico(d.historico || [])
    } catch { setHistorico([]) }
    finally { setLoadingHist(false) }
  }

  function toggleAtividade(id) {
    setAtividadesSel(prev => prev.includes(id) ? prev.filter(a => a !== id) : [...prev, id])
  }

  async function handleSalvar() {
    if (!emocaoSelecionada) { setErroForm("Selecione como você está se sentindo."); return }
    setErroForm(""); setSalvando(true)
    try {
      await diarioAPI.salvar({
        paciente_id:    user.id,
        data_hora_iso:  toISOLocal(),
        sentimento_id:  emocaoSelecionada,
        anotacao:       `Bem-estar: ${bemEstar}/10\n${anotacao}`.trim(),
        atividades_ids: atividadesSel,
      })
      setEmocaoSelecionada(null); setBemEstar(5); setAnotacao(""); setAtividadesSel([])
      setSucesso(true); setTimeout(() => setSucesso(false), 3000)
      carregarHistorico()
    } catch (e) { setErroForm(e?.detail || "Erro ao salvar.") }
    finally { setSalvando(false) }
  }

  return (
    <div className="diario-page">

      <section className="card diario-form">
        <h1 className="diario-titulo">📓 Como você está hoje?</h1>
        <p className="diario-subtitulo">
          {new Date().toLocaleDateString("pt-BR", { weekday: "long", day: "numeric", month: "long" })}
        </p>

        <div className="emocoes-grid">
          {EMOCOES.map(e => (
            <button key={e.id}
              className={`emocao-btn ${emocaoSelecionada === e.id ? "emocao-btn--active" : ""}`}
              onClick={() => setEmocaoSelecionada(e.id)} title={e.label}>
              <span className="emocao-emoji">{e.emoji}</span>
              <span className="emocao-label">{e.label}</span>
            </button>
          ))}
        </div>

        <div className="bem-estar-section">
          <label className="bem-estar-label">
            Nível de bem-estar: <strong style={{ color: "var(--green-dark)", marginLeft: 8 }}>{bemEstar}/10</strong>
          </label>
          <input type="range" min="0" max="10" value={bemEstar}
            onChange={e => setBemEstar(Number(e.target.value))} className="bem-estar-slider" />
          <div className="bem-estar-ticks"><span>😞 0</span><span>😐 5</span><span>😊 10</span></div>
        </div>

        {atividades.length > 0 && (
          <div className="atividades-section">
            <p className="atividades-titulo">Atividades realizadas hoje:</p>
            <div className="atividades-grid">
              {atividades.map(([id, texto]) => (
                <button key={id}
                  className={`atividade-chip ${atividadesSel.includes(id) ? "atividade-chip--active" : ""}`}
                  onClick={() => toggleAtividade(id)}>
                  {atividadesSel.includes(id) ? "✓ " : ""}{texto}
                </button>
              ))}
            </div>
          </div>
        )}

        <div className="input-group" style={{ marginTop: 20 }}>
          <label>Anotação livre <span style={{ color: "var(--text-light)" }}>(opcional)</span></label>
          <textarea className="input diario-textarea"
            placeholder="Como foi seu dia? Algo que queira registrar..."
            value={anotacao} onChange={e => setAnotacao(e.target.value)} rows={4} />
        </div>

        {erroForm && <p className="error-msg">{erroForm}</p>}
        {sucesso && <div className="sucesso-banner">✅ Registro salvo com sucesso!</div>}

        <button className="btn btn-primary" style={{ width: "100%", marginTop: 8 }}
          onClick={handleSalvar} disabled={salvando}>
          {salvando ? "Salvando..." : "💾 Salvar registro"}
        </button>
      </section>

      <section className="diario-historico">
        <h2 className="historico-titulo">📅 Histórico</h2>
        {loadingHist ? (
          <p className="empty-text">Carregando...</p>
        ) : historico.length === 0 ? (
          <div className="card" style={{ textAlign: "center", padding: "32px" }}>
            <p style={{ fontSize: "2rem" }}>📓</p>
            <p className="empty-text" style={{ marginTop: 8 }}>Nenhum registro ainda. Faça seu primeiro registro acima!</p>
          </div>
        ) : (
          <div className="historico-list">
            {historico.map(h => {
              const emocao = EMOCOES_MAP[h[2]] || { emoji: "❓", label: "Outro" }
              const anotacaoTexto = (h[3] || "").replace(/^Bem-estar:\s*\d+\/10\n?/i, "").trim()
              const match = (h[3] || "").match(/Bem-estar:\s*(\d+)/i)
              const nota = match ? parseInt(match[1]) : null
              return (
                <div key={h[0]} className="card historico-card">
                  <div className="historico-header">
                    <div className="historico-emocao">
                      <span className="historico-emoji">{emocao.emoji}</span>
                      <div>
                        <p className="historico-emocao-label">{emocao.label}</p>
                        <p className="historico-data">{formatarData(h[1])}</p>
                      </div>
                    </div>
                    {nota !== null && (
                      <div className="historico-nota">
                        <span className="nota-valor">{nota}</span>
                        <span className="nota-max">/10</span>
                      </div>
                    )}
                  </div>
                  {anotacaoTexto && <p className="historico-anotacao">"{anotacaoTexto}"</p>}
                  {h[4] && (
                    <div className="historico-atividades">
                      {h[4].split(", ").map((a, i) => <span key={i} className="atividade-tag">{a}</span>)}
                    </div>
                  )}
                </div>
              )
            })}
          </div>
        )}
      </section>
    </div>
  )
}