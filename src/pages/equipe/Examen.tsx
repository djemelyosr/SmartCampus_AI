import { useMemo, useState } from "react";
import { Link } from "react-router-dom";
import Icon from "../../components/Icon";
import { useAuth } from "../../lib/auth";

interface Cand { id: string; ini: string; name: string; prog: string; status: string; tone: "ok" | "warn" | "" ; level: string; avg: string; project: string; ref: string; city: string; created: string }
const CANDS: Cand[] = [
  { id: "fk", ini: "FK", name: "Fatma Kchaou", prog: "IIT · Licence informatique", status: "Entretien confirmé", tone: "ok", level: "Bac mathématiques", avg: "15,20 / 20 · non vérifié", project: "Ingénierie logicielle", ref: "SC-2026-0426", city: "Sfax", created: "06 juil. 2026" },
  { id: "mk", ini: "MK", name: "Mariem Kammoun", prog: "ISB · Gestion", status: "À examiner", tone: "", level: "Bac économie et gestion", avg: "14,10 / 20 · non vérifié", project: "Management", ref: "SC-2026-0431", city: "Tunis", created: "06 juil. 2026" },
  { id: "at", ini: "AT", name: "Aziz Trabelsi", prog: "IIT · Préparatoire", status: "QCM terminé", tone: "", level: "Bac sciences", avg: "13,80 / 20 · non vérifié", project: "Ingénierie", ref: "SC-2026-0419", city: "Sousse", created: "05 juil. 2026" },
  { id: "sa", ini: "SA", name: "Sarra Ayadi", prog: "IIT · Ingénierie", status: "Pièce manquante", tone: "warn", level: "Bac technique", avg: "—", project: "Systèmes embarqués", ref: "SC-2026-0422", city: "Sfax", created: "05 juil. 2026" },
  { id: "nb", ini: "NB", name: "Nour Ben Ali", prog: "ISB · Gestion", status: "À examiner", tone: "", level: "Bac économie", avg: "12,90 / 20 · non vérifié", project: "Finance", ref: "SC-2026-0435", city: "Gabès", created: "04 juil. 2026" },
  { id: "hf", ini: "HF", name: "Hedi Feki", prog: "IIT · Licence informatique", status: "QCM en cours", tone: "", level: "Bac informatique", avg: "16,00 / 20 · non vérifié", project: "Data", ref: "SC-2026-0440", city: "Monastir", created: "04 juil. 2026" },
];

