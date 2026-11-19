import { useMemo, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import FavButton from "../components/FavButton";
import { FORMATIONS, type Institution, type Level } from "../lib/catalog";
import { useFavorites } from "../lib/favorites";
import { useI18n } from "../lib/i18n";
import iconSparkle from "../assets/icon-sparkle.svg";
import shield from "../assets/shield-check.svg";
import check from "../assets/check.svg";
import search from "../assets/search.svg";
import circleCheck from "../assets/circle-check.svg";
import arrowUpRight from "../assets/arrow-up-right.svg";
import plus from "../assets/plus.svg";
import compass from "../assets/icon-compass.svg";
import compareIcon from "../assets/icon-compare.svg";
import arrowRight from "../assets/arrow-right.svg";

const INST: Institution[] = ["IIT", "ISB"];
const LEVELS: Level[] = ["Licence", "Prépa", "Ingénierie"];
const DOMAINS = ["Informatique & sciences", "Gestion & finance"] as const;

function Cbx({ on, label, onChange }: { on: boolean; label: string; onChange: () => void }) {
  return (
    <label className={`cbx ${on ? "on" : ""}`}>
      <input type="checkbox" checked={on} onChange={onChange} />
      <i>{on && <img src={check} alt="" />}</i>
      {label}
    </label>
  );
}

const toggle = <T,>(set: Set<T>, v: T) => {
  const n = new Set(set);
  n.has(v) ? n.delete(v) : n.add(v);
  return n;
};

export default function Formations() {
  const nav = useNavigate();
  const { t } = useI18n();
  const fav = useFavorites();
  const [onlyFav, setOnlyFav] = useState(false);
  const [inst, setInst] = useState<Set<Institution>>(new Set(INST));
  const [levels, setLevels] = useState<Set<Level>>(new Set(LEVELS));
  const [domains, setDomains] = useState<Set<string>>(new Set());
  const [q, setQ] = useState("");
  const [cmp, setCmp] = useState<string[]>(() => FORMATIONS.slice(0, 2).map((f) => f.id));

  const list = useMemo(() => {
    const s = q.trim().toLowerCase();
    return FORMATIONS.filter(
      (f) =>
        inst.has(f.institution) &&
        levels.has(f.level) &&
        (domains.size === 0 || domains.has(f.domain)) &&
        (!onlyFav || fav.has(f.id)) &&
        (!s || `${f.name} ${f.tagline} ${f.keywords} ${f.domain}`.toLowerCase().includes(s)),
    );
  }, [inst, levels, domains, q, onlyFav, fav.ids]);

  const count = (pred: (f: (typeof FORMATIONS)[number]) => boolean) => FORMATIONS.filter(pred).length;
  const toggleCmp = (id: string) =>
    setCmp((c) => (c.includes(id) ? c.filter((x) => x !== id) : c.length >= 3 ? c : [...c, id]));
  const reset = () => { setInst(new Set(INST)); setLevels(new Set(LEVELS)); setDomains(new Set()); setQ(""); setOnlyFav(false); };
  const selected = cmp.map((id) => FORMATIONS.find((f) => f.id === id)!).filter(Boolean);

  return (
    <div className="ws">
      <div className="heading">
        <div>
          <h1>Explorez les formations, ouvrez vos possibilités</h1>
          <p>IIT &amp; ISB · Des pistes à découvrir, sans choisir à votre place.</p>
        </div>
        <Link className="b" to="/comparaison">Mes pistes proposées <img src={iconSparkle} alt="" /></Link>
      </div>

      <div className="notice">
        <img src={shield} alt="" />
        <span>Catalogue de démonstration : intitulés, contenus, durées et conditions d’accès à confirmer auprès de l’établissement.</span>
      </div>

      <div className="layout">
        <aside className="side">
          <div className="panel">
            <h2>Affiner la recherche</h2>
            <Cbx on={onlyFav} label={`♥ ${t("Mes favoris")} · ${fav.ids.length}`} onChange={() => setOnlyFav(!onlyFav)} />
            <hr className="hr" />
            <p className="eyebrow2">Établissement</p>
            {INST.map((i) => <Cbx key={i} on={inst.has(i)} label={`${i} · ${count((f) => f.institution === i)}`} onChange={() => setInst(toggle(inst, i))} />)}
            <hr className="hr" />
            <p className="eyebrow2">Type de parcours</p>
            {LEVELS.map((l) => <Cbx key={l} on={levels.has(l)} label={`${l} · ${count((f) => f.level === l)}`} onChange={() => setLevels(toggle(levels, l))} />)}
            <hr className="hr" />
            <p className="eyebrow2">Domaine</p>
            {DOMAINS.map((d) => <Cbx key={d} on={domains.has(d)} label={d} onChange={() => setDomains(toggle(domains, d))} />)}
            <hr className="hr" />
            <button className="lnk" style={{ textAlign: "left" }} onClick={reset}>Réinitialiser les filtres</button>
          </div>
          <div className="panel tint">
            <h2>Besoin d’une boussole ?</h2>
            <p className="p-body">Votre goût des maths et du code peut guider votre exploration.</p>
            <div><button className="b" onClick={() => document.querySelector<HTMLButtonElement>(".fab")?.click()}>Parler à mon guide</button></div>
          </div>
        </aside>

        <section className="main">
          <div className="rowg" style={{ flexWrap: "nowrap" }}>
            <label className="search">
              <img src={search} alt="" />
              <input value={q} onChange={(e) => setQ(e.target.value)} placeholder="Rechercher une formation, un domaine…" aria-label="Rechercher" />
            </label>
            <span className="b">Trier : pertinence ⌄</span>
          </div>
          <div className="rowb">
            <b style={{ fontSize: 14, color: "var(--navy)" }}>{list.length} formation{list.length > 1 ? "s" : ""} illustrative{list.length > 1 ? "s" : ""}</b>
            <span className="chip2" style={{ border: "1px solid var(--line)" }}>
              {inst.size === 2 ? "IIT + ISB" : [...inst].join("")} · {levels.size === 3 ? "Tous les parcours" : [...levels].join(", ")}
            </span>
          </div>

          <div className="grid g2">
            {list.map((f) => {
              const on = cmp.includes(f.id);
              return (
                <article className="fcard" key={f.id}>
                  <div className="img"><img src={f.image} alt="" /><span className="badge">{f.institution}</span><FavButton on={fav.has(f.id)} onToggle={() => fav.toggle(f.id)} /></div>
                  <div className="rowb">
                    <div className="rowg" style={{ gap: 8 }}>
                      <span className="chip2 hl">{f.institution}</span>
                      <span className="chip2">{f.level}</span>
                    </div>
                    <img src={on ? circleCheck : plus} alt="" width={18} height={18} />
                  </div>
                  <h3>{f.name}</h3>
                  <p className="d">{f.tagline}</p>
                  <p className="m">{f.keywords}</p>
                  <p className="s">Contenu illustratif · Conditions à confirmer</p>
                  <div className="rowb">
                    <Link className="b" to={`/formations/${f.id}`}>Voir la formation <img src={arrowUpRight} alt="" /></Link>
                    <button className="lnk" style={{ fontSize: 12.5 }} onClick={() => toggleCmp(f.id)}>{on ? "✓ À comparer" : "＋ Comparer"}</button>
                  </div>
                </article>
              );
            })}
            {list.length === 0 && <p className="p-muted">Aucune formation ne correspond à ces filtres.</p>}
            <div className="col" style={{ padding: 22 }}>
              <img src={compass} alt="" width={27} height={27} />
              <b style={{ fontSize: 14, color: "var(--ink2)" }}>Un parcours, plusieurs questions</b>
              <span className="p-muted" style={{ color: "var(--muted3)" }}>
                Comparez les façons d’apprendre, les prérequis et les perspectives. Les passerelles vers l’ingénierie ne sont jamais garanties.
              </span>
              <b style={{ fontSize: 13.5, color: "var(--ink2)" }}>À discuter avec l’équipe IIT / ISB →</b>
            </div>
          </div>
        </section>
      </div>

      {selected.length > 0 && (
        <div className="compare-bar">
          <img src={compareIcon} alt="" />
          <div className="grow">
            <b>{selected.length} formation{selected.length > 1 ? "s" : ""} à comparer</b>
            {selected.map((f) => `${f.name} · ${f.institution}`).join("   +   ")}
          </div>
          <button className="b pri" disabled={selected.length < 2} onClick={() => nav(`/comparaison?ids=${cmp.join(",")}`)}>
            Comparer ma sélection <img src={arrowRight} alt="" />
          </button>
        </div>
      )}
    </div>
  );
}
