import { useState } from "react";
import { Link } from "react-router-dom";
import Icon from "../../components/Icon";

const DAYS = ["Lun. 06", "Mar. 07", "Mer. 08", "Jeu. 09", "Ven. 10"];
const HOURS = ["09:00", "10:00", "11:00", "14:00"];
type Cell = { kind: "free" } | { kind: "busy"; t: string; s: string } | { kind: "conf"; t: string; s: string };
const SEED: Record<string, Cell> = {
  "0-09:00": { kind: "busy", t: "Lina Ben Ali", s: "30 min · Équipe" },
  "3-10:00": { kind: "conf", t: "Fatma Kchaou", s: "10:00-10:30 · Amira · Confirmé" },
  "0-11:00": { kind: "busy", t: "Réunion équipe", s: "30 min · Équipe" },
  "3-14:00": { kind: "busy", t: "Aziz Trabelsi", s: "30 min · Équipe" },
};
const QUEUE: [string, string, string, string][] = [
  ["Mariem Kammoun", "SC-2026-0431 · ISB · Gestion", "QCM terminé", "Invitation à préparer"],
  ["Nour Ayadi", "SC-2026-0435 · IIT · Prépa", "Disponibilités attendues", ""],
  ["Aziz Trabelsi", "SC-2026-0419 · IIT · Ingénierie", "Replanification à confirmer", ""],
];

