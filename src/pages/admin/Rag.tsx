import { useMemo, useState } from "react";
import { Link } from "react-router-dom";
import AdminShell from "../../components/AdminShell";
import Icon from "../../components/Icon";

interface Doc { name: string; meta: string; inst: string; state: "Indexé" | "En cours" | "Échec OCR"; date: string; pct?: number }
const DOCS0: Doc[] = [
  { name: "Catalogue des parcours IIT.pdf", meta: "PDF · 2,4 Mo · Contenu à vérifier", inst: "IIT", state: "Indexé", date: "07 juil." },
  { name: "Présentation des programmes ISB.pdf", meta: "PDF · 1,8 Mo · Contenu à vérifier", inst: "ISB", state: "Indexé", date: "06 juil." },
  { name: "Guide de candidature – brouillon.pdf", meta: "PDF · 3,1 Mo · Contenu à vérifier", inst: "IIT / ISB", state: "En cours", date: "07 juil.", pct: 68 },
  { name: "Questions fréquentes – scan.pdf", meta: "PDF · 6,2 Mo · Texte non lisible", inst: "IIT / ISB", state: "Échec OCR", date: "07 juil." },
];
const AGENTS: [string, string, string][] = [["Orientation", "Profil & recommandations", "12 relais à examiner"], ["Admission", "Pré-inscription & QCM", "4 dossiers en attente"], ["Suivi", "E-mails & rendez-vous", "2 rappels à contrôler"]];

