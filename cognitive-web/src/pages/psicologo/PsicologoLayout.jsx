import { Routes, Route } from "react-router-dom"
import SidebarPsicologo    from "../../components/SidebarPsicologo"
import PsicologoDashboard  from "./PsicologoDashboard"
import PsicologoAgenda     from "./PsicologoAgenda"
import PsicologoPacientes  from "./PsicologoPacientes"
import PsicologoVinculos   from "./PsicologoVinculos"
import PsicologoAtividades from "./PsicologoAtividades"
import PsicologoPerfil     from "./PsicologoPerfil"
import "./PsicologoLayout.css"

export default function PsicologoLayout() {
  return (
    <div className="psi-layout">
      <SidebarPsicologo />
      <main className="psi-main">
        <Routes>
          <Route index                   element={<PsicologoDashboard />}  />
          <Route path="agenda"           element={<PsicologoAgenda />}     />
          <Route path="pacientes/*"      element={<PsicologoPacientes />}  />
          <Route path="vinculos"         element={<PsicologoVinculos />}   />
          <Route path="atividades"       element={<PsicologoAtividades />} />
          <Route path="perfil"           element={<PsicologoPerfil />}     />
        </Routes>
      </main>
    </div>
  )
}