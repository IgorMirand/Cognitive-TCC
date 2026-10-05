import { createContext, useContext, useState, useEffect } from "react"
import { authAPI } from "../api/api"

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)        // { id, username, user_type }
  const [loading, setLoading] = useState(true)

  // Recupera sessão salva ao abrir o app
  useEffect(() => {
    const saved = localStorage.getItem("user")
    if (saved) setUser(JSON.parse(saved))
    setLoading(false)
  }, [])

  async function login(email, password) {
    const data = await authAPI.login(email, password)
    // Salva o JWT para os próximos requests
    localStorage.setItem("token", data.access_token)
    const userData = { id: data.id, username: data.username, user_type: data.user_type }
    localStorage.setItem("user", JSON.stringify(userData))
    setUser(userData)
    return userData
  }

  function logout() {
    localStorage.removeItem("token")
    localStorage.removeItem("user")
    setUser(null)
  }

  return (
    <AuthContext.Provider value={{ user, loading, login, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

// Hook para usar em qualquer componente
export const useAuth = () => useContext(AuthContext)
