import { Navigate } from "react-router-dom"
import { useAuth } from "../context/AuthContext"

/**
 * Uso:
 * <ProtectedRoute>          → qualquer usuário logado
 * <ProtectedRoute role="Psicólogo">  → só psicólogos
 * <ProtectedRoute role="Paciente">   → só pacientes
 */
export default function ProtectedRoute({ children, role }) {
  const { user, loading } = useAuth()

  if (loading) return <div className="loading-screen">Carregando...</div>
  if (!user) return <Navigate to="/login" replace />
  if (role && user.user_type !== role) return <Navigate to="/" replace />

  return children
}