export default function Planning() {
  const [pick, setPick] = useState<string>("4-11:00");
  const [cand, setCand] = useState("Mariem Kammoun - ISB");
  const [mode, setMode] = useState("Visioconférence");
  const [msg, setMsg] = useState("");
  const [prop, setProp] = useState({ slot: "Ven. 10 juillet · 14:00 – 14:30", why: "Empêchement du candidat" });
  const label = (k: string) => { const [d, h] = k.split("-"); return `${DAYS[Number(d)]!.replace(".", "")} juillet · ${h}`; };

  return (
    <div className="ws" style={{ gap: 18 }}>
      <div className="rowb">
        <div>
          <h1 style={{ margin: 0, fontSize: 28, fontWeight: 600, letterSpacing: -0.8, color: "var(--navy)" }}>Planning des entretiens</h1>
          <p className="p-muted" style={{ margin: "6px 0 0", fontSize: 13, color: "var(--muted3)" }}>Planning IIT / ISB · Semaine du 6 au 10 juillet 2026 · Heure de Tunis (UTC+1)</p>
        </div>
        <button className="b" onClick={() => setMsg("Gestion des disponibilités : prototype de démonstration.")}>Gérer les disponibilités <Icon name="calendar" size={14} /></button>
      </div>
      <div className="rowg" style={{ gap: 8 }}>
        {["IIT & ISB ⌄", "Tous les conseillers ⌄", "Tous les statuts ⌄"].map((f) => <span key={f} className="b" style={{ padding: "8px 12px", fontSize: 12.5, borderRadius: 8 }}>{f}</span>)}
        <span className="chip2 hl line">Données de démonstration</span>
      </div>

      <div className="layout">
        <div className="main" style={{ gap: 14, flex: "1 1 700px" }}>
          <div className="panel">
            <h2 style={{ fontSize: 16 }}>Calendrier de l’équipe</h2>
            <div className="rowb"><span style={{ fontSize: 12.5, fontWeight: 600, color: "var(--ink2)" }}>6 – 10 juillet 2026</span><span className="rowg" style={{ gap: 6 }}><button className="b" style={{ padding: "4px 10px" }}>‹</button><button className="b" style={{ padding: "6px 12px", fontSize: 12.5 }}>Aujourd’hui</button><button className="b" style={{ padding: "4px 10px" }}>›</button></span></div>
            <div style={{ display: "grid", gridTemplateColumns: "44px repeat(5, minmax(0, 1fr))", gap: 8 }}>
              <small style={{ fontSize: 10, color: "var(--muted3)" }}>UTC+1</small>
              {DAYS.map((d, i) => <b key={d} style={{ fontSize: 12, textAlign: "center", padding: 6, borderRadius: 6, background: i === 3 ? "var(--panel)" : "none", color: "var(--ink2)" }}>{d}</b>)}
              {HOURS.map((h) => (
                <FragmentRow key={h} h={h}>
                  {DAYS.map((_, i) => {
                    const k = `${i}-${h}`;
                    const c = SEED[k] ?? { kind: "free" as const };
                    const picked = pick === k && c.kind === "free";
                    return (
                      <button key={k} className={`slot ${c.kind === "conf" ? "conf" : picked ? "pick" : c.kind === "busy" ? "busy" : ""}`} onClick={() => c.kind === "free" && setPick(k)} disabled={c.kind !== "free" && c.kind !== "conf"}>
                        {c.kind === "free" ? (picked ? <><b>Créneau sélectionné</b><span>{h}-{h.replace(/(\d+):(\d+)/, (_, a, b) => `${a}:${Number(b) + 30}`)} · Amira · Libre</span></> : "Disponible") : <><b>{c.t}</b><span>{c.s}</span></>}
                      </button>
                    );
                  })}
                </FragmentRow>
              ))}
            </div>
            <div className="rowg" style={{ gap: 10 }}><span className="chip2 hl">Confirmé</span><span className="chip2 hl line" style={{ background: "#fff" }}>Libre</span><span className="small" style={{ fontSize: 11.5 }}>Pas de 30 min · Créneau sélectionné : {label(pick).toLowerCase()}</span></div>
          </div>

          <div className="panel">
            <h2 style={{ fontSize: 16 }}>File des candidats · À planifier</h2>
            <div className="row-tbl head" style={{ gridTemplateColumns: "1fr 1.2fr 24px" }}><span>Candidat / parcours</span><span style={{ textAlign: "right" }}>Préparation et suite</span><span /></div>
            {QUEUE.map(([n, ref, st, act]) => (
              <button key={n} className="row-tbl" style={{ gridTemplateColumns: "1fr 1.2fr 24px", background: "none", border: 0, borderBottom: "1px solid #eef3f8", textAlign: "left" }} onClick={() => setCand(`${n} - ${ref.includes("ISB") ? "ISB" : "IIT"}`)}>
                <span><b style={{ display: "block", fontSize: 13 }}>{n}</b><small style={{ fontSize: 11.5, color: "var(--muted3)" }}>{ref}</small></span>
                <span style={{ textAlign: "right", fontSize: 12, color: "var(--muted3)" }}>{st}{act && <><br />{act}</>}</span><span>›</span>
              </button>
            ))}
          </div>

          <div className="panel">
            <h2 style={{ fontSize: 16 }}>Replanification à préparer</h2>
            <div className="rowb"><b style={{ fontSize: 13 }}>Aziz Trabelsi · SC-2026-0419</b><span className="chip2" style={{ background: "#fff4de", color: "#8d6417" }}>Accord candidat attendu</span></div>
            <p className="p-muted" style={{ fontSize: 12.5 }}>Créneau actuel : jeudi 9 juillet à 14:00. L’équipe peut proposer une nouvelle disponibilité ; le rendez-vous actuel est conservé jusqu’à confirmation.</p>
            <div className="grid g2" style={{ gap: 14 }}>
              <label className="fld" style={{ fontSize: 12 }}>Nouveau créneau proposé<select className="sel" value={prop.slot} onChange={(e) => setProp({ ...prop, slot: e.target.value })}>{["Ven. 10 juillet · 14:00 – 14:30", "Ven. 10 juillet · 09:00 – 09:30", "Mer. 8 juillet · 11:00 – 11:30"].map((o) => <option key={o}>{o}</option>)}</select></label>
              <label className="fld" style={{ fontSize: 12 }}>Motif de replanification<select className="sel" value={prop.why} onChange={(e) => setProp({ ...prop, why: e.target.value })}>{["Empêchement du candidat", "Indisponibilité du conseiller", "Autre motif"].map((o) => <option key={o}>{o}</option>)}</select></label>
            </div>
            <div><button className="b" style={{ fontSize: 12.5 }} onClick={() => setMsg(`Proposition préparée : ${prop.slot} (${prop.why}). Aucune notification envoyée dans la démonstration.`)}>Préparer la proposition <Icon name="calendar" size={14} /></button></div>
            <p className="small" style={{ fontSize: 11 }}>Aucune modification ni notification effectuée dans la démonstration.</p>
          </div>
        </div>

        <aside className="side" style={{ width: 330, gap: 14 }}>
          <div className="panel tint" style={{ borderRadius: 12, gap: 10 }}>
            <h2 style={{ fontSize: 15 }}>Rendez-vous confirmé</h2>
            <div><span className="chip2 hl line" style={{ fontSize: 11 }}>Fatma Kchaou · SC-2026-0426</span></div>
            <p style={{ fontSize: 20, fontWeight: 600, color: "var(--ink2)", lineHeight: 1.3 }}>Jeudi 9 juillet 2026<br />10:00 – 10:30</p>
            <p className="p-muted" style={{ fontSize: 12, lineHeight: 1.5 }}>Amira Mansour · Admissions IIT<br />Visioconférence · Heure de Tunis (UTC+1)</p>
            <hr className="hr" />
            <div className="kvx"><small>PRÉFÉRENCE CANDIDAT</small><b>Licence en informatique · IIT</b></div>
            <p className="p-muted" style={{ fontSize: 12 }}>Synthèse IA à relire : aime les mathématiques et le code ; préfère une progression pratique par projets. Hésite entre Licence et Prépa.</p>
            <div className="grid g2" style={{ gap: 10 }}><div className="kvx"><small>QCM DU 07 JUILLET</small><b>9 / 12 · Illustratif</b></div><div className="kvx"><small>POINT À VÉRIFIER</small><b>Relevé encore demandé</b></div></div>
            <p className="small" style={{ fontSize: 11 }}>Logique 4/5 · Maths 3/4 · Culture numérique 2/3. Aucun résultat d’admission.</p>
            <Link className="b" style={{ fontSize: 12.5, borderRadius: 8 }} to="/equipe/entretien">Ouvrir le dossier entretien <Icon name="ur" size={13} /></Link>
            <button className="b" style={{ fontSize: 12.5, borderRadius: 8 }} onClick={() => setMsg("Replanification proposée au candidat (démonstration).")}>Proposer une replanification <Icon name="calendar" size={13} /></button>
            <p className="small" style={{ fontSize: 11 }}>Le créneau confirmé reste inchangé tant que le nouveau rendez-vous n’est pas accepté.</p>
          </div>

          <div className="panel" style={{ gap: 12 }}>
            <h2 style={{ fontSize: 16 }}>Préparer une invitation</h2>
            <div><span className="chip2 hl line" style={{ fontSize: 11 }}>Créneau libre sélectionné</span></div>
            <label className="fld" style={{ fontSize: 12 }}>Candidat<select className="sel" value={cand} onChange={(e) => setCand(e.target.value)}>{["Mariem Kammoun - ISB", "Nour Ayadi - IIT", "Aziz Trabelsi - IIT"].map((o) => <option key={o}>{o}</option>)}</select></label>
            <label className="fld" style={{ fontSize: 12 }}>Conseiller<select className="sel"><option>Amira Mansour</option><option>Sami Gharbi</option></select></label>
            <label className="fld" style={{ fontSize: 12 }}>Créneau · Heure de Tunis<input className="sel" readOnly value={`${label(pick)} – ${pick.split("-")[1]!.replace(/(\d+):(\d+)/, (_, a, b) => `${a}:${Number(b) + 30}`)}`} /></label>
            <label className="fld" style={{ fontSize: 12 }}>Mode<select className="sel" value={mode} onChange={(e) => setMode(e.target.value)}>{["Visioconférence", "Sur site", "Téléphone"].map((o) => <option key={o}>{o}</option>)}</select></label>
            <div><button className="b pri" style={{ fontSize: 12.5, borderRadius: 8 }} onClick={() => setMsg(`Invitation préparée pour ${cand} · ${label(pick)} · ${mode}. Aucune invitation envoyée dans cette démonstration.`)}>Préparer l’invitation <Icon name="mail" size={14} color="#fff" /></button></div>
            <p className="small" style={{ fontSize: 11 }}>Aperçu à relire avant envoi. Aucune invitation envoyée dans cette démonstration.</p>
          </div>
        </aside>
      </div>
      {msg && <p className="okbox" role="status">{msg}</p>}
      <div className="notice" style={{ borderRadius: 9 }}><Icon name="shield" size={16} color="var(--blue2)" /><span style={{ fontSize: 13, color: "var(--ink2)" }}>Les créneaux et les scores servent à préparer l’échange. L’avis d’entretien et la décision officielle restent du ressort des personnes habilitées.</span></div>
    </div>
  );
}

function FragmentRow({ h, children }: { h: string; children: React.ReactNode }) {
  return <><small style={{ fontSize: 11, color: "var(--muted3)", paddingTop: 10 }}>{h}</small>{children}</>;
}
