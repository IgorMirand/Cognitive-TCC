import { Routes, Route } from "react-router-dom"
import Sidebar from "../../components/Sidebar"
import PacienteDashboard  from "./PacienteDashboard"
import PacienteDiario     from "./PacienteDiario"
import PacienteAgenda     from "./PacienteAgenda"
import PacienteNotificacoes from "./PacienteNotificacoes"
import PacientePerfil     from "./PacientePerfil"
import "./PacienteLayout.css"

export default function PacienteLayout() {
  return (
    <div className="paciente-layout">
      <Sidebar />
      <main className="paciente-main">
        <Routes>
          <Route index                  element={<PacienteDashboard />} />
          <Route path="diario"          element={<PacienteDiario />} />
          <Route path="agenda"          element={<PacienteAgenda />} />
          <Route path="notificacoes"    element={<PacienteNotificacoes />} />
          <Route path="perfil"          element={<PacientePerfil />} />
        </Routes>
      </main>
    </div>
  )
}