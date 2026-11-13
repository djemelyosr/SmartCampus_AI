import { useState } from "react";
import AdminShell from "../../components/AdminShell";
import Icon from "../../components/Icon";

const Tog = ({ on, onClick, label }: { on: boolean; onClick: () => void; label: string }) => <button type="button" role="switch" aria-checked={on} aria-label={label} className={`tog ${on ? "on" : ""}`} onClick={onClick}><i /></button>;
const STAGES: [string, string, boolean][] = [["1 →", "Orientation", false], ["2 →", "Pré-inscription", false], ["3 →", "QCM", false], ["4 →", "Entretien", false], ["5 · HUMAINE", "Décision humaine", true]];
const STAGE_SUB = ["Conseiller sur proposer", "Consentement reçu", "Repère pédagogique", "Compte rendu relu", "Personne habilitée"];
const MODELS = ["QCM", "E-mail de confirmation", "E-mail de rappel", "Notification"] as const;

function Sel({ label, value, options, onChange }: { label: string; value: string; options: string[]; onChange: (v: string) => void }) {
  return <label className="fld" style={{ fontSize: 12 }}>{label}<select className="sel" value={value} onChange={(e) => onChange(e.target.value)}>{options.map((o) => <option key={o}>{o}</option>)}</select></label>;
}

