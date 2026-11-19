import { useMemo, useState } from "react";
import AdminShell from "../../components/AdminShell";
import Icon from "../../components/Icon";

interface Ev { id: string; when: string; title: string; actor: string; status: "À contrôler" | "À prendre en charge" | "Consigné" | "Échec OCR" | "À relire"; kind: "Échecs" | "Relais humains" | "Droits" | "Autre"; ref: string; action: string; doc: string; scope: string; detail: string; tech?: boolean }
const EVS: Ev[] = [
  { id: "EVT-DEMO-0708-0912", when: "08 juil. · 10:06 · UTC+1", title: "Rappel candidat préparé", actor: "Agent Suivi · SC-2026-0426", status: "À contrôler", kind: "Autre", ref: "Entretien du 9 juillet · E-mail + espace", action: "Préparation d’un rappel", doc: "Modèle Rappel entretien J−1", scope: "IIT", detail: "Le rappel est prêt et n’a pas été envoyé. Relire le contenu avant activation." },
  { id: "EVT-DEMO-0708-0845", when: "08 juil. · 09:45 · UTC+1", title: "Escalade vers un conseiller", actor: "Agent Orientation · SC-2026-0435", status: "À prendre en charge", kind: "Relais humains", ref: "Demande explicite du candidat · IIT", action: "Relais humain ouvert", doc: "—", scope: "IIT", detail: "Le candidat souhaite parler à un conseiller. Aucun conseiller n’est encore attribué." },
  { id: "EVT-DEMO-0708-0915", when: "08 juil. · 09:15 · UTC+1", title: "Pièce complémentaire demandée", actor: "Amira Mansour · SC-2026-0426", status: "Consigné", kind: "Autre", ref: "Relevé de notes · Espace candidat", action: "Demande de pièce", doc: "Relevé de notes", scope: "IIT", detail: "Demande consignée et visible dans l’espace du candidat." },
  { id: "EVT-DEMO-0707-0941", when: "07 juil. · 09:41 · UTC+1", title: "Échec d’ingestion RAG · OCR", actor: "Service d’ingestion · IIT / ISB", status: "Échec OCR", kind: "Échecs", ref: "Questions fréquentes – scan.pdf", action: "Extraction du texte par OCR", doc: "Questions fréquentes – scan.pdf", scope: "IIT / ISB", detail: "Le texte du scan n’a pas pu être lisible. L’extraction n’a pas produit de contenu exploitable ; la source n’est pas indexée pour les réponses.", tech: true },
  { id: "EVT-DEMO-0707-0930", when: "07 juil. · 09:30 · UTC+1", title: "Modification de droits", actor: "Amira Mansour · Sami Gharbi", status: "Consigné", kind: "Droits", ref: "Rôle Entretiens · Périmètre IIT", action: "Changement de rôle", doc: "—", scope: "IIT", detail: "Amira Mansour, 07 juillet 2026, 09:30. Sami Gharbi, rôle Entretiens, périmètre limité à IIT." },
  { id: "EVT-DEMO-0707-0924", when: "07 juil. · 09:24 · UTC+1", title: "Bilan QCM disponible", actor: "Agent Admission · SC-2026-0426", status: "À relire", kind: "Autre", ref: "12 réponses · Relecture conseiller", action: "Génération du bilan", doc: "QCM Informatique v0.3", scope: "IIT", detail: "Le bilan est disponible pour relecture. Il ne constitue pas une décision." },
];
const FILTERS = ["Tous", "Échecs", "Relais humains", "Droits"] as const;
const TONE = (s: Ev["status"]): React.CSSProperties => (s === "Consigné" ? { background: "var(--panel)", color: "var(--blue2)" } : s === "À relire" ? { background: "var(--panel)", color: "var(--blue2)" } : { background: "#fff4de", color: "#8d6417" });

