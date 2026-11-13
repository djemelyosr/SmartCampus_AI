import { useEffect, useState, type ReactNode } from "react";
import { Link } from "react-router-dom";
import { initials } from "../../components/CandidateLayout";
import { api } from "../../lib/api";
import { useAuth } from "../../lib/auth";
import shield from "../../assets/p-shield.svg";
import plus from "../../assets/p-plus.svg";
import checkW from "../../assets/p-check-w.svg";
import checkB from "../../assets/p-check-b.svg";
import back from "../../assets/p-back.svg";

interface Form {
  school_level: string; bac: string; lycee: string; moyenne: string;
  interests: string[]; career_goal: string; learning: string;
  mobilite: string; budget: string; notes: string;
  first: string; last: string; phone: string; city: string; birth: string;
  consent: boolean; news: boolean; lang: string; audio: boolean; transcript: boolean;
}

const LEVELS = ["Seconde", "Première", "Terminale", "Bac obtenu", "Études supérieures"];
const BACS = ["Mathématiques", "Sciences expérimentales", "Informatique", "Économie et gestion", "Lettres", "Technique"];
const MOB = ["Sfax en priorité", "Tunisie, sans préférence", "Prêt(e) à déménager", "À discuter"];
const BUDGET = ["À discuter avec un conseiller", "Budget limité", "Budget confortable"];

function Field({ label, children, full }: { label: string; children: ReactNode; full?: boolean }) {
  return <label className="fld" style={{ fontSize: 13.5, color: "var(--navy)", gridColumn: full ? "1 / -1" : undefined }}>{label}{children}</label>;
}
function Sel({ value, options, onChange }: { value: string; options: string[]; onChange: (v: string) => void }) {
  return (
    <select value={value} onChange={(e) => onChange(e.target.value)} style={{ borderRadius: 12, minHeight: 46, fontSize: 14, borderColor: "var(--line)", color: "var(--navy)" }}>
      {!options.includes(value) && <option>{value}</option>}
      {options.map((o) => <option key={o}>{o}</option>)}
    </select>
  );
}