export default function Campagnes() {
  const [f, setF] = useState({ etab: "IIT et ISB", open: "01 juin 2026", close: "30 septembre 2026", r1: "Après 48 heures sans nouvelle pièce", r2: "5 jours après la première · 2 maximum", rdv: "24 heures avant · Heure de Tunis", esc: "Après 7 jours ou demande du candidat", qcm: "Informatique · v0.3 · 12 questions", conf: "Confirmation entretien · FR · v1.2", rappel: "Rappel entretien J−1 · FR · v1.1", notif: "Votre entretien a lieu demain · v1.0", subject: "Votre entretien SmartCampus a lieu demain" });
  const [auto, setAuto] = useState({ reception: true, qcm: true, espace: true });
  const [model, setModel] = useState<(typeof MODELS)[number]>("E-mail de rappel");
  const [active, setActive] = useState(true);
  const [msg, setMsg] = useState("");
  const set = (k: keyof typeof f) => (v: string) => setF({ ...f, [k]: v });
  const AUTO: [keyof typeof auto, string, string][] = [["reception", "Confirmations de réception", "Après dépôt et consentement explicite"], ["qcm", "Invitation QCM et rappels", "Modèles relus et autorisés par l’équipe"], ["espace", "Notifications dans l’espace candidat", "Sans exposer de document confidentiel"]];

  return (
    <AdminShell title="Un parcours fluide, une décision humaine" sub="Campagne 2026-2027 · Règles, modèles et relances · Configuration de démonstration"
      action={<button className="b dark" style={{ background: "var(--blue2)", borderColor: "var(--blue2)" }} onClick={() => setMsg("Brouillon enregistré (démonstration).")}>Enregistrer le brouillon <Icon name="save" size={14} color="#fff" /></button>}>
      <div className="panel" style={{ gap: 12 }}>
        <h2 style={{ fontSize: 17 }}>Campagne 2026-2027</h2>
        <div className="rowg" style={{ gap: 8 }}><span className="chip2 hl line" style={{ fontSize: 11 }}>Configuration · Brouillon</span><span className="small" style={{ fontSize: 11 }}>IIT & ISB · Rentrée septembre 2026</span></div>
        <div className="grid g3" style={{ gap: 14 }}>
          <Sel label="Établissements" value={f.etab} options={["IIT et ISB", "IIT", "ISB"]} onChange={set("etab")} />
          <label className="fld" style={{ fontSize: 12 }}>Ouverture indicative<input className="sel" value={f.open} onChange={(e) => set("open")(e.target.value)} /></label>
          <label className="fld" style={{ fontSize: 12 }}>Clôture indicative<input className="sel" value={f.close} onChange={(e) => set("close")(e.target.value)} /></label>
        </div>
        <p className="small" style={{ fontSize: 11 }}>Dates fictives : paramétrage, à faire confirmer par les établissements.</p>
        <div className="grid" style={{ gridTemplateColumns: "repeat(5, minmax(0, 1fr))", gap: 8 }}>
          {STAGES.map(([n, t, h], i) => <div key={t} className="prev" style={{ borderRadius: 6, padding: 12, gap: 4, background: h ? "#f6e7b8" : "#f5f8fc", borderColor: h ? "#ecd48a" : "var(--line)" }}><small style={{ fontSize: 11, color: h ? "#8d6417" : "var(--link)", fontWeight: 600 }}>{n}</small><b style={{ fontSize: 12.5 }}>{t}</b><span style={{ fontSize: 11 }}>{STAGE_SUB[i]}</span></div>)}
        </div>
      </div>

      <div className="layout" id="regles">
        <div className="panel" style={{ flex: "1 1 460px", gap: 12 }}>
          <h2 style={{ fontSize: 17 }}>Relances et escalade</h2>
          <Sel label="Dossier incomplet · Première relance" value={f.r1} options={["Après 48 heures sans nouvelle pièce", "Après 24 heures sans nouvelle pièce", "Après 72 heures sans nouvelle pièce"]} onChange={set("r1")} />
          <Sel label="Deuxième relance" value={f.r2} options={["5 jours après la première · 2 maximum", "3 jours après la première · 2 maximum", "7 jours après la première · 1 maximum"]} onChange={set("r2")} />
          <Sel label="Rendez-vous · Rappel" value={f.rdv} options={["24 heures avant · Heure de Tunis", "48 heures avant · Heure de Tunis", "2 heures avant · Heure de Tunis"]} onChange={set("rdv")} />
          <Sel label="Escalade vers un conseiller" value={f.esc} options={["Après 7 jours ou demande du candidat", "Après 3 jours ou demande du candidat", "Sur demande du candidat uniquement"]} onChange={set("esc")} />
          <p className="small" style={{ fontSize: 11 }}>Relais vers le service admissions d’établissement choisi. Relances suspendues dès qu’un conseiller prend en charge le dossier.</p>
        </div>
        <div className="panel" style={{ flex: "1 1 400px", gap: 12 }}>
          <h2 style={{ fontSize: 17 }}>Périmètre d’automatisation</h2>
          {AUTO.map(([k, t, d]) => <div className="rowb" key={k} style={{ flexWrap: "nowrap" }}><div className="kvx"><b style={{ fontSize: 13 }}>{t}</b><small>{d}</small></div><Tog on={auto[k]} onClick={() => setAuto({ ...auto, [k]: !auto[k] })} label={t} /></div>)}
          <div className="notice" style={{ borderRadius: 8 }}><Icon name="shield" size={15} color="var(--blue2)" /><span style={{ fontSize: 12.5, color: "var(--ink2)" }}>Décision officielle obligatoirement humaine. Aucune admission, aucun refus ni avis académique définitif ne peut être envoyé par un agent IA.</span></div>
          <div><span className="chip2 hl line" style={{ fontSize: 11 }}>Garde-fou verrouillé</span></div>
        </div>
      </div>

      <div className="panel" style={{ gap: 12 }} id="emails">
        <h2 style={{ fontSize: 17 }}>Modèles du parcours</h2>
        <div className="tabs2" id="qcm">{MODELS.map((m) => <button key={m} className={model === m ? "on" : ""} onClick={() => setModel(m)}>{m}</button>)}</div>
        <div className="layout">
          <div className="col" style={{ flex: "1 1 380px", gap: 12 }}>
            <Sel label="Modèle QCM associé" value={f.qcm} options={["Informatique · v0.3 · 12 questions", "Gestion · v0.2 · 10 questions"]} onChange={set("qcm")} />
            <small className="small" style={{ fontSize: 11 }}>Logique 5 · Mathématiques 4 · Culture numérique 3. Personnalisation ciblée, sans seuil d’admission.</small>
            <Sel label="Confirmation de rendez-vous" value={f.conf} options={["Confirmation entretien · FR · v1.2", "Confirmation entretien · AR · v1.0"]} onChange={set("conf")} />
            <Sel label="E-mail de rappel sélectionné" value={f.rappel} options={["Rappel entretien J−1 · FR · v1.1", "Rappel entretien H−2 · FR · v1.0"]} onChange={set("rappel")} />
            <Sel label="Notification associée" value={f.notif} options={["Votre entretien a lieu demain · v1.0", "Votre rendez-vous est confirmé · v1.0"]} onChange={set("notif")} />
            <label className="fld" style={{ fontSize: 12 }}>Objet du rappel<input className="sel" value={f.subject} onChange={(e) => set("subject")(e.target.value)} /></label>
            <label className={`cbx ${active ? "on" : ""}`} style={{ fontSize: 12.5 }}><input type="checkbox" checked={active} onChange={() => setActive(!active)} /><i>{active && <Icon name="check" size={12} color="#fff" />}</i>Activer l’e-mail et la notification pour ce rappel</label>
            <div><button className="b" style={{ fontSize: 12.5 }} onClick={() => setMsg("Édition des modèles : prototype de démonstration.")}>Modifier les modèles <Icon name="file" size={13} /></button></div>
          </div>
          <div className="panel" style={{ flex: "1 1 420px", background: "#f5f9fe", gap: 10 }}>
            <div className="rowg" style={{ gap: 8 }}><span className="chip2 hl line" style={{ fontSize: 11 }}>Aperçu · Aucun envoi réel</span></div>
            <small className="small" style={{ fontSize: 11 }}>À : kchaoufatma765@gmail.com</small>
            <b style={{ fontSize: 15, color: "var(--ink2)" }}>{f.subject}</b>
            <div className="p-body" style={{ fontSize: 12.5, lineHeight: 1.55, color: "var(--ink2)" }}>Bonjour Fatma,<br /><br />Votre entretien d’orientation est confirmé le jeudi 9 juillet 2026, de 10:00 à 10:30, heure de Tunis (UTC+1), avec Amira Mansour, service admissions IIT.<br /><br />Retrouvez le lien de visioconférence dans votre espace. Si votre relevé de notes n’est pas encore disponible, vous pouvez le signaler au conseiller.</div>
            <div><span className="b dark" style={{ fontSize: 12.5, borderRadius: 6, background: "var(--blue2)", borderColor: "var(--blue2)" }}>Consulter mon rendez-vous</span></div>
            <small className="small" style={{ fontSize: 10.5 }}>Cet échange prépare la suite de votre projet. Il ne vaut pas décision d’admission.</small>
            <hr className="hr" />
            <b style={{ fontSize: 12 }}>Notification dans l’espace candidat</b>
            <span style={{ fontSize: 12.5, color: "var(--ink2)" }}>Votre entretien a lieu demain · Jeudi 9 juillet à 10:00 avec Amira Mansour.</span>
          </div>
        </div>
        <div className="rowb"><small className="small" style={{ fontSize: 11 }}>{msg || "Version v0.4 · À relire par l’équipe avant activation. Aucun enregistrement ni envoi effectué dans la démo."}</small><div className="rowg" style={{ gap: 8 }}><button className="b" style={{ fontSize: 12.5 }} onClick={() => setMsg("Soumis à validation (démonstration).")}>Soumettre à validation</button><button className="b" style={{ fontSize: 12.5 }} disabled>Activer</button></div></div>
      </div>
    </AdminShell>
  );
}
