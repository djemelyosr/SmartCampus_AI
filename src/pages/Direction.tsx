import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import Icon from "../components/Icon";
import { api, type Stats } from "../lib/api";
import { useAuth } from "../lib/auth";

const DEMO_KPIS: [string, string, string, Parameters<typeof Icon>[0]["name"], string][] = [
  ["Conversations initiées", "1 200", "+18 %", "msg", ""],
  ["Pré-inscriptions", "552", "+12 %", "folder", ""],
  ["Conversion en inscription", "15,5 %", "+2,1 pts", "trend", ""],
  ["Dossiers en attente", "84", "24 prioritaires", "clock", "warn"],
];
const DEMO_FUNNEL: [string, number, string, string][] = [["Conversations", 1200, "100 % de la cohorte", "#f6e7b8"], ["Orientations", 920, "76,7 % de la cohorte", "#f6e7b8"], ["Pré-inscrits", 552, "46 % de la cohorte", "#78aecb"], ["Entretiens", 310, "25,8 % de la cohorte", "#126f9f"], ["Inscriptions", 186, "15,5 % de la cohorte", "#00518c"]];
const DEMO_COMPARE: [string, string, string][] = [["Conversations", "780", "420"], ["Pré-inscriptions", "370", "182"], ["Entretiens", "208", "102"], ["Inscriptions", "128", "58"], ["Conversion finale", "16,4 %", "13,8 %"]];
const DEMO_PROGRAMS: [string, number][] = [["IIT · Licence informatique", 210], ["IIT · Préparatoire", 102], ["ISB · Gestion", 96], ["ISB · Finance", 66], ["IIT · Ingénierie", 58]];
const DEMO_PENDING: [string, string, string, string, string][] = [["Fatma Kchaou", "IIT · Entretien confirmé", "Valider l’orientation →", "/equipe/examen", "IIT"], ["Mariem Kammoun", "ISB · Pré-inscription", "Examiner le dossier →", "/equipe/examen", "ISB"], ["Sarra Ayadi", "IIT · Dossier incomplet", "Relancer pour pièce →", "/equipe/examen", "IIT"]];