export default function ProfilEdit() {
  const { user } = useAuth();
  const [parts0, parts1] = (() => {
    const p = (user?.full_name ?? "").split(/\s+/);
    return [p[0] ?? "", p.slice(1).join(" ")];
  })();
  const initial: Form = {
    school_level: "Terminale", bac: "Mathématiques", lycee: "Lycée Hédi Chaker · Sfax", moyenne: "15,20 / 20",
    interests: ["Mathématiques", "Informatique"], career_goal: "Devenir ingénieur logiciel",
    learning: "Créer des projets concrets, avec une progression pratique et progressive.",
    mobilite: "Sfax en priorité", budget: "À discuter avec un conseiller",
    notes: "Je préfère rester à Sfax. J’aimerais connaître les frais avant de confirmer mon choix.",
    first: parts0, last: parts1, phone: "", city: "Sfax", birth: "",
    consent: false, news: false, lang: "Français", audio: false, transcript: true,
  };
  const [f, setF] = useState<Form>(initial);
  const [saved, setSaved] = useState<Form>(initial);
  const [newInterest, setNewInterest] = useState("");
  const [adding, setAdding] = useState(false);
  const [msg, setMsg] = useState("");
  const dirty = JSON.stringify(f) !== JSON.stringify(saved);
  const set = <K extends keyof Form>(k: K, v: Form[K]) => setF((s) => ({ ...s, [k]: v }));
  const ti = (k: keyof Form) => ({ value: f[k] as string, onChange: (e: { target: { value: string } }) => set(k, e.target.value as never) });

  useEffect(() => {
    api.getProfile().then((p) => {
      const c = (p.constraints ?? {}) as Record<string, string>;
      const next: Form = {
        ...initial,
        school_level: p.school_level ?? initial.school_level,
        interests: p.favorite_subjects?.length ? p.favorite_subjects : initial.interests,
        career_goal: p.career_goal ?? initial.career_goal,
        phone: p.phone ?? "",
        consent: p.consent_given,
        bac: c.bac ?? initial.bac, lycee: c.lycee ?? initial.lycee, moyenne: c.moyenne ?? initial.moyenne,
        learning: c.learning ?? initial.learning, mobilite: c.mobilite ?? initial.mobilite,
        budget: c.budget ?? initial.budget, notes: c.notes ?? initial.notes,
        city: c.city ?? initial.city, birth: c.birth ?? "", news: c.news === "1",
      };
      setF(next); setSaved(next);
    }).catch(() => { /* offline / demo: keep defaults */ });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const filled = [f.school_level, f.bac, f.lycee, f.career_goal, f.learning, f.mobilite, f.notes, f.phone, f.city, f.birth].filter(Boolean).length + (f.interests.length ? 1 : 0);
  const pct = Math.round((filled / 11) * 100);

  async function save() {
    setMsg("");
    try {
      await api.saveProfile({
        phone: f.phone || null, school_level: f.school_level, favorite_subjects: f.interests,
        interests: f.interests, career_goal: f.career_goal, consent_given: f.consent,
        constraints: { bac: f.bac, lycee: f.lycee, moyenne: f.moyenne, learning: f.learning, mobilite: f.mobilite, budget: f.budget, notes: f.notes, city: f.city, birth: f.birth, news: f.news ? "1" : "0" },
      });
      setSaved(f);
      setMsg("Profil enregistré.");
    } catch {
      setMsg("Enregistrement impossible : le serveur est injoignable ou la session a expiré.");
    }
  }

  const addInterest = () => {
    const v = newInterest.trim();
    if (v && !f.interests.includes(v)) set("interests", [...f.interests, v]);
    setNewInterest(""); setAdding(false);
  };
  const Cb = ({ on, onClick, children }: { on: boolean; onClick: () => void; children: ReactNode }) => (
    <label className={`cbx ${on ? "on" : ""}`} style={{ alignItems: "flex-start", fontSize: 13.5, color: "var(--navy)" }}>
      <input type="checkbox" checked={on} onChange={onClick} />
      <i style={on ? { background: "var(--navy)", borderColor: "var(--navy)" } : undefined}>{on && <img src={checkW} alt="" />}</i>{children}
    </label>
  );
  const Sw = ({ on, onClick }: { on: boolean; onClick: () => void }) => (
    <button type="button" role="switch" aria-checked={on} onClick={onClick}
      style={{ width: 34, height: 20, borderRadius: 20, border: 0, padding: 3, display: "flex", justifyContent: on ? "flex-end" : "flex-start", background: on ? "var(--link)" : "var(--line)", flex: "none" }}>
      <span style={{ width: 14, height: 14, borderRadius: 14, background: "#fff" }} />
    </button>
  );

  return (
    <div className="ws" style={{ gap: 22 }}>
      <div className="rowb">
        <div>
          <h1 style={{ margin: 0, fontSize: 28, fontWeight: 600, letterSpacing: -0.8, color: "var(--navy)" }}>Votre profil, avec vos mots</h1>
          <p className="p-muted" style={{ margin: "6px 0 0", fontSize: 14, color: "var(--muted2)" }}>Consultez et corrigez les informations partagées avec votre guide. Vous gardez la main.</p>
        </div>
        {dirty && <span className="chip2 amber">Modifications non enregistrées</span>}
      </div>
      <div className="notice" style={{ background: "#f5f8fc" }}><img src={shield} alt="" /><span>Prérempli à partir de nos échanges. Vos modifications enrichissent l’orientation, sans modifier automatiquement une pré-inscription déjà envoyée.</span></div>

      <div className="detail">
        <div className="l" style={{ gap: 18 }}>
          <div className="panel">
            <h2 style={{ color: "var(--navy)" }}>Votre parcours académique</h2>
            <div className="grid g2" style={{ gap: 16 }}>
              <Field label="Niveau actuel *"><Sel value={f.school_level} options={LEVELS} onChange={(v) => set("school_level", v)} /></Field>
              <Field label="Section du baccalauréat *"><Sel value={f.bac} options={BACS} onChange={(v) => set("bac", v)} /></Field>
              <Field label="Lycée"><input {...ti("lycee")} /></Field>
              <Field label="Moyenne annuelle déclarée"><input {...ti("moyenne")} /></Field>
            </div>
            <p className="small" style={{ color: "var(--muted2)", fontSize: 12.5 }}>Résultat déclaré, non vérifié. Le relevé pourra être demandé par le service admissions.</p>
          </div>

          <div className="panel">
            <h2 style={{ color: "var(--navy)" }}>Vos intérêts et votre projet</h2>
            <b style={{ fontSize: 13.5, color: "var(--navy)" }}>Matières préférées et centres d’intérêt</b>
            <div className="rowg" style={{ gap: 8 }}>
              {f.interests.map((i) => (
                <button key={i} type="button" className="chip2 line" style={{ background: "#f5f8fc", color: "var(--navy)", border: "1px solid var(--line)" }} onClick={() => set("interests", f.interests.filter((x) => x !== i))}>{i} ×</button>
              ))}
              {adding ? (
                <input autoFocus value={newInterest} onChange={(e) => setNewInterest(e.target.value)} onBlur={addInterest} onKeyDown={(e) => e.key === "Enter" && (e.preventDefault(), addInterest())} placeholder="Nouvel intérêt" style={{ border: "1px solid var(--line)", borderRadius: 12, padding: "10px 12px", font: "inherit", fontSize: 14 }} />
              ) : (
                <button type="button" className="b" style={{ color: "var(--navy)" }} onClick={() => setAdding(true)}>Ajouter un intérêt <img src={plus} alt="" /></button>
              )}
            </div>
            <Field label="Objectif professionnel"><input {...ti("career_goal")} /></Field>
            <Field label="Votre façon d’apprendre"><textarea rows={3} {...ti("learning")} style={{ borderRadius: 12 }} /></Field>
          </div>

          <div className="panel">
            <h2 style={{ color: "var(--navy)" }}>Vos contraintes et vos possibilités</h2>
            <div className="grid g2" style={{ gap: 16 }}>
              <Field label="Mobilité envisagée"><Sel value={f.mobilite} options={MOB} onChange={(v) => set("mobilite", v)} /></Field>
              <Field label="Budget à prévoir"><Sel value={f.budget} options={BUDGET} onChange={(v) => set("budget", v)} /></Field>
            </div>
            <Field label="Ce que l’équipe devrait savoir"><textarea rows={3} {...ti("notes")} style={{ borderRadius: 12 }} /></Field>
            <p className="small" style={{ color: "var(--muted2)", fontSize: 12.5 }}>Ces réponses aident à préparer l’échange. Elles ne constituent pas des conditions d’accès.</p>
          </div>

          <div className="panel">
            <h2 style={{ color: "var(--navy)" }}>Vos coordonnées</h2>
            <div className="grid g2" style={{ gap: 16 }}>
              <Field label="Prénom *"><input {...ti("first")} /></Field>
              <Field label="Nom *"><input {...ti("last")} /></Field>
              <Field label="Adresse e-mail *"><input value={user?.email ?? ""} readOnly style={{ background: "#f5f8fc" }} /></Field>
              <Field label="Téléphone"><input {...ti("phone")} placeholder="+216 …" /></Field>
              <Field label="Ville de résidence"><input {...ti("city")} /></Field>
              <Field label="Date de naissance"><input type="date" {...ti("birth")} /></Field>
            </div>
          </div>

          <div className="panel">
            <h2 style={{ color: "var(--navy)" }}>Vos choix, vos données</h2>
            <Cb on={f.consent} onClick={() => set("consent", !f.consent)}>J’accepte le traitement de mes informations pour l’orientation et le suivi de ma candidature par les équipes IIT / ISB. *</Cb>
            <Cb on={f.news} onClick={() => set("news", !f.news)}>Je souhaite recevoir les actualités et invitations des établissements. (Facultatif)</Cb>
            <p className="small" style={{ color: "var(--muted2)", fontSize: 12.5 }}>Politique de confidentialité · Demander la rectification ou la suppression de mes données.</p>
          </div>

          {msg && <p className={msg.includes("impossible") ? "errbox" : "okbox"} role="status">{msg}</p>}
          <div className="rowb">
            <button className="b" style={{ color: "var(--navy)" }} onClick={() => { setF(saved); setMsg(""); }} disabled={!dirty}>Annuler les modifications</button>
            <button className="b dark" onClick={save} disabled={!dirty || !f.consent}>Enregistrer mon profil <img src={checkB} alt="" /></button>
          </div>
        </div>

        <div className="r" style={{ gap: 18 }}>
          <div className="panel">
            <h2 style={{ color: "var(--navy)" }}>{f.first} {f.last}</h2>
            <div className="rowg" style={{ gap: 12, flexWrap: "nowrap" }}>
              <div className="avatar">{initials(`${f.first} ${f.last}`)}</div>
              <div className="kv" style={{ gap: 4 }}><b>Mon profil candidat</b><small>{f.school_level} · {f.city}</small></div>
            </div>
            <div className="rowb"><span style={{ fontSize: 13.5, color: "var(--ink2)" }}>Profil enrichi</span><span className="chip2 line" style={{ background: "#f5f8fc", color: "var(--navy)" }}>{pct} % · Aperçu</span></div>
            <div className="prog"><i style={{ width: `${pct}%` }} /></div>
            <p className="small" style={{ color: "var(--muted2)", fontSize: 12.5 }}>{dirty ? "Vos modifications viennent d’être saisies. Enregistrez pour mettre votre profil à jour." : "Votre profil est à jour."}</p>
          </div>

          <div className="panel">
            <h2 style={{ color: "var(--navy)" }}>Langue et audio</h2>
            <Field label="Langue de conversation"><Sel value={f.lang} options={["Français", "Tounsi", "Arabizi"]} onChange={(v) => set("lang", v)} /></Field>
            <p className="small" style={{ color: "var(--muted2)", fontSize: 12.5 }}>Également disponibles : Tounsi et Arabizi.</p>
            <hr className="hr" />
            <div className="rowb" style={{ flexWrap: "nowrap" }}><div className="kv" style={{ gap: 3 }}><b style={{ fontSize: 13.5 }}>Réponses audio</b><small style={{ fontSize: 12.5 }}>Lecture à votre demande</small></div><Sw on={f.audio} onClick={() => set("audio", !f.audio)} /></div>
            <div className="rowb" style={{ flexWrap: "nowrap" }}><div className="kv" style={{ gap: 3 }}><b style={{ fontSize: 13.5 }}>Transcription visible</b><small style={{ fontSize: 12.5 }}>Relire le contenu des messages audio</small></div><Sw on={f.transcript} onClick={() => set("transcript", !f.transcript)} /></div>
            <div className="notice" style={{ background: "#f5f8fc" }}><img src={shield} alt="" /><span>Le microphone n’est activé qu’à votre demande. Aucun enregistrement en continu.</span></div>
          </div>

          <div className="panel" style={{ background: "#f5f8fc", borderRadius: 16 }}>
            <h2 style={{ color: "var(--navy)" }}>Ce profil vous appartient</h2>
            <p className="p-body" style={{ fontSize: 14 }}>Vous pouvez corriger les informations issues de vos échanges à tout moment.</p>
            <p className="p-body">L’IA propose des pistes. Un conseiller étudie votre dossier et confirme avec vous les informations à vérifier.</p>
            <div><Link className="b" to="/comparaison" style={{ color: "var(--navy)" }}>Revenir à mon orientation <img src={back} alt="" /></Link></div>
          </div>
          <p className="small" style={{ color: "var(--muted2)", fontSize: 12.5 }}>Champs marqués * : nécessaires au suivi du profil.<br />Les préférences de communication se règlent dans <Link to="/espace/notifications" style={{ color: "var(--link)" }}>Notifications</Link>.</p>
        </div>
      </div>
    </div>
  );
}
