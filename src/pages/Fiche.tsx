import { Link, Navigate, useNavigate, useParams } from "react-router-dom";
import Journey from "../components/Journey";
import { FORMATIONS } from "../lib/catalog";
import { useAuth } from "../lib/auth";
import arrowLeft from "../assets/arrow-left.svg";
import profileSpark from "../assets/profile-spark.svg";
import codeXml from "../assets/code-xml.svg";
import calculator from "../assets/calculator.svg";
import users from "../assets/users.svg";
import arrowRight from "../assets/arrow-right.svg";
import compareIcon from "../assets/icon-compare.svg";

const SKILLS = [
  { icon: codeXml, t: "Créer et expérimenter", d: "Écrire, tester et améliorer un programme." },
  { icon: calculator, t: "Raisonner avec méthode", d: "Décomposer un problème et expliquer une solution." },
  { icon: users, t: "Apprendre par les projets", d: "Collaborer et présenter un travail concret." },
];

export default function Fiche() {
  const { id } = useParams();
  const nav = useNavigate();
  const { user } = useAuth();
  const f = FORMATIONS.find((x) => x.id === id);
  if (!f) return <Navigate to="/formations" replace />;
  const isLicence = f.id === "licence-info";

  return (
    <div className="ws" style={{ gap: 22 }}>
      <div className="rowb">
        <div>
          <h1 style={{ margin: 0, fontSize: 28, fontWeight: 600, letterSpacing: -0.8, color: "var(--ink2)" }}>{f.name}</h1>
          <p className="p-muted" style={{ margin: "6px 0 0", fontSize: 14 }}>Mes formations / Catalogue / {f.name} · {f.institution}</p>
        </div>
        <Link className="b" to="/formations">Retour au catalogue <img src={arrowLeft} alt="" /></Link>
      </div>

      <Journey current={2} />

      <section className="hero-dark">
        <div className="ov">
          <div className="rowg" style={{ gap: 8 }}>
            <span className="chip2 hl">{f.institution}</span>
            <span className="chip2 hl">{f.level} · Fiche illustrative</span>
          </div>
          <h2>{isLicence ? "Du raisonnement à vos premiers projets logiciels." : f.tagline}</h2>
          <p>
            {isLicence
              ? "Une piste pour développer votre pratique du code et construire votre projet pas à pas, avec des bases scientifiques et des projets concrets."
              : `Une piste autour de : ${f.keywords}. Contenu illustratif, à confirmer avec ${f.institution}.`}
          </p>
        </div>
        <aside className="aff">
          <img src={profileSpark} alt="" width={24} height={24} />
          <b>En lien avec votre profil</b>
          <p>Maths, informatique et apprentissage progressif : des points à explorer ensemble.</p>
          <small>Affinité indicative · Pas une admission</small>
        </aside>
      </section>

      <div className="detail">
        <div className="l">
          <div className="panel">
            <h2>Ce que vous pourriez explorer</h2>
            <p className="p-body" style={{ fontSize: 14, color: "var(--ink2)" }}>
              Une approche pédagogique envisagée autour de la programmation, de la logique et de la résolution de problèmes. Le contenu officiel et l’organisation sont à confirmer avec {f.institution}.
            </p>
            <div className="grid g3" style={{ gap: 16 }}>
              {SKILLS.map((s) => (
                <div className="skill" key={s.t}><img src={s.icon} alt="" /><b>{s.t}</b><span>{s.d}</span></div>
              ))}
            </div>
          </div>

          <div className="grid g2">
            <div className="panel">
              <h2>Cette piste vous parle si…</h2>
              <div className="p-body" style={{ color: "var(--ink2)" }}>
                • Vous aimez les maths et l’informatique.<br />• Vous avez envie de créer des logiciels.<br />• Vous préférez avancer par la pratique.
              </div>
              <p className="small">Des repères pour réfléchir, pas des critères d’éligibilité.</p>
            </div>
            <div className="panel">
              <h2>Des perspectives à explorer</h2>
              <p className="p-body" style={{ color: "var(--ink2)" }}>Développement logiciel, projets numériques et poursuite d’études selon votre parcours.</p>
              <p className="small">Débouchés indicatifs. Aucune promesse d’emploi ni de passerelle vers l’ingénierie.</p>
            </div>
          </div>

          <div className="panel">
            <h2>Prérequis et informations à vérifier</h2>
            <div className="rowb">
              <span className="p-body" style={{ color: "var(--ink2)" }}>Avant de vous engager, échangez avec l’établissement.</span>
              <span className="chip2 warn" style={{ background: "#fff4de", color: "#8d6417" }}>À confirmer</span>
            </div>
            {[
              ["Accès au parcours", "Bac et dossier académique à examiner par l’équipe pédagogique."],
              ["Organisation et frais", "Durée, programme, calendrier et frais à confirmer auprès de l’établissement."],
              ["Poursuite en ingénierie", "Possibilités à étudier selon le dossier, sans passerelle garantie."],
            ].map(([t, d]) => (
              <div className="chk" key={t}><b>{t}</b><span>{d}</span></div>
            ))}
          </div>
        </div>

        <div className="r">
          <div className="panel tint">
            <h2>Votre prochaine étape</h2>
            <div><span className="chip2 hl">{f.institution} · Parcours à explorer</span></div>
            <p className="big">Une préférence,<br />pas un engagement définitif.</p>
            <p className="p-body" style={{ fontSize: 14, color: "var(--ink2)" }}>
              Pour transmettre votre préinscription, créez un compte ou connectez-vous. Votre choix ne vaut pas admission.
            </p>
            <div><button className="b pri" style={{ borderRadius: 9 }} onClick={() => nav(user ? `/preinscription?formation=${f.id}` : "/inscription")}>Me pré-inscrire <img src={arrowRight} alt="" /></button></div>
            <div><Link className="b" to={`/comparaison?ids=${f.id}`}>Ajouter à ma comparaison <img src={compareIcon} alt="" /></Link></div>
            <p className="small">Rentrée visée : septembre 2026 · Campagne démo</p>
          </div>
          <div className="panel">
            <h2>Et la Prépa ?</h2>
            <p className="p-body" style={{ color: "var(--ink2)" }}>Le cycle préparatoire est une autre piste si vous souhaitez approfondir vos bases scientifiques avant de vous spécialiser.</p>
            <div><Link className="b" to="/comparaison?ids=licence-info,prepa">Comparer Licence et Prépa</Link></div>
          </div>
          <div className="panel">
            <h2>Une question sur ce parcours ?</h2>
            <p className="p-body" style={{ color: "var(--ink2)" }}>Un conseiller peut vous aider à vérifier les conditions d’accès, le rythme et les poursuites possibles.</p>
            <div><a className="b" href="mailto:admissions@iit.example">Contacter un conseiller</a></div>
            <hr className="hr" />
            <p className="small">Documentation {f.institution} · à vérifier<br />Synthèse illustrative, sans source officielle validée.</p>
          </div>
        </div>
      </div>
    </div>
  );
}
