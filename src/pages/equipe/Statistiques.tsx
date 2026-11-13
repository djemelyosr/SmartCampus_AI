import { useEffect, useMemo, useState } from "react";
import Icon from "../../components/Icon";
import { api, type Stats } from "../../lib/api";
import { useAuth } from "../../lib/auth";

type Inst = "IIT" | "ISB";
// Demonstration data (aggregates only): to be replaced by a statistics endpoint.
const INTERESTS: [Inst, string, number][] = [
  ["IIT", "Licence informatique", 210], ["IIT", "Préparatoire", 102], ["IIT", "Ingénierie", 58],
  ["ISB", "Gestion", 96], ["ISB", "Finance", 66],
];
const ORIENT: [Inst, string, number, number, number][] = [
  // inst, programme, orientations proposées, pré-inscrits, validées
  ["IIT", "Licence informatique", 188, 142, 31], ["IIT", "Préparatoire", 96, 70, 18], ["IIT", "Ingénierie", 54, 41, 9],
  ["ISB", "Gestion", 90, 71, 12], ["ISB", "Finance", 61, 44, 10],
];
const FUNNEL: [Inst, string, number][] = [
  ["IIT", "Conversations", 780], ["IIT", "Pré-inscriptions", 370], ["IIT", "Entretiens", 208], ["IIT", "Inscriptions", 128],
  ["ISB", "Conversations", 420], ["ISB", "Pré-inscriptions", 182], ["ISB", "Entretiens", 102], ["ISB", "Inscriptions", 58],
];

export default function Statistiques() {
  const { user } = useAuth();
  const own: Inst = user?.role === "isb_head" ? "ISB" : "IIT";
  const [range, setRange] = useState("Campagne complète");
  const [live, setLive] = useState<Stats | null>(null);
  useEffect(() => { api.stats().then(setLive).catch(() => setLive(null)); }, [own]);
  const interests = useMemo(() => live ? live.programs.map((p) => [p.institution, p.name, p.interest] as [Inst, string, number]) : INTERESTS.filter((r) => r[0] === own), [own, live]);
  const orient = useMemo(() => live ? live.programs.map((p) => [p.institution, p.name, p.orientations, p.preinscriptions, p.validated] as [Inst, string, number, number, number]) : ORIENT.filter((r) => r[0] === own), [own, live]);
  const funnel = useMemo(() => live ? live.funnel.map((f) => [own, f.label, f.value] as [Inst, string, number]) : FUNNEL.filter((r) => r[0] === own), [own, live]);
  const imax = Math.max(...interests.map((r) => r[2]), 1);
  const fmax = Math.max(...funnel.map((r) => r[2]), 1);
  const total = interests.reduce((s, r) => s + r[2], 0);

  return (
    <div className="ws" style={{ gap: 18 }}>
      <div className="rowb" style={{ alignItems: "flex-start" }}>
        <div>
          <h1 style={{ margin: 0, fontSize: 28, fontWeight: 600, letterSpacing: -0.8, color: "var(--navy)" }}>Intérêts et orientations · {own}</h1>
          <p className="p-muted" style={{ margin: "6px 0 0", fontSize: 13, color: "var(--muted3)" }}>Campagne 2026-2027 · {live ? "Données agrégées en direct" : "Données agrégées de démonstration"} · Aucun candidat identifiable</p>
        </div>
        <button className="b" onClick={() => window.print()}>Exporter les statistiques <Icon name="ur" size={13} /></button>
      </div>
      <div className="rowg" style={{ gap: 8 }}>
        <select className="sel" value={range} onChange={(e) => setRange(e.target.value)} aria-label="Période">{["Campagne complète", "01 juin – 07 juillet 2026", "01 juillet – 07 juillet 2026"].map((o) => <option key={o}>{o}</option>)}</select>
      </div>

      <div className="grid g4" style={{ gap: 14 }}>
        <div className="stat"><div className="rowb"><span className="l">Intérêts exprimés</span><Icon name="msg" size={15} color="var(--muted3)" /></div><span className="v">{total}</span></div>
        <div className="stat"><div className="rowb"><span className="l">Orientations proposées</span><Icon name="trend" size={15} color="var(--muted3)" /></div><span className="v">{orient.reduce((s, r) => s + r[2], 0)}</span></div>
        <div className="stat"><div className="rowb"><span className="l">Pré-inscrits</span><Icon name="shield" size={15} color="var(--muted3)" /></div><span className="v">{orient.reduce((s, r) => s + r[3], 0)}</span></div>
        <div className="stat"><div className="rowb"><span className="l">Validées</span><Icon name="folder" size={15} color="var(--muted3)" /></div><span className="v">{orient.reduce((s, r) => s + r[4], 0)}</span></div>
      </div>

      <div className="layout">
        <div className="panel" style={{ flex: "0 1 420px", gap: 12 }}>
          <h2 style={{ fontSize: 17 }}>Parcours les plus demandés</h2>
          <span className="small" style={{ fontSize: 12 }}>Préférences exprimées · Ne vaut pas affectation</span>
          {interests.map(([, n, v]) => (
            <div className="col" key={n} style={{ gap: 6 }}>
              <div className="rowb" style={{ fontSize: 12.5 }}><span>{n}</span><b>{v}</b></div>
              <div className="hbar"><i style={{ width: `${(v / imax) * 100}%` }} /></div>
            </div>
          ))}
        </div>
        <div className="panel" style={{ flex: "1 1 520px", gap: 8 }}>
          <h2 style={{ fontSize: 17 }}>Orientations proposées par l’IA et avis académique</h2>
          <div className="row-tbl head" style={{ gridTemplateColumns: "1.4fr 1fr 1fr 1fr" }}><span>Parcours</span><span>Proposées</span><span>Pré-inscrits</span><span>Validées</span></div>
          {orient.map(([, n, p, c, a]) => (
            <div className="row-tbl" key={n} style={{ gridTemplateColumns: "1.4fr 1fr 1fr 1fr", fontSize: 13 }}><span>{n}</span><b>{p}</b><b>{c}</b><b>{a}</b></div>
          ))}
          <p className="small" style={{ fontSize: 12 }}><Icon name="shield" size={13} /> La confirmation ou l’ajustement d’une recommandation reste une décision humaine.</p>
        </div>
      </div>

      <div className="panel" style={{ gap: 12 }}>
        <h2 style={{ fontSize: 17 }}>Du premier échange à l’inscription · {own}</h2>
        <div className="bars">{funnel.map(([, n, v]) => <div className="c" key={n}><i style={{ height: `${(v / fmax) * 100}%`, background: "#126f9f" }} title={`${n} : ${v}`} /></div>)}</div>
        <div className="rowg" style={{ gap: 14, flexWrap: "nowrap" }}>{funnel.map(([, n, v]) => <div key={n} style={{ flex: 1, fontSize: 11 }}><b style={{ display: "block", fontSize: 14, color: "var(--ink2)" }}>{v}</b><span style={{ color: "var(--muted3)" }}>{n}</span></div>)}</div>
      </div>
    </div>
  );
}
