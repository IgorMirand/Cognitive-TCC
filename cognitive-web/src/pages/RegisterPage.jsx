import { useState } from "react"
import { useNavigate, Link } from "react-router-dom"
import { authAPI } from "../api/api"
import "./AuthPages.css"

export default function RegisterPage() {
  const navigate = useNavigate()

  const [form, setForm] = useState({
    username: "", email: "", password: "", data_nascimento: "", codigo: "",
  })
  const [error, setError]     = useState("")
  const [success, setSuccess] = useState("")
  const [loading, setLoading] = useState(false)

  function handleChange(e) {
    setForm(f => ({ ...f, [e.target.name]: e.target.value }))
  }

  async function handleSubmit(e) {
    e.preventDefault()
    setError("")
    setSuccess("")
    setLoading(true)
    try {
      await authAPI.register({
        username:        form.username,
        email:           form.email,
        password:        form.password,
        data_nascimento: form.data_nascimento, // DD/MM/YYYY
        user_type:       form.codigo ? "Psicólogo" : "Paciente",
      })
      setSuccess("Conta criada! Redirecionando para o login...")
      setTimeout(() => navigate("/login"), 2000)
    } catch (err) {
      setError(err?.detail || "Erro ao criar conta.")
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="auth-bg">
      <div className="auth-card">
        <div className="auth-logo">🧠</div>
        <h1 className="auth-title">Criar conta</h1>
        <p className="auth-subtitle">Junte-se ao Cognitive</p>

        <form onSubmit={handleSubmit}>
          <div className="input-group">
            <label>Nome</label>
            <input className="input" name="username" placeholder="Seu nome completo"
              value={form.username} onChange={handleChange} required />
          </div>

          <div className="input-group">
            <label>Email</label>
            <input className="input" type="email" name="email" placeholder="seu@email.com"
              value={form.email} onChange={handleChange} required />
          </div>

          <div className="input-group">
            <label>Senha</label>
            <input className="input" type="password" name="password" placeholder="Mínimo 6 caracteres"
              value={form.password} onChange={handleChange} required />
          </div>

          <div className="input-group">
            <label>Data de nascimento</label>
            <input className="input" name="data_nascimento" placeholder="DD/MM/AAAA"
              value={form.data_nascimento} onChange={handleChange} required />
          </div>

          <div className="input-group">
            <label>Código de psicólogo <span style={{ color: "var(--text-light)" }}>(opcional)</span></label>
            <input className="input" name="codigo" placeholder="Deixe em branco se for paciente"
              value={form.codigo} onChange={handleChange} />
          </div>

          {error   && <p className="error-msg">{error}</p>}
          {success && <p style={{ color: "var(--green-dark)", fontSize: "0.875rem" }}>{success}</p>}

          <button className="btn btn-primary" style={{ width: "100%", marginTop: 8 }} disabled={loading}>
            {loading ? "Criando conta..." : "Criar conta"}
          </button>
        </form>

        <p className="auth-footer">
          Já tem conta? <Link to="/login">Entrar</Link>
        </p>
      </div>
    </div>
  )
}
