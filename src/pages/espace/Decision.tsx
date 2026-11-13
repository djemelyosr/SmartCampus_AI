import { Link } from "react-router-dom";
import { useAuth } from "../../lib/auth";

const STEPS: [string, string, string][] = [
  ["01 · Préinscription reçue", "06 juillet · Votre préférence : Licence en informatique, IIT.", ""],
  ["02 · QCM terminé", "07 juillet · Bilan transmis au conseiller, sans décision automatique.", ""],
  ["03 · Entretien réalisé", "09 juillet · Échange avec Amira Mansour ; compte rendu à examiner.", ""],
  ["04 · Décision officielle en attente", "Après examen humain du dossier et vérification des pièces.", ""],
];

/** Screen 17: candidate follow-up after the interview, until the institution's decision. */
export default function Decision() {
  const { user } = useAuth();
  return (
    <div className="ws" style={{ gap: 22, maxWidth: 1000 }}>
      <div>
        <h1 style={{ margin: 0, fontSize: 28, fontWeight: 600, letterSpacing: -0.8, color: "var(--navy)" }}>Votre candidature, jusqu’à la décision</h1>
        <p className="p-muted" style={{ margin: "14px 0 0", fontSize: 13, color: "var(--muted3)" }}>{user?.full_name} · Dossier SC-2026-0426 · Licence en informatique, IIT · Exemple après entretien : 09 juillet 2026, 11:00</p>
      </div>
      <div className="notice" style={{ padding: 20, flexDirection: "column", gap: 10 }}>
        <b style={{ fontSize: 16, color: "var(--ink2)" }}>Entretien réalisé · Dossier en cours d’étude</b>
        <span style={{ fontSize: 13, color: "var(--ink2)" }}>L’équipe habilitée examine votre dossier. Aucune admission n’est confirmée à ce stade. Vous serez informée dans votre espace et par e-mail.</span>
      </div>

      <div className="grid g2">
        <div className="panel" style={{ gap: 14 }}>
          <h2 style={{ fontSize: 18, color: "var(--navy)" }}>Les étapes de votre dossier</h2>
          {STEPS.map(([t, d]) => (
            <div className="kvx" key={t} style={{ gap: 5 }}><b style={{ fontSize: 13 }}>{t}</b><small style={{ fontSize: 12 }}>{d}</small></div>
          ))}
        </div>
        <div className="panel" style={{ gap: 14 }}>
          <h2 style={{ fontSize: 18, color: "var(--navy)" }}>Une pièce reste à fournir</h2>
          <p className="p-muted" style={{ fontSize: 12.5 }}>Le relevé de notes est demandé pour compléter l’étude du dossier. Le document déjà déposé reste à vérifier par l’équipe.</p>
          <div><Link className="b pri" style={{ borderRadius: 6, fontSize: 12.5 }} to="/espace/documents">Ajouter mon relevé de notes</Link></div>
          <p className="p-muted" style={{ fontSize: 12.5 }}>Vous ne disposez pas encore du document ? Signalez-le au conseiller pour connaître la marche à suivre.</p>
          <div><a className="b" style={{ borderRadius: 6, fontSize: 12.5 }} href="mailto:admissions@iit.example">Contacter mon conseiller</a></div>
        </div>
      </div>

      <div className="panel" style={{ gap: 16 }}>
        <h2 style={{ fontSize: 20, color: "var(--navy)" }}>Et après la décision ?</h2>
        <div className="grid g2">
          <div className="panel tint" style={{ borderRadius: 6, gap: 10, borderColor: "transparent" }}>
            <b style={{ fontSize: 14, color: "var(--ink2)" }}>Si la décision est favorable</b>
            <span className="p-muted" style={{ fontSize: 12.5 }}>Consultez la notification officielle, les conditions et les pièces requises. Suivez ensuite les modalités d’inscription communiquées par l’établissement.</span>
          </div>
          <div className="panel tint" style={{ borderRadius: 6, gap: 10, borderColor: "transparent" }}>
            <b style={{ fontSize: 14, color: "var(--ink2)" }}>Si un complément est nécessaire</b>
            <span className="p-muted" style={{ fontSize: 12.5 }}>Ajoutez les informations demandées et suivez leur vérification. Une nouvelle orientation peut être discutée avec le conseiller.</span>
          </div>
        </div>
        <b style={{ fontSize: 12.5, color: "var(--ink2)" }}>Inscription finale : elle n’est confirmée qu’après validation des formalités par l’établissement. La préinscription, le QCM et l’entretien ne la remplacent pas.</b>
      </div>

      <div className="rowg" style={{ gap: 12 }}>
        <Link className="b pri" style={{ borderRadius: 6 }} to="/espace/notifications">Voir mes notifications</Link>
        <Link className="b" style={{ borderRadius: 6 }} to="/espace/documents">Consulter mes documents</Link>
        <Link className="b" style={{ borderRadius: 6 }} to="/espace">Retour à mon parcours</Link>
      </div>
      <p className="small" style={{ fontSize: 11.5 }}>État illustratif de démonstration · Les décisions et les confirmations officielles sont réservées aux équipes habilitées.</p>
    </div>
  );
}
