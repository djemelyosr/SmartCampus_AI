import { useState } from "react";
import AdminShell from "../../components/AdminShell";
import Icon from "../../components/Icon";

type Status = "À vérifier" | "Brouillon" | "En validation" | "Publié";
interface P { id: string; inst: string; type: string; name: string; status: Status; ref: string; intro: string; duree: string; pre: string; outs: string; doc: string; passage: string }
const P0: P[] = [
  { id: "lic", inst: "IIT", type: "Licence", name: "Licence en informatique", status: "À vérifier", ref: "PRG-IIT-LIC-INFO · v0.3", intro: "Un parcours pour explorer l’informatique, la programmation et les projets logiciels. Contenu à confirmer auprès de l’établissement.", duree: "Non renseignée", pre: "À renseigner par le responsable académique à partir d’une source officielle validée. Aucun seuil de notes ou diplôme requis confirmé.", outs: "Développement logiciel, activités numériques. Exemples d’orientation, sans garantie d’emploi ni de poursuite d’études.", doc: "Catalogue des parcours IIT.pdf", passage: "Référence officielle à joindre par l’établissement" },
  { id: "pre", inst: "IIT", type: "Prépa", name: "Cycle préparatoire", status: "Brouillon", ref: "PRG-IIT-PRE-01 · v0.1", intro: "Consolider les fondamentaux scientifiques avant de se spécialiser.", duree: "Non renseignée", pre: "À renseigner.", outs: "Poursuite d’études selon le dossier.", doc: "Catalogue des parcours IIT.pdf", passage: "" },
  { id: "ing", inst: "IIT", type: "Ingénierie", name: "Ingénierie informatique", status: "À vérifier", ref: "PRG-IIT-ING-01 · v0.2", intro: "Explorer une spécialisation selon le parcours antérieur.", duree: "Non renseignée", pre: "À renseigner.", outs: "Conception de systèmes, projet technique.", doc: "Catalogue des parcours IIT.pdf", passage: "" },
  { id: "ges", inst: "ISB", type: "Licence", name: "Parcours en gestion", status: "Brouillon", ref: "PRG-ISB-GES-01 · v0.1", intro: "Relier les enjeux de l’entreprise et les usages du numérique.", duree: "Non renseignée", pre: "À renseigner.", outs: "Gestion, organisation, projets.", doc: "Présentation des programmes ISB.pdf", passage: "" },
];
const TONE: Record<Status, React.CSSProperties> = { "À vérifier": { background: "#fff4de", color: "#8d6417" }, Brouillon: { background: "var(--panel)", color: "var(--blue2)" }, "En validation": { background: "var(--panel)", color: "var(--blue2)" }, Publié: { background: "#e3f4ea", color: "#1b6b3a" } };

