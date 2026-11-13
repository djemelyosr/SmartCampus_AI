import { useState, type FormEvent } from "react";
import { Link, useNavigate } from "react-router-dom";
import AuthShell from "../components/AuthShell";
import { api, ApiError } from "../lib/api";
import { useAuth } from "../lib/auth";
import check from "../assets/check.svg";
import shield from "../assets/shield-check.svg";
import arrowRight from "../assets/arrow-right.svg";
import messageCircle from "../assets/message-circle.svg";
import gitCompare from "../assets/git-compare.svg";
import users from "../assets/users-w.svg";

export default function Register() {
  const { login } = useAuth();
  const nav = useNavigate();
  const [f, setF] = useState({ first: "", last: "", email: "", pw: "", pw2: "" });
  const [showPw, setShowPw] = useState(false);
  const [terms, setTerms] = useState(false);
  const [news, setNews] = useState(false);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const set = (k: keyof typeof f) => (e: { target: { value: string } }) => setF({ ...f, [k]: e.target.value });

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setError("");
    if (f.pw.length < 12) return setError("Le mot de passe doit contenir au moins 12 caractères.");
    if (f.pw !== f.pw2) return setError("Les deux mots de passe ne sont pas identiques.");
    if (!terms) return setError("Veuillez accepter les conditions d’utilisation.");
    setBusy(true);
    try {
      await api.register(f.email, f.pw, `${f.first} ${f.last}`.trim());
      await login(f.email, f.pw);
      nav("/espace");
    } catch (err) {
      setError(err instanceof ApiError && err.status === 409 ? "Cette adresse e-mail est déjà utilisée." : "Création impossible, vérifiez vos informations.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <AuthShell
      eyebrow="UN PREMIER PAS, SANS ENGAGEMENT"
      title={["Votre projet mérite", "un espace à lui."]}
      lead="Créez votre compte pour retrouver vos échanges, enregistrer vos pistes et avancer à votre rythme vers IIT ou ISB."
      cardTitle="Mon avenir, mon choix"
      items={[
        { icon: messageCircle, t: "Retrouver vos échanges", d: "Un historique pour construire votre projet progressivement." },
        { icon: gitCompare, t: "Garder vos pistes", d: "Comparez les parcours avant de faire votre choix." },
        { icon: users, t: "Être accompagné", d: "Une équipe humaine peut prendre le relais à tout moment." },
      ]}
      cardFoot={<>L’IA vous accompagne. Vous gardez le choix.<br />Aucune décision d’admission automatique.</>}
      below={
        <>
          <div className="rowg" style={{ gap: 12 }}>
            {["Français", "Tounsi", "Arabizi", "Texte & audio"].map((l, i) => <span key={l} className={`chip2 ${i === 0 ? "hl" : ""}`} style={{ fontSize: 11 }}>{l}</span>)}
          </div>
          <p className="small" style={{ fontSize: 11, color: "var(--muted3)" }}>Les informations sur les formations sont illustratives, à confirmer auprès de l’établissement.</p>
        </>
      }
      formWidth={620}
    >
      <form className="fcardx" onSubmit={onSubmit}>
        <h2>Créer mon compte candidat</h2>
        <p className="sub">Après l’exploration libre, conservez vos échanges et préparez votre candidature. Champs * requis. Les comptes de l’équipe (responsables, entretien, direction) sont créés par un administrateur.</p>
        <div className="grid g2" style={{ gap: 16 }}>
          <label className="fld">Prénom *<input value={f.first} onChange={set("first")} required autoComplete="given-name" /></label>
          <label className="fld">Nom *<input value={f.last} onChange={set("last")} required autoComplete="family-name" /></label>
        </div>
        <label className="fld">Adresse e-mail *
          <input type="email" value={f.email} onChange={set("email")} required autoComplete="email" />
          <span className="tiny">Vous recevrez un lien pour vérifier votre adresse.</span>
        </label>
        <label className="fld">Mot de passe *
          <span className="pw"><input type={showPw ? "text" : "password"} value={f.pw} onChange={set("pw")} required minLength={12} autoComplete="new-password" /><button type="button" onClick={() => setShowPw(!showPw)}>{showPw ? "Masquer" : "Afficher"}</button></span>
          <span className="tiny">Au moins 12 caractères ; choisissez un mot de passe unique.</span>
        </label>
        <label className="fld">Confirmer le mot de passe *
          <span className="pw"><input type={showPw ? "text" : "password"} value={f.pw2} onChange={set("pw2")} required autoComplete="new-password" /></span>
        </label>
        <hr />
        <b style={{ fontSize: 12, color: "var(--ink2)" }}>Votre consentement</b>
        <label className={`cbx ${terms ? "on" : ""}`} style={{ fontSize: 12, alignItems: "flex-start" }}>
          <input type="checkbox" checked={terms} onChange={() => setTerms(!terms)} /><i>{terms && <img src={check} alt="" />}</i>
          <span>J’accepte les conditions d’utilisation et le traitement de mes données pour créer et gérer mon compte. *</span>
        </label>
        <a className="lnk" style={{ fontSize: 12 }} href="#confidentialite">Lire les conditions et la politique de confidentialité ↗</a>
        <label className={`cbx ${news ? "on" : ""}`} style={{ fontSize: 12, alignItems: "flex-start" }}>
          <input type="checkbox" checked={news} onChange={() => setNews(!news)} /><i>{news && <img src={check} alt="" />}</i>
          <span>Je souhaite recevoir les actualités et invitations IIT / ISB. Facultatif, modifiable à tout moment.</span>
        </label>
        <div className="infobox"><img src={shield} alt="" /><span>La création du compte ne vaut pas pré-inscription. Vous choisirez séparément de transmettre votre candidature, avec votre consentement.</span></div>
        {error && <p className="errbox" role="alert">{error}</p>}
        <button className="bt" disabled={busy}>Créer mon compte <img src={arrowRight} alt="" /></button>
        <hr />
        <div className="rowb" style={{ fontSize: 13 }}>
          <span style={{ color: "var(--muted3)" }}>Vous avez déjà un compte ?</span>
          <Link to="/connexion" style={{ color: "var(--link)", fontWeight: 600 }}>Me connecter →</Link>
        </div>
      </form>
      <p className="tiny" style={{ fontSize: 11, color: "var(--muted3)", margin: 0 }}>
        Vos données sont accessibles uniquement aux équipes habilitées pour vous accompagner. Vous pouvez demander leur accès, leur rectification ou leur suppression.
      </p>
    </AuthShell>
  );
}
