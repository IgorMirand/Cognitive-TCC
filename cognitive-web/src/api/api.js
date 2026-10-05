const BASE_URL = "/api"

const getToken = () => localStorage.getItem("token")

// ─── Headers automáticos (JWT se existir) ───────────────────────────────────
function headers(extra = {}) {
  const h = {
    "Content-Type": "application/json",
    ...extra,
  }
  const token = getToken()
  if (token) h["Authorization"] = `Bearer ${token}`
  return h
}

// ─── Tratamento de resposta ──────────────────────────────────────────────────
// Se a resposta de erro não for JSON (ex.: HTML de um 404/405), evita estourar
// "Unexpected token <" e devolve um objeto { detail } padronizado.
async function handle(res) {
  if (res.ok) return res.json()

  let erro
  try {
    erro = await res.json()
  } catch {
    erro = { detail: `Erro ${res.status}` }
  }
  throw erro
}

// ─── Helpers HTTP ────────────────────────────────────────────────────────────
async function get(path) {
  const res = await fetch(`${BASE_URL}${path}`, { headers: headers() })
  return handle(res)
}

async function post(path, body) {
  const res = await fetch(`${BASE_URL}${path}`, {
    method: "POST",
    headers: headers(),
    body: JSON.stringify(body),
  })
  return handle(res)
}

async function put(path, body) {
  const res = await fetch(`${BASE_URL}${path}`, {
    method: "PUT",
    headers: headers(),
    body: JSON.stringify(body),
  })
  return handle(res)
}

async function del(path) {
  const res = await fetch(`${BASE_URL}${path}`, {
    method: "DELETE",
    headers: headers(),
  })
  return handle(res)
}

// ─── Auth ────────────────────────────────────────────────────────────────────
export const authAPI = {
  login: (email, password) => post("/login", { email, password }),
  register: (data) => post("/register", data),
}

// ─── Usuário ─────────────────────────────────────────────────────────────────
export const userAPI = {
  get:            (id)       => get(`/users/${id}`),
  update:         (id, data) => put(`/users/${id}`, data),
  changePassword: (id, data) => put(`/users/${id}/password`, data),
}

// ─── Agenda ──────────────────────────────────────────────────────────────────
export const agendaAPI = {
  getPsicologo:   (psicologoId) => get(`/agenda/psicologo/${psicologoId}`),
  addSlot:        (data)        => post("/agenda/disponibilidade", data),
  deleteSlot:     (id)          => del(`/agenda/${id}`),
  reservar:       (id, data)    => put(`/agenda/${id}/reservar`, data),
}

// ─── Diário ──────────────────────────────────────────────────────────────────
export const diarioAPI = {
  salvar:    (data)       => post("/diario", data),
  historico: (pacienteId) => get(`/diario/historico/${pacienteId}`),
}

// ─── Psicólogo ───────────────────────────────────────────────────────────────
export const psicologoAPI = {
  stats:                  (id)           => get(`/psicologo/${id}/stats`),
  pacientes:              (id)           => get(`/psicologo/${id}/pacientes`),
  getPsicologoDoPaciente: (id)           => get(`/paciente/${id}/psicologo`),
  gerarCodigo:            (id)           => post(`/codigos/gerar/${id}`),
  vincular:               (data)         => post("/vincular", data),
  validarCodigoMaster:    (codigo)       => get(`/codigos/master/validar/${codigo}`),
  usarCodigoMaster:       (data)         => post("/codigos/master/usar", data),
  listarAtividades:       ()             => get("/atividades"),
  criarAtividade:         (data)         => post("/atividades", data),
  deletarAtividade:       (id)           => del(`/atividades/${id}`),
  getAnotacoes:           (psiId, pacId) => get(`/consultas/${psiId}/${pacId}`),
  salvarConsulta:         (data)         => post("/consultas", data),
  enviarConvite:          (data)         => post("/email/enviar_convite", data),
}

// ─── Notificações ────────────────────────────────────────────────────────────
export const notificacoesAPI = {
  get:         (userId) => get(`/notificacoes/${userId}`),
  deletar:     (id)     => del(`/notificacoes/${id}`),
  marcarLidas: (userId) => put(`/notificacoes/marcar_lida/${userId}`),
}

// ─── Analytics ───────────────────────────────────────────────────────────────
export const analyticsAPI = {
  relatorio:         (pacienteId) => get(`/relatorios/analise/${pacienteId}`),
  graficoAtividades: (pacienteId) => get(`/relatorios/grafico_atividades/${pacienteId}`),
}