export default function Rag() {
  const [docs, setDocs] = useState(DOCS0);
  const [q, setQ] = useState("");
  const [inst, setInst] = useState("Tous les établissements");
  const [msg, setMsg] = useState("");
  const list = useMemo(() => docs.filter((d) => d.name.toLowerCase().includes(q.toLowerCase()) && (inst.startsWith("Tous") || d.inst.includes(inst))), [docs, q, inst]);
  const failed = docs.filter((d) => d.state === "Échec OCR").length;
  const retry = (n: string) => { setDocs(docs.map((d) => (d.name === n ? { ...d, state: "En cours", pct: 5 } : d))); setMsg("Relance OCR préparée (démonstration)."); };
  const add = () => {
    const name = window.prompt("Nom du document PDF à ajouter :");
    if (name?.trim()) setDocs([{ name: name.trim().endsWith(".pdf") ? name.trim() : `${name.trim()}.pdf`, meta: "PDF · en attente · Contenu à vérifier", inst: "IIT / ISB", state: "En cours", date: "08 juil.", pct: 0 }, ...docs]);
  };

  return (
    <AdminShell title="La confiance se configure" sub="Sources documentaires, agents et règles de fonctionnement · Environnement de démonstration"
      action={<Link className="b" to="/admin/journal">Journal d’activité <Icon name="ur" size={13} /></Link>}>
      <div className="grid g3" style={{ gap: 14 }}>
        <div className="stat"><span className="l">Sources documentaires</span><span className="v">{docs.length + 20}</span><small className="small" style={{ fontSize: 12 }}>{docs.filter((d) => d.state === "Indexé").length + 20} indexées · {docs.filter((d) => d.state === "En cours").length} en cours</small></div>
        <div className="stat"><span className="l">Agents actifs</span><span className="v">3 / 3</span><small className="small" style={{ fontSize: 12 }}>18 relais humains ouverts</small></div>
        <div className="stat"><span className="l">Ingestion à reprendre</span><span className="v">{failed}</span><small style={{ fontSize: 12, color: "#8d6417" }}>Action administrateur requise</small></div>
      </div>

      <div className="panel" style={{ gap: 12 }}>
        <div className="rowb" style={{ alignItems: "flex-start" }}>
          <div><h2 style={{ fontSize: 17 }}>Base de connaissances · Sources RAG</h2><span className="small" style={{ fontSize: 12 }}>Indexation technique ≠ validation du contenu. Documents fictifs, à vérifier.</span></div>
          <button className="b dark" style={{ borderRadius: 8, background: "var(--blue2)", borderColor: "var(--blue2)" }} onClick={add}>Ajouter une source <Icon name="plus" size={14} color="#fff" /></button>
        </div>
        <div className="rowg" style={{ gap: 10, flexWrap: "nowrap" }}>
          <label className="search" style={{ height: 38 }}><Icon name="search" size={15} color="var(--muted3)" /><input value={q} onChange={(e) => setQ(e.target.value)} placeholder="Rechercher un document…" aria-label="Rechercher un document" /></label>
          <select className="sel" value={inst} onChange={(e) => setInst(e.target.value)}>{["Tous les établissements", "IIT", "ISB"].map((o) => <option key={o}>{o}</option>)}</select>
        </div>
        <div className="row-tbl head" style={{ gridTemplateColumns: "2.4fr .8fr 1fr .8fr 30px" }}><span>Document</span><span>Établissement</span><span>Ingestion</span><span>Mise à jour</span><span /></div>
        {list.map((d) => (
          <div className="row-tbl" key={d.name} style={{ gridTemplateColumns: "2.4fr .8fr 1fr .8fr 30px" }}>
            <div className="rowg" style={{ gap: 10, flexWrap: "nowrap" }}><Icon name="file" size={16} color="var(--blue2)" /><div className="kvx"><b style={{ fontSize: 13 }}>{d.name}</b><small>{d.meta}</small></div></div>
            <span>{d.inst}</span>
            <span><span className="chip2" style={d.state === "Indexé" ? { background: "var(--panel)", color: "var(--blue2)" } : d.state === "En cours" ? { background: "var(--panel)", color: "var(--blue2)" } : { background: "#fff4de", color: "#8d6417" }}>{d.state === "En cours" ? `En cours · ${d.pct} %` : d.state}</span></span>
            <span style={{ color: "var(--muted3)" }}>{d.date}</span>
            {d.state === "Échec OCR" ? <button aria-label="Relancer l’OCR" className="lnk" onClick={() => retry(d.name)}><Icon name="refresh" size={15} /></button> : <Icon name="dots" size={16} color="var(--muted3)" />}
          </div>
        ))}
        {list.length === 0 && <p className="p-muted">Aucun document ne correspond à la recherche.</p>}
        {failed > 0 && <div className="warnbox" style={{ borderRadius: 6 }}><Icon name="shield" size={15} color="#8d6417" />{failed} source exclue des réponses : relancer l’OCR ou importer un PDF avec texte sélectionnable.</div>}
        {msg && <p className="okbox" role="status">{msg}</p>}
      </div>

      <div className="panel" style={{ gap: 12 }}>
        <h2 style={{ fontSize: 17 }}>Supervision des agents</h2>
        <div className="grid g3" style={{ gap: 14 }}>
          {AGENTS.map(([n, d, r]) => (
            <div key={n} className="prev" style={{ borderRadius: 8 }}>
              <div className="rowb"><Icon name="bot" size={16} color="var(--muted3)" /><span className="chip2 hl" style={{ fontSize: 11 }}>Actif</span></div>
              <b>{n}</b><span style={{ fontSize: 12 }}>{d}</span><span style={{ fontSize: 12, color: "var(--ink2)" }}>{r}</span>
              <Link to="/admin/journal" style={{ fontSize: 12.5, fontWeight: 600, color: "var(--navy)" }}>Inspecter l’activité →</Link>
            </div>
          ))}
        </div>
        <hr className="hr" />
        <div className="rowb"><span style={{ fontSize: 12.5, color: "var(--ink2)" }}><Icon name="shield" size={14} /> Validation humaine obligatoire avant toute décision d’admission. Règle active pour tous les agents.</span><span className="chip2 hl line" style={{ fontSize: 11 }}>Règle verrouillée</span></div>
      </div>
    </AdminShell>
  );
}