export default function Programmes() {
  const [list, setList] = useState(P0);
  const [sel, setSel] = useState("lic");
  const [q, setQ] = useState("");
  const [inst, setInst] = useState("IIT & ISB");
  const [verified, setVerified] = useState(false);
  const [msg, setMsg] = useState("");
  const cur = list.find((p) => p.id === sel)!;
  const set = (k: keyof P, v: string) => setList(list.map((p) => (p.id === sel ? { ...p, [k]: v } : p)));
  const vis = list.filter((p) => (inst === "IIT & ISB" || p.inst === inst) && p.name.toLowerCase().includes(q.toLowerCase()));
  const add = () => { const id = `p${list.length}`; setList([...list, { id, inst: "IIT", type: "Licence", name: "Nouveau programme", status: "Brouillon", ref: `PRG-NEW-${list.length} · v0.1`, intro: "", duree: "Non renseignée", pre: "", outs: "", doc: "Catalogue des parcours IIT.pdf", passage: "" }]); setSel(id); };

  return (
    <AdminShell title="Des parcours clairs, des informations vérifiées" sub="Programmes IIT / ISB · Catalogue de démonstration · Campagne 2026-2027"
      action={<button className="b gold" onClick={add}>Ajouter un programme <Icon name="plus" size={14} /></button>}>
      <div className="warnbox"><Icon name="shield" size={15} color="#8d6417" />SmartCampus.pdf présente le projet, pas les conditions officielles. Prérequis, durées et modalités doivent être confirmés par l’établissement avant publication.</div>
      <div className="layout">
        <aside className="side" style={{ width: 280 }}>
          <b style={{ fontSize: 12 }}>Rechercher</b>
          <input className="sel" value={q} onChange={(e) => setQ(e.target.value)} placeholder="Nom ou référence du programme…" aria-label="Rechercher un programme" />
          <div className="rowg" style={{ gap: 8 }}>
            <select className="sel" value={inst} onChange={(e) => setInst(e.target.value)}>{["IIT & ISB", "IIT", "ISB"].map((o) => <option key={o}>{o}</option>)}</select>
            <span className="sel">Statut ⌄</span>
          </div>
          <div className="panel" style={{ padding: 0, gap: 0, background: "#f5f9fe" }}>
            <p className="small" style={{ padding: "10px 14px", fontSize: 11.5 }}>{vis.length} programmes · Données indicatives</p>
            {vis.map((p) => (
              <button key={p.id} onClick={() => setSel(p.id)} style={{ textAlign: "left", background: p.id === sel ? "var(--panel)" : "#fff", border: 0, borderTop: "1px solid var(--line)", padding: 14, display: "flex", flexDirection: "column", gap: 8 }}>
                <span className="chip2 hl" style={{ alignSelf: "flex-start", fontSize: 11 }}>{p.inst} · {p.type}</span>
                <b style={{ fontSize: 14, color: "var(--ink2)" }}>{p.name}</b>
                <span className="chip2" style={{ alignSelf: "flex-start", fontSize: 11, ...TONE[p.status] }}>{p.status}</span>
                <small style={{ fontSize: 11, color: "var(--muted3)" }}>Révision du 07 juillet 2026</small>
              </button>
            ))}
          </div>
          <p className="small" style={{ fontSize: 11 }}>Les intitulés et débouchés sont indicatifs. Aucune condition d’admission ni tarification réelle n’est publiée ici.</p>
          <div className="panel" style={{ gap: 8 }}><h2 style={{ fontSize: 15 }}>Circuit de validation</h2>{["Compléter la fiche interne", "Faire vérifier les sources", "Obtenir la validation académique", "Autoriser la publication humaine"].map((s, i) => <span key={s} style={{ fontSize: 12.5, color: "var(--ink2)", fontWeight: i === 3 ? 700 : 400 }}>{i + 1}. {s}</span>)}</div>
        </aside>

        <div className="panel main" style={{ gap: 12 }}>
          <div className="rowb"><h2 style={{ fontSize: 18 }}>{cur.name}</h2><small className="small" style={{ fontSize: 11 }}>{cur.ref}</small></div>
          <div><span className="chip2" style={TONE[cur.status]}>{cur.status}</span></div>
          <label className="fld">Intitulé du programme<input value={cur.name} onChange={(e) => set("name", e.target.value)} /></label>
          <div className="grid g2" style={{ gap: 14 }}>
            <label className="fld">Établissement<select value={cur.inst} onChange={(e) => set("inst", e.target.value)}><option>IIT</option><option>ISB</option></select></label>
            <label className="fld">Type<select value={cur.type} onChange={(e) => set("type", e.target.value)}><option>Licence</option><option>Prépa</option><option>Ingénierie</option></select></label>
          </div>
          <label className="fld">Présentation indicative<textarea rows={3} value={cur.intro} onChange={(e) => set("intro", e.target.value)} /></label>
          <div className="grid g2" style={{ gap: 14 }}>
            <label className="fld">Durée officielle<input value={cur.duree} onChange={(e) => set("duree", e.target.value)} /></label>
            <label className="fld">Statut éditorial<select value={cur.status} onChange={(e) => set("status", e.target.value)}>{(["À vérifier", "Brouillon", "En validation", "Publié"] as Status[]).map((s) => <option key={s} disabled={s === "Publié"}>{s}</option>)}</select></label>
          </div>
          <label className="fld">Prérequis et conditions d’accès<textarea rows={2} value={cur.pre} onChange={(e) => set("pre", e.target.value)} /></label>
          <label className="fld">Débouchés indicatifs<textarea rows={2} value={cur.outs} onChange={(e) => set("outs", e.target.value)} /></label>
          <hr className="hr" />
          <b style={{ fontSize: 13, color: "var(--ink2)", fontWeight: 400 }}>Référence documentaire</b>
          <label className="fld">Document associé<select value={cur.doc} onChange={(e) => set("doc", e.target.value)}>{["Catalogue des parcours IIT.pdf", "Présentation des programmes ISB.pdf", "Guide de candidature – brouillon.pdf"].map((d) => <option key={d}>{d}</option>)}</select><span className="hint">Source de démonstration · Indexée le 07 juillet 2026. Le contenu et les passages à citer restent à vérifier ; indexation ≠ validation.</span></label>
          <label className="fld">Passage / référence officielle<input value={cur.passage} onChange={(e) => set("passage", e.target.value)} placeholder="Référence officielle à joindre par l’établissement" /></label>
          <div className="warnbox"><Icon name="shield" size={14} color="#8d6417" />Conditions et frais : non documentés. Ne pas déduire de critères d’accès, de montants ni de passerelle garantie à partir du PDF du projet.</div>
          <label className={`cbx ${verified ? "on" : ""}`} style={{ fontSize: 12.5 }}><input type="checkbox" checked={verified} onChange={() => setVerified(!verified)} /><i>{verified && <Icon name="check" size={12} color="#fff" />}</i>J’ai vérifié cette fiche avec une source officielle de l’établissement.</label>
          <div className="rowg" style={{ gap: 10 }}>
            <button className="b" onClick={() => setMsg("Brouillon enregistré (démonstration).")}>Enregistrer le brouillon <Icon name="save" size={14} /></button>
            <button className="b gold" disabled={!verified} onClick={() => { set("status", "En validation"); setMsg("Fiche soumise à validation académique."); }}>Soumettre à validation</button>
          </div>
          <div><button className="b" disabled>Publier le programme <Icon name="lock" size={14} /></button></div>
          <p className="small" style={{ fontSize: 11 }}>{msg || "Publication bloquée jusqu’à la validation humaine. Aucun changement enregistré dans la démonstration."}</p>
        </div>
      </div>
    </AdminShell>
  );
}
