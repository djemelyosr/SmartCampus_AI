import { Link } from "react-router-dom";
import brandIcon from "../assets/brand-icon.svg";
import { useAuth } from "../lib/auth";
import { useI18n } from "../lib/i18n";
import LangSwitcher from "./LangSwitcher";

export default function PublicNav() {
  const { user, logout } = useAuth();
  const { t } = useI18n();
  return (
    <header className="nav">
      <Link to="/" className="brand">
        <div className="brand-symbol"><img src={brandIcon} alt="" /></div>
        <div>
          <div className="brand-name">SmartCampus</div>
          <div className="brand-sub">IIT &amp; ISB</div>
        </div>
      </Link>
      <nav className="nav-links">
        <Link to="/formations">{t("Découvrir les formations")}</Link>
        <a className="dim" href="mailto:admissions@iit.example">{t("Besoin d’aide ?")}</a>
        {user ? (
          <button className="pill" onClick={logout}>{user.full_name || user.email} · {t("Déconnexion")}</button>
        ) : (
          <Link className="pill" to="/connexion">{t("Se connecter")}</Link>
        )}
        <LangSwitcher />
      </nav>
    </header>
  );
}
