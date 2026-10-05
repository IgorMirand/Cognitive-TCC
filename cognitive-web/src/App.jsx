import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom"
import { AuthProvider, useAuth } from "./context/AuthContext"
import ProtectedRoute from "./components/ProtectedRoute"

// Páginas (vamos criar uma por vez)
import LoginPage        from "./pages/LoginPage"
import RegisterPage     from "./pages/RegisterPage"
import HomePaciente     from "./pages/HomePaciente"
import HomePsicologo    from "./pages/HomePsicologo"

// Redireciona para a home certa conforme o tipo de usuário
function HomeRedirect() {
  const { user } = useAuth()
  if (!user) return <Navigate to="/login" replace />
  if (user.user_type === "Psicólogo" || user.user_type === "Psicologo")
    return <Navigate to="/psicologo" replace />
  return <Navigate to="/paciente" replace />
}

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          {/* Públicas */}
          <Route path="/login"    element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />

          {/* Redireciona "/" para home correta */}
          <Route path="/" element={<HomeRedirect />} />

          {/* Paciente */}
          <Route path="/paciente/*" element={
            <ProtectedRoute role="Paciente">
              <HomePaciente />
            </ProtectedRoute>
          } />

          {/* Psicólogo */}
          <Route path="/psicologo/*" element={
            <ProtectedRoute role="Psicólogo">
              <HomePsicologo />
            </ProtectedRoute>
          } />

          {/* Fallback */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  )
}
