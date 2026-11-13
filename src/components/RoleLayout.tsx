import { Link, NavLink, Outlet } from "react-router-dom";
import brandIcon from "../assets/brand-icon.svg";
import Icon from "./Icon";
import { initials } from "./CandidateLayout";
import { homeFor, useAuth } from "../lib/auth";
import { useI18n } from "../lib/i18n";
import LangSwitcher from "./LangSwitcher";

export const ROLE_LABEL: Record<string, string> = {
  iit_head: "Responsable académique",
  isb_head: "Responsable académique",
  interviewer: "Responsable entretien",
  direction: "Direction",
  admin: "Administrateur",
  candidate: "Espace candidat",
};

export const DOSSIERS_TAB: [string, string] = ["/equipe/examen", "DOSSIERS CANDIDATS"];
export const INTERVIEW_TAB: [string, string] = ["/equipe/planning", "ENTRETIENS"];
export const TEAM_TABS: [string, string][] = [DOSSIERS_TAB, INTERVIEW_TAB];
export const STATS_TAB: [string, string] = ["/equipe/statistiques", "STATISTIQUES"];
export const DIRECTION_TABS: [string, string][] = [["/direction", "PILOTAGE"]];
export const ADMIN_TABS: [string, string][] = [["/admin", "ADMINISTRATION"]];

/** Tabs shown to each team role. Academic heads only see candidate files; interviewers also see interviews. */
export function tabsFor(role: string): [string, string][] {
  if (role === "direction") return DIRECTION_TABS;
  if (role === "admin") return ADMIN_TABS;
  if (role === "interviewer") return TEAM_TABS;
  return [DOSSIERS_TAB, STATS_TAB]; // iit_head, isb_head
}

/** Header shared by team screens. `tabs` differ per area (équipe, direction, administration). */
export function RoleHeader({ tabs }: { tabs: [string, string][] }) {
  const { user, logout } = useAuth();
  const { t } = useI18n();
  return (
    <header className="cnav">
      <div className="gold" />
      <div className="top">
        <Link to={homeFor(user?.role ?? "")} className="brand">
          <div className="brand-symbol"><img src={brandIcon} alt="" /></div>
          <div><div className="brand-name">SmartCampus</div><div className="brand-sub">IIT &amp; ISB</div></div>
        </Link>
        <div className="who">
          <LangSwitcher />
          <Icon name="bell" size={16} color="#e6edf8" />
          <div className="lbl"><b>{t("Mon profil")}</b><small>{t(ROLE_LABEL[user?.role ?? ""] ?? "")}</small></div>
          <button className="av" title={t("Se déconnecter")} onClick={logout}>{initials(user?.full_name || user?.email || "")}</button>
        </div>
      </div>
      <nav className="tabs" style={{ justifyContent: "flex-start" }}>
        {tabs.map(([to, label]) => (
          <NavLink key={to} to={to} className={({ isActive }) => `tab ${isActive ? "on" : ""}`} style={{ flex: "0 0 260px" }}>
            <span>{t(label)}</span><i />
          </NavLink>
        ))}
      </nav>
      <div className="gold2" />
    </header>
  );
}

export default function RoleLayout({ tabs }: { tabs?: [string, string][] }) {
  const { user } = useAuth();
  return (
    <div className="page">
      <RoleHeader tabs={tabs ?? tabsFor(user?.role ?? "")} />
      <Outlet />
    </div>
  );
}
