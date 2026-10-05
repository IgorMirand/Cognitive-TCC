import { useEffect, useState } from "react"
import { useNavigate } from "react-router-dom"
import { useAuth } from "../../context/AuthContext"
import { psicologoAPI, analyticsAPI } from "../../api/api"
import "./PsicologoPacientes.css"

// ── Tela de detalhe do paciente ──────────────────────────────────────────────
function DetalhePaciente({ paciente, onVoltar }) {
  const [relatorio,   setRelatorio]   = useState(null)
  const [anotacoes,   setAnotacoes]   = useState([])
  const [novaAnotacao, setNovaAnotacao] = useState("")
  const [salvando,    setSalvando]    = useState(false)
  const [loading,     setLoading]     = useState(true)
  const [aba,         setAba]         = useState("relatorio") // "relatorio" | "anotacoes"
  const { user } = useAuth()

  useEffect(() => {
    Promise.all([
      analyticsAPI.relatorio(paciente[0]).catch(() => null),
      psicologoAPI.getAnotacoes(user.id, paciente[0]).catch(() => ({ anotacoes: [] })),
    ]).then(([rel, anot]) => {
      setRelatorio(rel)
      setAnotacoes(anot.anotacoes || [])
    }).finally(() => setLoading(false))
  }, [paciente[0]])

  async function handleSalvarAnotacao() {
    if (!novaAnotacao.trim()) return
    setSalvando(true)
    try {
      const agora = new Date()
      const iso = new Date(agora - agora.getTimezoneOffset() * 60000).toISOString().slice(0, 19)
      await psicologoAPI.salvarConsulta({
        psicologo_id:  user.id,
        paciente_id:   paciente[0],
        anotacao:      novaAnotacao,
        data_hora_iso: iso,
      })
      setAnotacoes(prev => [[Date.now(), iso, novaAnotacao], ...prev])
      setNovaAnotacao("")
    } catch {}
    finally { setSalvando(false) }
  }

  return (
    <div className="detalhe-page">
      <button className="voltar-btn" onClick={onVoltar}>← Voltar</button>

      <header className="detalhe-header">
        <div className="detalhe-avatar">{paciente[1]?.[0]?.toUpperCase()}</div>
        <div>
          <h1 className="detalhe-nome">{paciente[1]}</h1>
          <p className="detalhe-sub">Paciente</p>
        </div>
      </header>

      {/* Abas */}
      <div className="abas">
        <button className={`aba-btn ${aba === "relatorio" ? "aba-btn--active" : ""}`}
          onClick={() => setAba("relatorio")}>📊 Relatório</button>
        <button className={`aba-btn ${aba === "anotacoes" ? "aba-btn--active" : ""}`}
          onClick={() => setAba("anotacoes")}>📝 Anotações</button>
      </div>

      {loading ? (
        <p className="empty-text" style={{ marginTop: 24 }}>Carregando...</p>
      ) : aba === "relatorio" ? (
        <div className="relatorio-section">
          {!relatorio ? (
            <div className="card" style={{ textAlign: "center", padding: 40 }}>
              <p style={{ fontSize: "2rem" }}>📊</p>
              <p className="empty-text" style={{ marginTop: 8 }}>
                Paciente ainda não tem registros no diário.
              </p>
            </div>
          ) : (
            <>
              <div className="card resumo-card">
                <p className="resumo-texto">💡 {relatorio.resumo_texto}</p>
              </div>
              {relatorio.grafico_evolucao_base64 && (
                <div className="card grafico-card">
                  <h3 className="grafico-titulo">Evolução do bem-estar</h3>
                  <img
                    src={`data:image/png;base64,${relatorio.grafico_evolucao_base64}`}
                    alt="Evolução do bem-estar"
                    className="grafico-img"
                  />
                </div>
              )}
              {relatorio.grafico_distribuicao_base64 && (
                <div className="card grafico-card">
                  <h3 className="grafico-titulo">Distribuição de emoções</h3>
                  <img
                    src={`data:image/png;base64,${relatorio.grafico_distribuicao_base64}`}
                    alt="Distribuição de emoções"
                    className="grafico-img"
                  />
                </div>
              )}
            </>
          )}
        </div>
      ) : (
        <div className="anotacoes-section">
          <div className="card nova-anotacao">
            <h3 className="secao-titulo">Nova anotação</h3>
            <textarea
              className="input"
              rows={4}
              placeholder="Registre suas observações sobre a consulta..."
              value={novaAnotacao}
              onChange={e => setNovaAnotacao(e.target.value)}
              style={{ resize: "vertical" }}
            />
            <button className="btn btn-primary" style={{ marginTop: 12 }}
              onClick={handleSalvarAnotacao} disabled={salvando || !novaAnotacao.trim()}>
              {salvando ? "Salvando..." : "💾 Salvar anotação"}
            </button>
          </div>

          {anotacoes.length === 0 ? (
            <div className="card" style={{ textAlign: "center", padding: 32 }}>
              <p className="empty-text">Nenhuma anotação ainda.</p>
            </div>
          ) : (
            <div className="anotacoes-lista">
              {anotacoes.map((a, i) => (
                <div key={a[0] ?? i} className="card anotacao-card">
                  <p className="anotacao-data">
                    {new Date(a[1]).toLocaleDateString("pt-BR", {
                      day: "numeric", month: "long", year: "numeric",
                      hour: "2-digit", minute: "2-digit",
                    })}
                  </p>
                  <p className="anotacao-texto">{a[2]}</p>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  )
}

// ── Tela principal — lista de pacientes ──────────────────────────────────────
export default function PsicologoPacientes() {
  const { user }    = useAuth()
  const navigate    = useNavigate()

  const [pacientes,  setPacientes]  = useState([])
  const [busca,      setBusca]      = useState("")
  const [loading,    setLoading]    = useState(true)
  const [selecionado, setSelecionado] = useState(null)

  useEffect(() => {
    if (!user) return
    psicologoAPI.pacientes(user.id)
      .then(d => setPacientes(d.pacientes || []))
      .finally(() => setLoading(false))
  }, [user])

  if (selecionado) {
    return <DetalhePaciente paciente={selecionado} onVoltar={() => setSelecionado(null)} />
  }

  const filtrados = pacientes.filter(([, nome]) =>
    nome.toLowerCase().includes(busca.toLowerCase())
  )

  if (loading) return <div className="loading-screen">Carregando pacientes...</div>

  return (
    <div className="pacientes-page">
      <header className="pacientes-header">
        <div>
          <h1 className="pacientes-titulo">👥 Pacientes</h1>
          <p className="pacientes-sub">{pacientes.length} paciente{pacientes.length !== 1 ? "s" : ""} vinculado{pacientes.length !== 1 ? "s" : ""}</p>
        </div>
        <button className="btn btn-outline" onClick={() => navigate("/psicologo/vinculos")}>
          + Vincular paciente
        </button>
      </header>

      {pacientes.length === 0 ? (
        <div className="card pacientes-empty">
          <p style={{ fontSize: "3rem" }}>👥</p>
          <h3>Nenhum paciente vinculado</h3>
          <p>Gere um código de vínculo e compartilhe com seus pacientes.</p>
          <button className="btn btn-primary" style={{ marginTop: 16 }}
            onClick={() => navigate("/psicologo/vinculos")}>
            Gerar código
          </button>
        </div>
      ) : (
        <>
          {/* Busca */}
          <div className="busca-wrapper">
            <span className="busca-icon">🔍</span>
            <input className="input busca-input" placeholder="Buscar paciente..."
              value={busca} onChange={e => setBusca(e.target.value)} />
          </div>

          {filtrados.length === 0 ? (
            <p className="empty-text" style={{ marginTop: 20 }}>Nenhum paciente encontrado.</p>
          ) : (
            <div className="pacientes-grid">
              {filtrados.map(([id, nome]) => (
                <div key={id} className="card paciente-card"
                  onClick={() => setSelecionado([id, nome])}>
                  <div className="paciente-card-avatar">
                    {nome?.[0]?.toUpperCase()}
                  </div>
                  <div className="paciente-card-info">
                    <p className="paciente-card-nome">{nome}</p>
                    <p className="paciente-card-sub">Clique para ver relatório e anotações</p>
                  </div>
                  <span className="paciente-card-arrow">→</span>
                </div>
              ))}
            </div>
          )}
        </>
      )}
    </div>
  )
}