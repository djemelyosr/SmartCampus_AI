import { useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import Journey from "../components/Journey";
import { FORMATIONS } from "../lib/catalog";
import { useAuth } from "../lib/auth";
import arrowUpRight from "../assets/arrow-up-right.svg";
import circleCheck from "../assets/circle-check.svg";
import check from "../assets/check.svg";
import route from "../assets/route.svg";
import arrowRight from "../assets/arrow-right.svg";

interface Detail { aff: string; why: string; how: string; pre: string; talk: string }

const DETAILS: Record<string, Detail> = {
  "licence-info": { aff: "Affinité élevée", why: "Votre envie de coder et d’avancer progressivement rejoint cette piste.", how: "Projets, programmation et bases scientifiques.", pre: "Bac et dossier académique à examiner.", talk: "Vérifier les possibilités de poursuite en ingénierie." },
  prepa: { aff: "Affinité à explorer", why: "Votre goût des maths peut être un atout pour une approche scientifique.", how: "Fondamentaux et raisonnement scientifique.", pre: "Profil scientifique à étudier avec IIT.", talk: "Échanger sur le rythme et la part de théorie." },
  gestion: { aff: "Alternative à explorer", why: "Une piste si le numérique appliqué à l’entreprise vous attire aussi.", how: "Gestion, projets et enjeux de l’entreprise.", pre: "Bac et intérêt pour la gestion à préciser.", talk: "Moins directement lié à votre objectif logiciel." },
};
const generic = (keywords: string, inst: string): Detail => ({
  aff: "Alternative à explorer", why: "Une piste complémentaire à considérer selon vos intérêts.", how: keywords + ".", pre: `Prérequis à confirmer avec ${inst}.`, talk: "Échanger avec l’équipe sur l’adéquation avec votre projet.",
});

const PROFILE = ["Maths & informatique", "Ingénierie logicielle", "Apprendre par les projets"];
const DEFAULT_IDS = ["licence-info", "prepa", "gestion"];

export default function Comparaison() {
  const [params] = useSearchParams();
  const nav = useNavigate();
  const { user } = useAuth();
  const raw = params.get("ids")?.split(",").filter(Boolean) ?? [];
  const ids = raw.length >= 2 ? raw : [...raw, ...DEFAULT_IDS.filter((d) => !raw.includes(d))].slice(0, 3);
  const items = ids.map((id) => FORMATIONS.find((f) => f.id === id)).filter((f): f is NonNullable<typeof f> => !!f);
  const [chosen, setChosen] = useState(items[0]?.id);
  const chosenF = items.find((f) => f.id === chosen);

  return (
    <div className="ws" style={{ gap: 22 }}>
      <div className="rowb">
        <div>
          <h1 style={{ margin: 0, fontSize: 28, fontWeight: 600, letterSpacing: -0.8, color: "var(--navy)" }}>Plusieurs chemins. Votre choix.</h1>
          <p className="p-muted" style={{ margin: "6px 0 0", fontSize: 14, color: "var(--muted2)" }}>Des pistes expliquées à partir de vos intérêts, de votre projet et de votre façon d’apprendre.</p>
        </div>
        <button className="b" onClick={() => document.querySelector<HTMLButtonElement>(".fab")?.click()}>Affiner avec mon guide <img src={arrowUpRight} alt="" /></button>
      </div>

      <Journey current={2} chevrons />

      <div className="rowg" style={{ gap: 10 }}>
        <span className="p-muted" style={{ flex: 1, color: "var(--muted2)" }}>Votre boussole</span>
        {PROFILE.map((p) => <span className="chip2 line" style={{ background: "#f5f8fc" }} key={p}>{p}</span>)}
        <span className="chip2 hl line">{items.length} pistes comparées</span>
      </div>

      <div className="grid" style={{ gridTemplateColumns: `repeat(${Math.max(items.length, 1)}, minmax(0, 1fr))` }}>
        {items.map((f) => {
          const d = DETAILS[f.id] ?? generic(f.keywords, f.institution);
          const sel = chosen === f.id;
          return (
            <article className={`cmp ${sel ? "sel" : ""}`} key={f.id}>
              <div className="rowb"><span className="chip2 hl line">{f.institution}</span>{sel && <img src={circleCheck} alt="" width={18} height={18} />}</div>
              <h2>{f.name}</h2>
              <div><span className={`chip2 line ${d.aff === "Affinité élevée" ? "hl" : ""}`} style={d.aff === "Affinité élevée" ? undefined : { background: "#f5f8fc" }}>{d.aff}</span></div>
              <p className="small" style={{ color: "var(--muted2)" }}>Affinité indicative · pas une décision d’admission</p>
              <hr className="hr" />
              <div className="sec first"><b>Pourquoi cette piste ?</b><span>{d.why}</span></div>
              <div className="sec"><b>Approche pédagogique envisagée</b><span>{d.how}</span></div>
              <div className="sec"><b>Prérequis à confirmer</b><span>{d.pre}</span></div>
              <div className="att"><b>À discuter avec l’équipe</b><span>{d.talk}</span></div>
              <div>
                {sel ? (
                  <button className="b dark">Parcours retenu <img src={check} alt="" /></button>
                ) : (
                  <button className="b" onClick={() => setChosen(f.id)}>Explorer cette piste <img src={arrowUpRight} alt="" /></button>
                )}
              </div>
            </article>
          );
        })}
      </div>

      <div className="compare-bar">
        <img src={route} alt="" style={{ width: 26, height: 26 }} />
        <div className="grow">
          <b style={{ fontSize: 15 }}>Votre préférence : {chosenF?.name} · {chosenF?.institution}</b>
          Pour conserver vos échanges et déposer un dossier, créez un compte ou connectez-vous.
        </div>
        <button className="b dark" onClick={() => nav(user ? `/preinscription?formation=${chosen}` : "/inscription")}>
          Continuer vers la préinscription <img src={arrowRight} alt="" />
        </button>
      </div>

      <div className="rowb" style={{ alignItems: "flex-start" }}>
        <p className="p-muted" style={{ maxWidth: 750, fontSize: 12.5, lineHeight: 1.5, color: "var(--muted2)", margin: 0 }}>
          Et l’Ingénierie IIT ? Une poursuite à explorer selon votre parcours et l’étude de votre dossier, sans passerelle garantie. Documentation IIT / ISB · à vérifier.
        </p>
        <Link to="/formations" style={{ fontSize: 13.5, fontWeight: 600, color: "var(--navy)" }}>Voir tous les parcours →</Link>
      </div>
    </div>
  );
}
