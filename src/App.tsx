import { BrowserRouter, Navigate, Outlet, Route, Routes } from "react-router-dom";
import RoleLayout, { ADMIN_TABS, DIRECTION_TABS } from "./components/RoleLayout";
import Decision from "./pages/espace/Decision";
import Examen from "./pages/equipe/Examen";
import Planning from "./pages/equipe/Planning";
import Entretien from "./pages/equipe/Entretien";
import Statistiques from "./pages/equipe/Statistiques";
import Direction from "./pages/Direction";
import Rag from "./pages/admin/Rag";
import Users from "./pages/admin/Users";
import Programmes from "./pages/admin/Programmes";
import Campagnes from "./pages/admin/Campagnes";
import IA from "./pages/admin/IA";
import Journal from "./pages/admin/Journal";
import CandidateLayout from "./components/CandidateLayout";
import ChatWidget from "./components/ChatWidget";
import SafeWidget from "./components/SafeWidget";
import AppHeader from "./components/AppHeader";
import RequireAuth from "./components/RequireAuth";
import { AuthProvider, homeFor, useAuth } from "./lib/auth";
import { LangProvider } from "./lib/i18n";
import Comparaison from "./pages/Comparaison";
import Fiche from "./pages/Fiche";
import Formations from "./pages/Formations";
import Home from "./pages/Home";
import Login from "./pages/Login";
import Recuperation from "./pages/Recuperation";
import Register from "./pages/Register";
import Dashboard from "./pages/espace/Dashboard";
import ProfilEdit from "./pages/espace/ProfilEdit";
import Preinscription from "./pages/espace/Preinscription";
import Documents from "./pages/espace/Documents";
import QcmEnCours from "./pages/espace/QcmEnCours";
import QcmResultats from "./pages/espace/QcmResultats";
import Rendezvous from "./pages/espace/Rendezvous";
import Notifications from "./pages/espace/Notifications";

function TeamHome() {
  const { user } = useAuth();
  return <Navigate to={homeFor(user?.role ?? "")} replace />;
}

function PublicLayout() {
  return (
    <div className="page">
      <AppHeader />
      <Outlet />
    </div>
  );
}

export default function App() {
  return (
    <LangProvider>
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route element={<PublicLayout />}>
            <Route path="/" element={<Home />} />
            <Route path="/formations" element={<Formations />} />
            <Route path="/formations/:id" element={<Fiche />} />
            <Route path="/comparaison" element={<Comparaison />} />
            <Route path="/connexion" element={<Login />} />
            <Route path="/inscription" element={<Register />} />
            <Route path="/recuperation" element={<Recuperation />} />
          </Route>
          <Route path="/espace" element={<RequireAuth roles={["candidate"]}><CandidateLayout /></RequireAuth>}>
            <Route index element={<Dashboard />} />
            <Route path="profil" element={<ProfilEdit />} />
            <Route path="preinscription" element={<Preinscription />} />
            <Route path="documents" element={<Documents />} />
            <Route path="qcm" element={<QcmEnCours />} />
            <Route path="qcm/resultats" element={<QcmResultats />} />
            <Route path="entretien/reserver" element={<Rendezvous confirmed={false} />} />
            <Route path="entretien" element={<Rendezvous confirmed />} />
            <Route path="suivi" element={<Decision />} />
            <Route path="notifications" element={<Notifications />} />
          </Route>
          <Route path="/equipe" element={<RequireAuth roles={["iit_head", "isb_head", "interviewer"]}><RoleLayout /></RequireAuth>}>
            <Route index element={<TeamHome />} />
            <Route path="examen" element={<Examen />} />
            <Route path="statistiques" element={<RequireAuth roles={["iit_head", "isb_head"]}><Statistiques /></RequireAuth>} />
            <Route path="planning" element={<RequireAuth roles={["interviewer"]}><Planning /></RequireAuth>} />
            <Route path="entretien" element={<RequireAuth roles={["interviewer"]}><Entretien /></RequireAuth>} />
          </Route>
          <Route element={<RequireAuth roles={["direction"]}><RoleLayout tabs={DIRECTION_TABS} /></RequireAuth>}>
            <Route path="/direction" element={<Direction />} />
          </Route>
          <Route path="/admin" element={<RequireAuth roles={["admin"]}><RoleLayout tabs={ADMIN_TABS} /></RequireAuth>}>
            <Route index element={<Rag />} />
            <Route path="utilisateurs" element={<Users />} />
            <Route path="formations" element={<Programmes />} />
            <Route path="campagnes" element={<Campagnes />} />
            <Route path="ia" element={<IA />} />
            <Route path="journal" element={<Journal />} />
          </Route>
        </Routes>
        <SafeWidget><ChatWidget /></SafeWidget>
      </BrowserRouter>
    </AuthProvider>
    </LangProvider>
  );
}
