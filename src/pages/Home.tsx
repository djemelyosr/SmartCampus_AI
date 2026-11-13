import { Link } from "react-router-dom";
import { useI18n } from "../lib/i18n";

const STEPS = [
  ["01", "Échanger", "Chatbot libre, texte ou audio."],
  ["02", "S’orienter", "Comparer les pistes et les formations."],
  ["03", "Se préinscrire", "Créer un compte et transmettre le dossier."],
  ["04", "Passer le QCM", "Préparer l’entretien avec un bilan ciblé."],
  ["05", "Rencontrer et suivre", "Réserver, échanger et suivre la décision."],
];

export default function Home() {
  const { t } = useI18n();
  return (
    <div className="container">
      <section className="hero">
        <div className="hero-left">
          <p className="eyebrow">{t("ORIENTATION IIT & ISB · ACCÈS LIBRE")}</p>
          <h1 className="h1">{t("Votre avenir commence")}<br />{t("par une conversation.")}</h1>
          <p className="lead">
            {t("Un doute entre Licence, Prépa, Ingénierie ou les formations ISB ? Échangez avec SmartCampus et explorez des pistes adaptées à votre projet.")}
          </p>
          <p className="text-muted">
            {t("Aucune inscription pour discuter ou comparer les formations.")}<br />
            {t("Français, dialecte tunisien ou Arabizi · Texte et audio.")}
          </p>
          <div className="row">
            <Link className="btn" to="/formations">{t("Découvrir les formations")}</Link>
            <Link className="btn" to="/connexion">{t("J’ai déjà un compte")}</Link>
          </div>
        </div>
        <aside className="card hero-right">
          <h2 className="h3">{t("Un guide à vos côtés")}</h2>
          <p className="tag">{t("FRANÇAIS · TOUNSI · ARABIZI")}</p>
          <div className="welcome">
            <b>{t("Une question sur votre orientation ?")}</b>
            <span className="text-muted" style={{ color: "var(--ink)" }}>
              {t("Cliquez sur l’icône de conversation en bas à droite. Le guide s’ouvre ici, sans quitter l’accueil.")}
            </span>
          </div>
          <p className="small">{t("Accès libre, sans compte · Échangez par texte ou audio à votre rythme.")}</p>
        </aside>
      </section>

      <section style={{ display: "flex", flexDirection: "column", gap: 18 }}>
        <h2 className="h2">{t("Un parcours simple, dans le bon ordre")}</h2>
        <div className="steps">
          {STEPS.map(([n, tt, d]) => (
            <div className="step" key={n}>
              <span className="num">{n}</span>
              <span className="ttl">{t(tt)}</span>
              <span className="dsc">{t(d)}</span>
            </div>
          ))}
        </div>
      </section>

      <section className="split">
        <div className="card">
          <h2 className="h3">{t("Un compte seulement pour aller plus loin")}</h2>
          <p className="text-muted">
            {t("Sauvegardez vos échanges, retrouvez vos choix et suivez votre candidature. La création du compte ne vaut pas préinscription.")}
          </p>
          <div><Link className="btn" to="/inscription" style={{ display: "inline-block" }}>{t("Créer mon compte candidat")}</Link></div>
        </div>
        <div className="card">
          <h2 className="h3">{t("L’IA vous guide. Vous gardez le choix.")}</h2>
          <p className="text-muted">
            {t("Un conseiller peut prendre le relais. L’orientation et le QCM sont des aides : seule l’équipe habilitée de l’établissement décide de l’admission.")}
          </p>
          <div><a className="btn" href="mailto:admissions@iit.example" style={{ display: "inline-block" }}>{t("Contacter les admissions")}</a></div>
        </div>
      </section>

      <p className="small">
        {t("Maquette de démonstration · Formations, conditions d’accès et sources à confirmer auprès de l’IIT / ISB. Accès équipe réservé aux comptes habilités.")}
      </p>
    </div>
  );
}