export default function Examen() {
  const { user } = useAuth();
  const canInterview = user?.role === "interviewer" || user?.role === "admin"; // academic heads only review files
  const [sel, setSel] = useState("fk");
  const [q, setQ] = useState("");
  const [tab, setTab] = useState("Synthèse du dossier");
  const [note, setNote] = useState("");
  const [validated, setValidated] = useState<Record<string, boolean>>({});
  const list = useMemo(() => CANDS.filter((c) => c.name.toLowerCase().includes(q.toLowerCase())), [q]);
  const c = CANDS.find((x) => x.id === sel) ?? CANDS[0]!;
  const toGo = CANDS.filter((x) => !validated[x.id]).length;

  return (
    <div className="ws" style={{ gap: 18 }}>
      <div className="rowb">
        <div>
          <h1 style={{ margin: 0, fontSize: 28, fontWeight: 600, letterSpacing: -0.8, color: "var(--navy)" }}>Des données au dialogue</h1>
          <p className="p-muted" style={{ margin: "6px 0 0", fontSize: 14, color: "var(--muted3)" }}>Étudiez le dossier, préparez l’entretien et gardez la main sur l’orientation.</p>
        </div>
        <button className="b" onClick={() => window.print()}>Exporter les dossiers <Icon name="ur" size={14} /></button>
      </div>

      <div className="layout">
        <aside className="side" style={{ width: 232 }}>
          <label className="search" style={{ height: 40 }}><Icon name="search" size={15} color="var(--muted3)" /><input value={q} onChange={(e) => setQ(e.target.value)} placeholder="Rechercher un candidat" aria-label="Rechercher un candidat" /></label>
          <div className="rowg" style={{ gap: 6 }}><span className="chip2 hl line">À traiter · {toGo}</span><span className="chip2 line">IIT + ISB ⌄</span></div>
          {list.map((x) => (
            <button key={x.id} className={`cand ${x.id === sel ? "on" : ""}`} onClick={() => setSel(x.id)}>
              <span className="ini">{x.ini}</span>
              <span><b>{x.name}</b><small>{x.prog}</small><span className={`chip2 ${x.tone === "ok" ? "hl" : x.tone === "warn" ? "warn" : ""}`} style={{ fontSize: 11, padding: "3px 8px", ...(x.tone === "warn" ? { background: "#fff4de", color: "#8d6417" } : x.tone ? {} : { background: "#eef4f9" }) }}>{validated[x.id] ? "Orientation validée" : x.status}</span></span>
            </button>
          ))}
          <p className="small" style={{ fontSize: 11.5 }}>{list.length} de 24 dossiers · Trier par activité récente</p>
        </aside>

        <div className="main" style={{ gap: 14 }}>
          <div className="panel" style={{ gap: 12 }}>
            <div className="rowb">
              <div><h2 style={{ fontSize: 20, color: "var(--navy)" }}>{c.name}</h2><span className="small" style={{ fontSize: 12 }}>{c.ref} · {c.city} · Créé le {c.created}</span></div>
              <span className="chip2 warn" style={{ background: validated[c.id] ? "#e3f4ea" : "#fff4de", color: validated[c.id] ? "#1b6b3a" : "#8d6417" }}>{validated[c.id] ? "Orientation validée" : "Validation humaine en attente"}</span>
            </div>
            <div className="tabs2" role="tablist">{["Synthèse du dossier", "Conversation", "Documents (1)", "Historique"].map((t) => <button key={t} role="tab" aria-selected={tab === t} className={tab === t ? "on" : ""} style={{ border: 0, background: "none", padding: "4px 8px" }} onClick={() => setTab(t)}>{t}</button>)}</div>
            {tab === "Synthèse du dossier" ? (
              <div className="grid g3" style={{ gap: 12 }}>
                <div className="kvx"><small>Niveau déclaré</small><b>{c.level}</b></div>
                <div className="kvx"><small>Moyenne déclarée</small><b>{c.avg}</b></div>
                <div className="kvx"><small>Projet</small><b>{c.project}</b></div>
              </div>
            ) : <p className="p-muted" style={{ fontSize: 13 }}>{tab === "Conversation" ? "Résumé des échanges avec l’agent disponible dans « Préparer l’entretien »." : tab === "Historique" ? "06 juil. · Préinscription reçue · 07 juil. · QCM terminé · 08 juil. · Relevé demandé." : "document_candidat.pdf · à vérifier par l’équipe."}</p>}
          </div>

          <div className="grid g2" style={{ gap: 14, alignItems: "stretch" }}>
            <div className="panel" style={{ gap: 12 }}>
              <h2>Orientation proposée par l’IA</h2>
              <div><span className="chip2 hl">Préférence candidat · Licence IIT</span></div>
              <p className="p-body" style={{ color: "var(--ink2)", fontSize: 13 }}>Goût des maths et du code, objectif logiciel, préférence pour des projets concrets : la Licence paraît cohérente avec une progression pratique.</p>
              <p className="small" style={{ fontSize: 12 }}>Alternative discutée : Prépa IIT. Gestion ISB explorée, moins proche du projet déclaré.</p>
              <div><span className="chip2 hl">Documentation IIT · à vérifier</span></div>
              <p className="small" style={{ fontSize: 11.5 }}>Suggestion non décisionnelle · Sources à contrôler.</p>
            </div>
            <div className="panel" style={{ gap: 10 }}>
              <div className="rowb"><h2>QCM · Terminé le 07 juillet</h2></div>
              <div className="rowb"><b style={{ fontSize: 28, color: "var(--ink2)" }}>9 / 12</b><span className="chip2 hl">Repère pédagogique</span></div>
              {[["Logique", 4, 5], ["Mathématiques", 3, 4], ["Culture numérique", 2, 3]].map(([n, g, t]) => (
                <div key={n as string} className="col" style={{ gap: 6 }}><div className="rowb" style={{ fontSize: 12.5 }}><span>{n}</span><span>{g} / {t}</span></div><div className="hbar"><i style={{ width: `${((g as number) / (t as number)) * 100}%` }} /></div></div>
              ))}
              <p className="small" style={{ fontSize: 11.5 }}>Score illustratif · Ne vaut pas admission.</p>
            </div>
          </div>

          <div className="panel" style={{ gap: 12 }}>
            <h2>Préparer l’entretien du 09 juillet · 10:00</h2>
            <div className="grid g2" style={{ gap: 14 }}>
              <div className="kvx"><b style={{ fontSize: 12.5 }}>Synthèse des échanges</b><span style={{ fontSize: 12.5, color: "var(--muted3)" }}>Hésite entre Prépa et Licence. Souhaite créer des logiciels et apprendre progressivement.</span></div>
              <div className="kvx"><b style={{ fontSize: 12.5 }}>Points à approfondir</b><span style={{ fontSize: 12.5, color: "var(--muted3)" }}>Confirmer la mobilité et le budget, explorer un projet personnel, vérifier le relevé de notes.</span></div>
            </div>
            <div className="rowg" style={{ gap: 10 }}>
              {canInterview && <Link className="b" style={{ fontSize: 12.5, borderRadius: 8 }} to="/equipe/entretien">Ouvrir le rendez-vous</Link>}
              <button className="b" style={{ fontSize: 12.5, borderRadius: 8 }} onClick={() => setNote("Demande de relevé de notes envoyée au candidat (démonstration).")}>Demander une pièce</button>
              {canInterview && <Link className="b" style={{ fontSize: 12.5, borderRadius: 8 }} to="/equipe/entretien">Saisir le compte rendu</Link>}
            </div>
          </div>

          <div className="panel tint" style={{ borderRadius: 12, gap: 10 }}>
            <h2 style={{ fontSize: 14 }}><Icon name="shield" size={14} /> Votre appréciation pédagogique</h2>
            <input className="sel" style={{ width: "100%" }} value={note} onChange={(e) => setNote(e.target.value)} placeholder="Ajouter un avis motivé avant validation ou ajustement…" aria-label="Appréciation pédagogique" />
            <div className="rowb">
              <span className="small" style={{ fontSize: 11.5 }}>Valider l’orientation ne confirme pas l’admission.</span>
              <div className="rowg" style={{ gap: 10 }}>
                <button className="b" style={{ fontSize: 12.5, borderRadius: 8 }} onClick={() => setNote((n) => n || "Proposition à ajuster : ")}>Ajuster la proposition</button>
                <button className="b dark" style={{ fontSize: 12.5, borderRadius: 8 }} onClick={() => setValidated({ ...validated, [c.id]: true })}>Valider l’orientation <Icon name="check" size={13} color="#fff" /></button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
