import { NavLink, useNavigate } from "react-router-dom"
import { useAuth } from "../context/AuthContext"
import "./Sidebar.css"

const NAV = [
  { to: "/psicologo",            icon: "🏠", label: "Início"      },
  { to: "/psicologo/pacientes",  icon: "👥", label: "Pacientes"   },
  { to: "/psicologo/agenda",     icon: "📅", label: "Agenda"      },
  { to: "/psicologo/vinculos",   icon: "🔗", label: "Vínculos"    },
  { to: "/psicologo/atividades", icon: "🏃", label: "Atividades"  },
  { to: "/psicologo/perfil",     icon: "👤", label: "Perfil"      },
]

export default function SidebarPsicologo() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()

  function handleLogout() {
    logout()
    navigate("/login")
  }

  return (
    <aside className="sidebar">
      <div className="sidebar-logo">
        <span className="sidebar-logo-icon">🧠</span>
        <span className="sidebar-logo-text">Cognitive</span>
      </div>

      <div className="sidebar-user">
        <div className="sidebar-avatar">
          {user?.username?.[0]?.toUpperCase() || "P"}
        </div>
        <div>
          <p className="sidebar-username">{user?.username}</p>
          <p className="sidebar-role" style={{ color: "#5b8dd9" }}>Psicólogo</p>
        </div>
      </div>

      <nav className="sidebar-nav">
        {NAV.map(({ to, icon, label }) => (
          <NavLink key={to} to={to} end={to === "/psicologo"}
            className={({ isActive }) => `sidebar-link ${isActive ? "sidebar-link--active" : ""}`}>
            <span className="sidebar-link-icon">{icon}</span>
            <span>{label}</span>
          </NavLink>
        ))}
      </nav>

      <button className="sidebar-logout" onClick={handleLogout}>
        <span>🚪</span> Sair
      </button>
    </aside>
  )
}