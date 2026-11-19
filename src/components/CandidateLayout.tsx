import { Link, NavLink, Outlet } from "react-router-dom";
import brandIcon from "../assets/brand-icon.svg";
import bell from "../assets/bell.svg";
import { useAuth } from "../lib/auth";
import { useI18n } from "../lib/i18n";
import LangSwitcher from "./LangSwitcher";

const TABS: [string, string][] = [
  ["/espace", "MON PARCOURS"],
  ["/comparaison", "MON ORIENTATION"],
  ["/formations", "MES FORMATIONS"],
  ["/espace/suivi", "MA CANDIDATURE"],
  ["/espace/entretien", "MES RENDEZ-VOUS"],
];

export const initials = (name: string) =>
  name.split(/\s+/).filter(Boolean).slice(0, 2).map((p) => p[0]!.toUpperCase()).join("") || "?";

/** Signed-in candidate header (Figma screens 09-18): IIT blue with gold accents + 5 tabs. */
export function CandidateHeader() {
  const { user, logout } = useAuth();
  const { t } = useI18n();
  return (
    <header className="cnav">
      <div className="gold" />
      <div className="top">
        <Link to="/espace" className="brand">
          <div className="brand-symbol"><img src={brandIcon} alt="" /></div>
          <div><div className="brand-name">SmartCampus</div><div className="brand-sub">IIT &amp; ISB</div></div>
        </Link>
        <div className="who">
          <LangSwitcher />
          <Link to="/espace/notifications" aria-label={t("Notifications")}><img src={bell} alt="" width={18} height={18} /></Link>
          <div className="lbl"><Link to="/espace/profil"><b>{t("Mon profil")}</b></Link><small>{t("Espace candidat")}</small></div>
          <button className="av" title={t("Se déconnecter")} onClick={logout}>{initials(user?.full_name || user?.email || "")}</button>
        </div>
      </div>
      <nav className="tabs">
        {TABS.map(([to, label]) => (
          <NavLink key={to} to={to} end className={({ isActive }) => `tab ${isActive ? "on" : ""}`}>
            <span>{t(label)}</span><i />
          </NavLink>
        ))}
      </nav>
      <div className="gold2" />
    </header>
  );
}

export default function CandidateLayout() {
  return (
    <div className="page">
      <CandidateHeader />
      <Outlet />
    </div>
  );
}
