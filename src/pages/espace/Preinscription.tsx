import { useEffect, useState, type ReactNode } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import Journey from "../../components/Journey";
import { api, ApiError } from "../../lib/api";
import { useAuth } from "../../lib/auth";
import { FORMATIONS } from "../../lib/catalog";
import { loadCandidature, saveCandidature } from "../../lib/candidature";
import sparkle from "../../assets/sparkle-s.svg";
import check from "../../assets/check.svg";
import arrowRight from "../../assets/arrow-right.svg";

const LEVELS = ["Seconde", "Première", "Terminale", "Bac obtenu", "Études supérieures"];
const BACS = ["Mathématiques", "Sciences expérimentales", "Informatique", "Économie et gestion", "Lettres", "Technique"];

const Field = ({ label, children }: { label: string; children: ReactNode }) => (
  <label className="fld" style={{ fontSize: 13.5, color: "var(--ink2)" }}>{label}{children}</label>
);

export default function Preinscription() {
  const { user } = useAuth();
  const nav = useNavigate();
  const [params] = useSearchParams();
  const formationId = params.get("formation") ?? loadCandidature().formation;
  const f = FORMATIONS.find((x) => x.id === formationId) ?? FORMATIONS[0]!;
  const parts = (user?.full_name ?? "").split(/\s+/);
  const [v, setV] = useState({
    first: parts[0] ?? "", last: parts.slice(1).join(" "), phone: "", city: "", birth: "",
    level: "Terminale", bac: "Mathématiques", lycee: "", moyenne: "",
  });
  const [consent, setConsent] = useState(false);
  const [news, setNews] = useState(false);
  const [msg, setMsg] = useState("");
  const [busy, setBusy] = useState(false);
  const set = (k: keyof typeof v) => (e: { target: { value: string } }) => setV((s) => ({ ...s, [k]: e.target.value }));

  useEffect(() => {
    saveCandidature({ formation: f.id });
    api.getProfile().then((p) => {
      const c = (p.constraints ?? {}) as Record<string, string>;
      setV((s) => ({ ...s, phone: p.phone ?? s.phone, level: p.school_level ?? s.level, bac: c.bac ?? s.bac, lycee: c.lycee ?? s.lycee, moyenne: c.moyenne ?? s.moyenne, city: c.city ?? s.city, birth: c.birth ?? s.birth }));
      setConsent(p.consent_given);
    }).catch(() => { /* no backend: keep empty form */ });
  }, [f.id]);

  async function send() {
    setMsg("");
    if (!consent) return setMsg("Le consentement est nécessaire pour envoyer votre pré-inscription.");
    if (!v.first || !v.last || !v.phone || !v.city || !v.birth) return setMsg("Complétez les champs marqués *.");
    setBusy(true);
    let remote = false;
    let failure = "";
    try {
      await api.saveProfile({ phone: v.phone, school_level: v.level, favorite_subjects: [], interests: [], career_goal: null, consent_given: true, constraints: { bac: v.bac, lycee: v.lycee, moyenne: v.moyenne, city: v.city, birth: v.birth, news: news ? "1" : "0" } });
      await api.createPreinscription(Number(f.id));
      remote = true;
    } catch (e) { failure = e instanceof ApiError ? e.message : "Le serveur est injoignable."; }
    setBusy(false);
    if (!remote) {
      return setMsg(failure || "Cette formation est introuvable dans le catalogue du serveur : elle n’a pas été envoyée.");
    }
    saveCandidature({ formation: f.id, preinscription: { sentAt: new Date().toISOString(), ref: "SC-2026-0426" } });
    nav("/espace/qcm");
  }

  return (
    <div className="ws" style={{ gap: 22 }}>
      <div>
        <h1 style={{ margin: 0, fontSize: 28, fontWeight: 600, letterSpacing: -0.8, color: "var(--navy)" }}>Une première étape vers votre projet</h1>
        <p className="p-muted" style={{ margin: "6px 0 0", fontSize: 14, color: "var(--muted3)" }}>Vérifiez vos informations avant d’envoyer votre pré-inscription. Votre choix n’est pas une admission.</p>
      </div>
      <Journey current={3} chevrons />

      <div className="detail">
        <div className="l" style={{ gap: 18 }}>
          <div className="panel">
            <h2>Vos informations personnelles</h2>
            <div className="notice" style={{ padding: 11, borderRadius: 8 }}><img src={sparkle} alt="" style={{ width: 16, height: 16 }} /><span style={{ fontSize: 12.5, color: "var(--ink2)" }}>Prérempli à partir de nos échanges. Vous pouvez tout modifier.</span></div>
            <div className="grid g2" style={{ gap: 16 }}>
              <Field label="Prénom *"><input value={v.first} onChange={set("first")} /></Field>
              <Field label="Nom *"><input value={v.last} onChange={set("last")} /></Field>
              <Field label="Adresse e-mail *"><input value={user?.email ?? ""} readOnly style={{ background: "#f5f8fc" }} /></Field>
              <Field label="Téléphone *"><input value={v.phone} onChange={set("phone")} placeholder="+216 …" /></Field>
              <Field label="Ville de résidence *"><input value={v.city} onChange={set("city")} /></Field>
              <Field label="Date de naissance *"><input type="date" value={v.birth} onChange={set("birth")} /></Field>
            </div>
          </div>
          <div className="panel">
            <h2>Votre parcours académique</h2>
            <div className="grid g2" style={{ gap: 16 }}>
              <Field label="Niveau actuel *"><select value={v.level} onChange={set("level")}>{LEVELS.map((o) => <option key={o}>{o}</option>)}</select></Field>
              <Field label="Section du baccalauréat *"><select value={v.bac} onChange={set("bac")}>{BACS.map((o) => <option key={o}>{o}</option>)}</select></Field>
              <Field label="Lycée"><input value={v.lycee} onChange={set("lycee")} /></Field>
              <Field label="Moyenne annuelle déclarée"><input value={v.moyenne} onChange={set("moyenne")} placeholder="15,20 / 20" /></Field>
            </div>
            <p className="small" style={{ color: "var(--muted3)", fontSize: 12.5 }}>Résultat déclaré par le candidat, non vérifié. Le relevé pourra être demandé par le service admissions.</p>
          </div>
          <div className="panel">
            <h2>Vos choix, vos données</h2>
            <label className={`cbx ${consent ? "on" : ""}`} style={{ alignItems: "flex-start" }}>
              <input type="checkbox" checked={consent} onChange={() => setConsent(!consent)} /><i>{consent && <img src={check} alt="" />}</i>
              <span>J’accepte le traitement de mes informations pour l’orientation et le suivi de ma candidature par les équipes IIT / ISB. *</span>
            </label>
            <label className={`cbx ${news ? "on" : ""}`} style={{ alignItems: "flex-start" }}>
              <input type="checkbox" checked={news} onChange={() => setNews(!news)} /><i>{news && <img src={check} alt="" />}</i>
              <span>Je souhaite recevoir les actualités et invitations des établissements. (Facultatif)</span>
            </label>
            <p className="small" style={{ color: "var(--muted3)", fontSize: 12.5 }}>Consulter la politique de confidentialité · Demander la rectification ou la suppression de mes données.</p>
          </div>
          {msg && <p className="errbox" role="alert">{msg}</p>}
          <div className="rowb">
            <button className="b" onClick={() => { saveCandidature({ formation: f.id }); setMsg("Brouillon enregistré."); }}>Enregistrer le brouillon</button>
            <button className="b pri" style={{ borderRadius: 9 }} onClick={send} disabled={busy}>Envoyer ma pré-inscription <img src={arrowRight} alt="" /></button>
          </div>
        </div>

        <div className="r" style={{ gap: 18 }}>
          <div className="panel tint" style={{ borderColor: "var(--line2)" }}>
            <h2>Votre parcours retenu</h2>
            <div><span className="chip2 hl">{f.institution} · Votre préférence</span></div>
            <p style={{ fontSize: 23, fontWeight: 600, color: "var(--ink2)", lineHeight: 1.45 }}>{f.name}</p>
            <p className="p-body" style={{ fontSize: 14, color: "var(--ink2)" }}>Un chemin pratique et progressif, en lien avec votre projet d’ingénierie logicielle.</p>
            <hr className="hr" />
            <b style={{ fontSize: 13.5, color: "var(--ink2)" }}>Rentrée visée</b>
            <p className="p-body" style={{ fontSize: 14, color: "var(--ink2)" }}>Septembre 2026 · Campagne démo</p>
            <div><Link className="b" to="/comparaison" style={{ borderRadius: 9 }}>Modifier mon choix</Link></div>
          </div>
          <div className="panel">
            <h2>Et après l’envoi ?</h2>
            {[["Pré-inscription reçue", "Un e-mail vous confirme la réception."], ["QCM personnalisé", "Des questions pour mieux comprendre vos acquis."], ["Échange avec un conseiller", "Votre dossier et vos attentes seront étudiés ensemble."]].map(([t, d], i) => (
              <div className="rowg" key={t} style={{ alignItems: "flex-start", flexWrap: "nowrap", gap: 12 }}>
                <span className="avatar" style={{ width: 25, height: 25, fontSize: 12.5, background: "var(--panel)", border: 0 }}>{i + 1}</span>
                <div className="kv" style={{ gap: 4 }}><b style={{ color: "var(--ink2)" }}>{t}</b><small style={{ color: "var(--muted3)" }}>{d}</small></div>
              </div>
            ))}
            <hr className="hr" />
            <p className="small" style={{ color: "var(--muted3)", fontSize: 12.5 }}>Aucun paiement à cette étape. L’admission sera décidée par l’établissement après examen humain.</p>
          </div>
        </div>
      </div>
    </div>
  );
}