export default function Direction() {
  const { user } = useAuth();
  const canOpen = user?.role === "admin"; // candidate files are for the academic team; direction only sees aggregates
  const [inst, setInst] = useState("IIT & ISB");
  const [range, setRange] = useState("01 juin – 07 juillet 2026");
  const [cmp, setCmp] = useState(true);
  const [live, setLive] = useState<Stats | null>(null);
  useEffect(() => { api.stats().then(setLive).catch(() => setLive(null)); }, []);
  const FUNNEL = useMemo(() => {
    if (!live) return DEMO_FUNNEL;
    const base = live.funnel[0]?.value || 1;
    const cols = ["#f6e7b8", "#f6e7b8", "#78aecb", "#126f9f", "#00518c"];
    return live.funnel.map((f, i): [string, number, string, string] => [f.label, f.value, `${Math.round((1000 * f.value) / base) / 10} % de la cohorte`.replace(".", ","), cols[i] ?? "#00518c"]);
  }, [live]);
  const KPIS = useMemo(() => {
    if (!live) return DEMO_KPIS;
    const t = live.totals;
    return [
      ["Conversations initiées", String(t.conversations), "en direct", "msg", ""],
      ["Pré-inscriptions", String(t.preinscriptions), "en direct", "folder", ""],
      ["Conversion en inscription", `${String(t.conversion).replace(".", ",")} %`, "en direct", "trend", ""],
      ["Dossiers en attente", String(t.pending), "à suivre", "clock", "warn"],
    ] as typeof DEMO_KPIS;
  }, [live]);
  const COMPARE = useMemo(() => {
    const b = live?.by_institution;
    if (!b) return DEMO_COMPARE;
    const row = (l: string, k: keyof Stats["totals"], pct = false): [string, string, string] => [l, ...(["IIT", "ISB"] as const).map((i) => `${String(b[i][k]).replace(".", ",")}${pct ? " %" : ""}`)] as [string, string, string];
    return [row("Conversations", "conversations"), row("Pré-inscriptions", "preinscriptions"), row("Entretiens", "interviews"), row("Inscriptions", "enrollments"), row("Conversion finale", "conversion", true)];
  }, [live]);
  const PROGRAMS = useMemo(() => live ? live.programs.map((p): [string, number] => [`${p.institution} · ${p.name}`, p.interest]) : DEMO_PROGRAMS, [live]);
  const PENDING = useMemo(() => live ? live.pending.map((p): [string, string, string, string, string] => [p.candidate, `${p.institution ?? ""} · ${p.step}`, `${p.action} →`, "/equipe/examen", p.institution ?? ""]) : DEMO_PENDING, [live]);
  const max = FUNNEL[0]?.[1] || 1;
  const pend = useMemo(() => PENDING.filter((p) => inst === "IIT & ISB" || p[4] === inst), [inst, PENDING]);
  const prog = useMemo(() => PROGRAMS.filter(([n]) => inst === "IIT & ISB" || n.startsWith(inst)), [inst, PROGRAMS]);
  const pmax = Math.max(...prog.map((p) => p[1]), 1);

  return (
    <div className="ws" style={{ gap: 18 }}>
      <div className="rowb" style={{ alignItems: "flex-start" }}>
        <div>
          <h1 style={{ margin: 0, fontSize: 28, fontWeight: 600, letterSpacing: -0.8, color: "var(--navy)" }}>Une vue d’ensemble, des actions ciblées</h1>
          <p className="p-muted" style={{ margin: "6px 0 0", fontSize: 13, color: "var(--muted3)" }}>Campagne 2026-2027 · {live ? "Données agrégées en direct" : "Données agrégées de démonstration"}</p>
        </div>
        <button className="b" onClick={() => window.print()}>Exporter le rapport <Icon name="ur" size={13} /></button>
      </div>
      <div className="rowb">
        <div className="rowg" style={{ gap: 8 }}>
          <select className="sel" value={inst} onChange={(e) => setInst(e.target.value)} aria-label="Établissement">{["IIT & ISB", "IIT", "ISB"].map((o) => <option key={o}>{o}</option>)}</select>
          <select className="sel" value={range} onChange={(e) => setRange(e.target.value)} aria-label="Période">{["01 juin – 07 juillet 2026", "01 juillet – 07 juillet 2026", "Campagne complète"].map((o) => <option key={o}>{o}</option>)}</select>
        </div>
        <button className={`chip2 ${cmp ? "hl" : ""} line`} style={{ border: "1px solid var(--line)" }} onClick={() => setCmp(!cmp)}>Comparaison : période précédente</button>
      </div>

      <div className="grid g4" style={{ gap: 14 }}>
        {KPIS.map(([l, v, d, ic, tone]) => (
          <div className="stat" key={l}>
            <div className="rowb"><span className="l">{l}</span><Icon name={ic} size={15} color="var(--muted3)" /></div>
            <span className="v">{v}</span>
            <div><span className={`chip2 ${tone ? "warn" : "hl"}`} style={tone ? { background: "#fff4de", color: "#8d6417" } : { background: "var(--panel)" }}>{cmp || tone ? d : "—"}</span></div>
          </div>
        ))}
      </div>

      <div className="layout">
        <div className="panel" style={{ flex: "1 1 560px", gap: 12 }}>
          <h2 style={{ fontSize: 17 }}>Du premier échange à l’inscription</h2>
          <span className="small" style={{ fontSize: 12 }}>Candidats uniques par étape · Cohorte de démonstration</span>
          <div className="rowg" style={{ gap: 14, flexWrap: "nowrap" }}>{FUNNEL.map(([n, v]) => <b key={n} style={{ flex: 1, fontSize: 22, color: "var(--ink2)", fontWeight: 600 }}>{v.toLocaleString("fr-FR")}</b>)}</div>
          <div className="bars">{FUNNEL.map(([n, v, , col]) => <div className="c" key={n}><i style={{ height: `${(v / max) * 100}%`, background: col }} title={`${n} : ${v}`} /></div>)}</div>
          <div className="rowg" style={{ gap: 14, flexWrap: "nowrap", alignItems: "flex-start" }}>{FUNNEL.map(([n, , p]) => <div key={n} style={{ flex: 1, fontSize: 11 }}><b style={{ display: "block", fontSize: 12, color: "var(--ink2)" }}>{n}</b><span style={{ color: "var(--muted3)" }}>{p}</span></div>)}</div>
          <p className="small" style={{ fontSize: 12 }}><Icon name="shield" size={13} /> Point d’attention : 242 pré-inscrits n’ont pas encore réalisé l’entretien.</p>
        </div>
        <div className="panel" style={{ flex: "0 1 460px", gap: 8 }}>
          <h2 style={{ fontSize: 17 }}>IIT / ISB</h2>
          <span className="small" style={{ fontSize: 12 }}>Comparer les dynamiques, pas les candidats</span>
          <div className="row-tbl head" style={{ gridTemplateColumns: "1.4fr 1fr 1fr" }}><span>Indicateur</span><b style={{ color: "var(--blue2)" }}>IIT</b><b style={{ color: "var(--blue2)" }}>ISB</b></div>
          {COMPARE.map(([n, a, b]) => <div className="row-tbl" key={n} style={{ gridTemplateColumns: "1.4fr 1fr 1fr", fontSize: 13 }}><span>{n}</span><b style={{ color: "var(--blue2)" }}>{a}</b><b style={{ color: "var(--blue2)" }}>{b}</b></div>)}
        </div>
      </div>

      <div className="layout">
        <div className="panel" style={{ flex: "0 1 380px", gap: 12 }}>
          <h2 style={{ fontSize: 17 }}>Les parcours les plus demandés</h2>
          <span className="small" style={{ fontSize: 12 }}>Préférences exprimées · Ne vaut pas affectation</span>
          {prog.map(([n, v]) => <div className="col" key={n} style={{ gap: 6 }}><div className="rowb" style={{ fontSize: 12.5 }}><span>{n}</span><b>{v}</b></div><div className="hbar"><i style={{ width: `${(v / pmax) * 100}%` }} /></div></div>)}
        </div>
        <div className="panel" style={{ flex: "1 1 520px", gap: 8 }}>
          <h2 style={{ fontSize: 17 }}>Dossiers en attente d’action</h2>
          <div className="row-tbl head" style={{ gridTemplateColumns: "1fr 1.2fr 1.2fr" }}><span>Candidat</span><span>Étape</span><span>Action attendue</span></div>
          {pend.map(([n, e, a, to]) => <div className="row-tbl" key={n} style={{ gridTemplateColumns: "1fr 1.2fr 1.2fr" }}><b style={{ fontSize: 13 }}>{n}</b><span style={{ fontSize: 12.5, color: "var(--muted3)" }}>{e}</span>{canOpen ? <Link to={to} style={{ color: "var(--blue2)", fontWeight: 600, fontSize: 12.5 }}>{a}</Link> : <span title="Action pour l’équipe habilitée" style={{ color: "var(--blue2)", fontWeight: 600, fontSize: 12.5 }}>{a}</span>}</div>)}
          {pend.length === 0 && <p className="p-muted">Aucun dossier en attente pour cet établissement.</p>}
          <div className="notice" style={{ borderRadius: 8, justifyContent: "space-between", alignItems: "center" }}><span style={{ fontSize: 12.5, color: "var(--ink2)" }}><Icon name="bot" size={14} /> Agents IA · {live ? (live.agents.sourced_pct === null ? "—" : live.agents.sourced_pct) : 94} % de réponses avec source proposée · {live ? live.agents.handoffs : 18} relais humains</span><Link to="/admin/journal" className="chip2 hl" style={{ background: "#fff" }}>Voir le détail</Link></div>
        </div>
      </div>
    </div>
  );
}
