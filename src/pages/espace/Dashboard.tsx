import { Link } from "react-router-dom";
import Journey from "../../components/Journey";
import { initials } from "../../components/CandidateLayout";
import { useAuth } from "../../lib/auth";
import sparkles from "../../assets/d-sparkles.svg";
import arrowRight from "../../assets/d-arrow-right.svg";
import arrowUpRight from "../../assets/d-arrow-up-right.svg";
import message from "../../assets/d-message.svg";
import compare from "../../assets/d-compare.svg";
import clipboard from "../../assets/clipboard-list.svg";
import code from "../../assets/d-code.svg";
import calc from "../../assets/d-calc.svg";
import briefcase from "../../assets/briefcase.svg";
import messages from "../../assets/d-messages.svg";

const PREVIEWS = [
  { inst: "IIT", icon: code, t: "Licence · Informatique", d: "Apprendre par la pratique", id: "licence-info" },
  { inst: "IIT", icon: calc, t: "Cycle préparatoire", d: "Consolider les fondamentaux", id: "prepa" },
  { inst: "ISB", icon: briefcase, t: "Parcours en gestion", d: "Relier business et numérique", id: "gestion" },
];

export default function Dashboard() {
  const { user } = useAuth();
  const name = user?.full_name || user?.email || "";
  const first = name.split(/\s+/)[0] ?? "";

  return (
    <div className="ws" style={{ gap: 22 }}>
      <div className="rowb" style={{ padding: "8px 0" }}>
        <div>
          <h1 style={{ margin: 0, fontSize: 28, fontWeight: 600, letterSpacing: -0.8, color: "var(--navy)" }}>Bonjour {first}, dessinons la suite.</h1>
          <p className="p-muted" style={{ margin: "6px 0 0", fontSize: 14, color: "var(--muted2)" }}>Votre orientation prend forme. Avancez une étape à la fois, en toute confiance.</p>
        </div>
        <Link className="b" to="/espace/profil" style={{ color: "var(--navy)" }}>Voir mon profil <img src={arrowUpRight} alt="" /></Link>
      </div>

      <Journey current={1} chevrons />

      <div className="detail">
        <div className="l">
          <section className="nba">
            <div className="eb"><img src={sparkles} alt="" />VOTRE PROCHAINE ÉTAPE</div>
            <h2>Des maths au code,<br />quel chemin vous ressemble ?</h2>
            <p>Vous aimez les mathématiques et l’informatique. Reprenons votre échange pour explorer la Licence et la Prépa, sans choisir à votre place.</p>
            <div className="rowb">
              <button className="go" onClick={() => document.querySelector<HTMLButtonElement>(".fab")?.click()}>Reprendre mon orientation <img src={arrowRight} alt="" /></button>
              <span style={{ color: "var(--cyan)", fontSize: 13.5 }}>Dernier échange · aujourd’hui, 10:42</span>
            </div>
          </section>

          <div className="panel">
            <h2 style={{ color: "var(--navy)" }}>Votre parcours, en clair</h2>
            <div className="rowg" style={{ gap: 18, alignItems: "flex-start", flexWrap: "nowrap" }}>
              <div className="metric"><img src={message} alt="" /><b>01</b><span>Conversation démarrée</span></div>
              <div className="metric"><img src={compare} alt="" /><b>03</b><span>Pistes à explorer</span></div>
              <div className="metric"><img src={clipboard} alt="" /><b>À venir</b><span>Pré-inscription</span></div>
            </div>
            <hr className="hr" />
            <p className="p-muted" style={{ fontSize: 14, color: "var(--muted2)" }}>Aucun dossier envoyé pour le moment. Prenez le temps de comparer vos possibilités.</p>
          </div>

          <div className="panel">
            <h2 style={{ color: "var(--navy)" }}>À explorer ensemble</h2>
            <div className="grid g3" style={{ gap: 14 }}>
              {PREVIEWS.map((p) => (
                <div className="prev" key={p.id}>
                  <div className="rowb"><span className="chip2 hl line" style={{ color: "var(--navy)" }}>{p.inst}</span><img src={p.icon} alt="" /></div>
                  <b>{p.t}</b>
                  <span>{p.d}</span>
                  <Link to={`/formations/${p.id}`} style={{ fontSize: 13.5, fontWeight: 600, color: "var(--navy)" }}>Découvrir →</Link>
                </div>
              ))}
            </div>
          </div>
        </div>

        <div className="r">
          <div className="panel">
            <h2 style={{ color: "var(--navy)" }}>Votre profil se précise</h2>
            <div className="rowg" style={{ gap: 12, flexWrap: "nowrap" }}>
              <div className="avatar">{initials(name)}</div>
              <div className="kv" style={{ gap: 3 }}><b>{name}</b><small>Terminale · Bac mathématiques</small></div>
            </div>
            <div className="rowb" style={{ fontSize: 14, color: "var(--navy)" }}><span>Profil enrichi</span><span>60 %</span></div>
            <div className="prog"><i style={{ width: "60%" }} /></div>
            <hr className="hr" />
            <div className="kv"><small>Intérêts</small>Mathématiques, informatique</div>
            <div className="kv"><small>Projet</small>Devenir ingénieur logiciel</div>
            <div className="kv"><small>Préférence</small>Une approche progressive</div>
            <div><span className="chip2 amber" style={{ background: "#fff4de", border: 0 }}>À préciser · contraintes et mobilité</span></div>
          </div>
          <div className="panel" style={{ background: "#f5f8fc", borderRadius: 16 }}>
            <h2 style={{ color: "var(--navy)" }}>Une équipe à vos côtés</h2>
            <img src={messages} alt="" width={26} height={26} />
            <p className="p-body" style={{ fontSize: 14 }}>Une question sur votre futur parcours ? Le service admissions peut prendre le relais à tout moment.</p>
            <div><a className="b" href="mailto:admissions@iit.example" style={{ color: "var(--navy)" }}>Contacter un conseiller</a></div>
          </div>
        </div>
      </div>
    </div>
  );
}