export default function Journal() {
  const [sel, setSel] = useState(EVS[3]!.id);
  const [filter, setFilter] = useState<(typeof FILTERS)[number]>("Tous");
  const [q, setQ] = useState("");
  const [assignee, setAssignee] = useState("");
  const [msg, setMsg] = useState("");
  const [retried, setRetried] = useState(false);
  const counts = (k: string) => EVS.filter((e) => e.kind === k).length;
  const list = useMemo(() => EVS.filter((e) => (filter === "Tous" || e.kind === filter) && `${e.title} ${e.actor} ${e.ref}`.toLowerCase().includes(q.toLowerCase())), [filter, q]);
  const cur = EVS.find((e) => e.id === sel) ?? EVS[0]!;

  return (
    <AdminShell title="Chaque action garde une trace" sub="Événements et relais IIT / ISB · Heure de Tunis (UTC+1) · Données de démonstration"
      action={<button className="b" onClick={() => window.print()}>Exporter la sélection <Icon name="download" size={13} /></button>}>
      <div className="grid g3" style={{ gap: 14 }}>
        <div className="stat"><span className="l">Relais humains ouverts</span><span className="v">18</span><small className="small" style={{ fontSize: 12 }}>12 orientation · 4 admission · 2 suivi</small></div>
        <div className="stat"><span className="l">Ingestion à reprendre</span><span className="v">{retried ? 0 : 1}</span><small className="small" style={{ fontSize: 12 }}>Source exclue des réponses</small></div>
        <div className="stat"><span className="l">Rappels à contrôler</span><span className="v">2</span><small className="small" style={{ fontSize: 12 }}>Aucun envoi depuis cet écran</small></div>
      </div>

      <div className="rowg" style={{ gap: 10, flexWrap: "nowrap" }}>
        <label className="search" style={{ height: 38 }}><Icon name="search" size={15} color="var(--muted3)" /><input value={q} onChange={(e) => setQ(e.target.value)} placeholder="Rechercher un dossier, acteur ou document…" aria-label="Rechercher dans le journal" /></label>
        <span className="sel">7–8 juillet 2026 ⌄</span><span className="sel">IIT & ISB ⌄</span>
      </div>
      <div className="tabs2">{FILTERS.map((f) => <button key={f} className={filter === f ? "on" : ""} style={{ border: 0, background: "none", color: filter === f ? "var(--blue2)" : "var(--muted3)", fontWeight: filter === f ? 600 : 400 }} onClick={() => setFilter(f)}>{f === "Tous" ? `Tous · ${EVS.length}` : f === "Échecs" ? `Échecs · ${counts("Échecs")}` : f}</button>)}<span className="sel" style={{ padding: "6px 10px" }}>Tous les acteurs ⌄</span></div>

      <div className="layout">
        <div className="main" style={{ gap: 14 }}>
          <div className="panel" style={{ padding: 0, gap: 0 }}>
            <div className="rowb" style={{ padding: "10px 16px", fontSize: 11.5, color: "var(--muted3)", borderBottom: "1px solid var(--line)" }}><span>Horodatage, action et acteur</span><span>Statut</span></div>
            {list.map((e) => (
              <button key={e.id} onClick={() => setSel(e.id)} style={{ textAlign: "left", background: e.id === sel ? "var(--panel)" : "#fff", border: 0, borderBottom: "1px solid #eef3f8", padding: "14px 16px", display: "flex", justifyContent: "space-between", gap: 10 }}>
                <span className="kvx" style={{ gap: 4 }}><small style={{ fontSize: 11 }}>{e.when}</small><b style={{ fontSize: 14 }}>{e.title}</b><small>{e.actor}</small><small>{e.ref}</small></span>
                <span className="chip2" style={{ alignSelf: "flex-start", fontSize: 11, ...TONE(e.status) }}>{e.status}</span>
              </button>
            ))}
            {list.length === 0 && <p className="p-muted" style={{ padding: 16 }}>Aucun événement.</p>}
            <div className="rowb" style={{ padding: "10px 16px", fontSize: 11.5, color: "var(--muted3)" }}><span>{list.length} événements · Page 1 sur 1</span><span>‹ 1 ›</span></div>
          </div>
          <div className="panel" style={{ gap: 10 }}>
            <h2 style={{ fontSize: 15 }}>Relais humains prioritaires</h2>
            <div className="rowg" style={{ gap: 8 }}><Icon name="users" size={15} color="var(--blue2)" /><b style={{ fontSize: 13 }}>SC-2026-0435 · Nour Ayadi</b></div>
            <small className="small" style={{ fontSize: 12 }}>Souhaite parler à un conseiller · Orientation IIT</small>
            <div><span className="chip2" style={{ background: "#fff4de", color: "#8d6417", fontSize: 11 }}>Non attribué · À prendre en charge</span></div>
            <label className="fld" style={{ fontSize: 12 }}>Attribuer à<select className="sel" value={assignee} onChange={(e) => setAssignee(e.target.value)}><option value="">Choisir un conseiller habilité…</option><option>Amira Mansour</option><option>Sami Gharbi</option><option>Inès Jaziri</option></select></label>
            <div><button className="b" style={{ fontSize: 12.5 }} disabled={!assignee} onClick={() => setMsg(`Prise en charge préparée pour ${assignee} (démonstration, aucune attribution effectuée).`)}>Préparer la prise en charge <Icon name="users" size={13} /></button></div>
            <small className="small" style={{ fontSize: 11 }}>Aucune attribution effectuée dans la démonstration.</small>
          </div>
        </div>

        <aside className="side" style={{ width: 420, gap: 14 }}>
          <div className="panel" style={{ gap: 12 }}>
            <h2 style={{ fontSize: 17 }}>{cur.title}</h2>
            <div><span className="chip2" style={{ fontSize: 11, ...TONE(cur.status) }}>{cur.tech ? (retried ? "Échec · Reprise lancée" : "Échec · Reprise non lancée") : cur.status}</span></div>
            <div className="kvx"><small style={{ fontSize: 11 }}>ÉVÉNEMENT</small><b style={{ fontSize: 13 }}>{cur.id}</b></div>
            <div className="kvx"><small style={{ fontSize: 11 }}>ACTEUR</small><b style={{ fontSize: 13 }}>{cur.actor.split(" · ")[0]}</b></div>
            <div className="kvx"><small style={{ fontSize: 11 }}>HORODATAGE</small><b style={{ fontSize: 13 }}>{cur.when.replace(" · ", " 2026 · ").replace("juil.", "juillet")}</b></div>
            <div className="kvx"><small style={{ fontSize: 11 }}>ACTION</small><b style={{ fontSize: 13 }}>{cur.action}</b></div>
            <div className="grid g2" style={{ gap: 10 }}><div className="kvx"><small style={{ fontSize: 11 }}>DOCUMENT</small><b style={{ fontSize: 13 }}>{cur.doc}</b></div><div className="kvx"><small style={{ fontSize: 11 }}>STATUT</small><b style={{ fontSize: 13 }}>{cur.tech && retried ? "Reprise lancée" : cur.status}</b></div></div>
            <div className="kvx"><small style={{ fontSize: 11 }}>PÉRIMÈTRE</small><b style={{ fontSize: 13 }}>{cur.scope}</b></div>
            <p className="p-body" style={{ fontSize: 12.5, color: "var(--ink2)", lineHeight: 1.5 }}>{cur.detail}</p>
            {cur.tech && <>
              <div className="warnbox"><Icon name="shield" size={14} color="#8d6417" />Cette source reste exclue du RAG jusqu’à une reprise technique réussie, puis une vérification humaine du contenu.</div>
              <b style={{ fontSize: 12.5 }}>Actions de reprise disponibles</b>
              <button className="b dark" style={{ alignSelf: "flex-start", fontSize: 12.5, background: "var(--blue2)", borderColor: "var(--blue2)" }} onClick={() => { setRetried(true); setMsg("Relance OCR préparée (démonstration)."); }}>Préparer une relance OCR <Icon name="refresh" size={13} color="#fff" /></button>
              <button className="b" style={{ alignSelf: "flex-start", fontSize: 12.5 }} onClick={() => setMsg("Import d’un PDF lisible : prototype de démonstration.")}>Importer un PDF lisible <Icon name="upload" size={13} /></button>
              <button className="b" style={{ alignSelf: "flex-start", fontSize: 12.5 }} onClick={() => setMsg("Rapport technique : indisponible dans la démonstration.")}>Consulter le rapport technique <Icon name="file" size={13} /></button>
              <small className="small" style={{ fontSize: 11 }}>Aucune relance ni importation effectuée. Des actions ouvrent une préparation ; elles ne simulent pas une réussite.</small>
            </>}
          </div>
          <div className="panel" style={{ gap: 8 }}>
            <h2 style={{ fontSize: 15 }}>Contrôle des changements de droits</h2>
            <p className="p-muted" style={{ fontSize: 12.5 }}>Amira Mansour · 07 juillet 2026, 09:30. Sami Gharbi : rôle Entretiens, périmètre limité à IIT.</p>
            <p className="small" style={{ fontSize: 11.5 }}>Action consignée dans les données de démonstration. Consultation des dossiers assignés, sans permission d’admission officielle.</p>
            <div><button className="b" style={{ fontSize: 12.5 }} onClick={() => { setFilter("Droits"); setSel(EVS[4]!.id); }}>Consulter le changement <Icon name="clipboard" size={13} /></button></div>
          </div>
        </aside>
      </div>
      {msg && <p className="okbox" role="status">{msg}</p>}
      <div className="notice" style={{ borderRadius: 8 }}><Icon name="shield" size={15} color="var(--blue2)" /><span style={{ fontSize: 12.5, color: "var(--ink2)" }}>Les traces facilitent le contrôle et le relais humain. Elles ne constituent pas une décision d’admission. Les données sensibles et secrets sont masqués.</span></div>
    </AdminShell>
  );
}
