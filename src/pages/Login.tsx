import { useState, type FormEvent } from "react";
import { Link, useNavigate } from "react-router-dom";
import AuthShell from "../components/AuthShell";
import { ApiError } from "../lib/api";
import { homeFor, useAuth } from "../lib/auth";
import check from "../assets/check.svg";
import arrowRight from "../assets/arrow-right.svg";
import arrowUpRight from "../assets/arrow-up-right.svg";
import shield from "../assets/shield-check.svg";
import userPlus from "../assets/user-plus.svg";
import compass from "../assets/auth-compass.svg";
import compare from "../assets/auth-compare.svg";
import calendar from "../assets/calendar.svg";

export default function Login() {
  const { login } = useAuth();
  const nav = useNavigate();
  const [team, setTeam] = useState(false);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPw, setShowPw] = useState(false);
  const [remember, setRemember] = useState(true);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError("");
    try {
      const u = await login(email, password);
      nav(homeFor(u.role));
    } catch (err) {
      setError(err instanceof ApiError ? "Adresse e-mail ou mot de passe incorrect." : "Le serveur est injoignable.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <AuthShell
      eyebrow="VOTRE AVENIR COMMENCE PAR UN ÉCHANGE"
      title={["Un espace pour construire", "votre prochain chapitre."]}
      lead="Explorez vos possibilités à IIT et ISB, clarifiez votre projet et avancez à votre rythme, avec une équipe à vos côtés."
      cardTitle="Mon avenir, mon choix"
      items={[
        { icon: compass, t: "Trouver votre voie", d: "Des pistes expliquées à partir de vos intérêts." },
        { icon: compare, t: "Comparer avant de choisir", d: "Licence, Prépa et Ingénierie : gardez vos options ouvertes." },
        { icon: calendar, t: "Échanger avec une personne", d: "Un conseiller prend le relais pour étudier votre projet." },
      ]}
      cardFoot={<>L’IA vous accompagne. Vous gardez le choix.<br />Aucune décision d’admission automatique.</>}
      below={
        <>
          <div className="rowg" style={{ gap: 12 }}>
            {["Français", "Tounsi", "Arabizi", "Texte & audio"].map((l, i) => <span key={l} className={`chip2 line ${i === 0 ? "hl" : ""}`} style={{ fontSize: 11 }}>{l}</span>)}
          </div>
          <p className="small" style={{ fontSize: 11, color: "var(--muted3)" }}>Les informations sur les formations sont illustratives, à confirmer auprès de l’établissement.</p>
        </>
      }
      formWidth={520}
    >
      <form className="fcardx" onSubmit={onSubmit}>
        <h2>Bienvenue sur SmartCampus</h2>
        <div className="seg2">
          <button type="button" className={!team ? "on" : ""} onClick={() => setTeam(false)}>Je suis candidat</button>
          <button type="button" className={team ? "on" : ""} onClick={() => setTeam(true)}>Je suis membre de l’équipe</button>
        </div>
        <p className="sub">
          {team ? "Utilisez le compte associé à votre invitation IIT / ISB." : "Retrouvez votre dossier avec un compte. Pour discuter avec le guide, aucun compte n’est nécessaire."}
        </p>
        <label className="fld">Adresse e-mail
          <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} required autoComplete="email" />
        </label>
        <label className="fld">Mot de passe
          <span className="pw"><input type={showPw ? "text" : "password"} value={password} onChange={(e) => setPassword(e.target.value)} required autoComplete="current-password" /><button type="button" onClick={() => setShowPw(!showPw)}>{showPw ? "Masquer" : "Afficher"}</button></span>
        </label>
        <div className="rowb">
          <label className={`cbx ${remember ? "on" : ""}`} style={{ fontSize: 12 }}>
            <input type="checkbox" checked={remember} onChange={() => setRemember(!remember)} /><i>{remember && <img src={check} alt="" />}</i>Rester connecté
          </label>
          <Link to="/recuperation" style={{ color: "var(--link)", fontSize: 12, fontWeight: 600 }}>Mot de passe oublié ?</Link>
        </div>
        {error && <p className="errbox" role="alert">{error}</p>}
        <button className="bt" disabled={busy}>Me connecter <img src={arrowRight} alt="" /></button>
        <hr />
        <b style={{ fontSize: 13, color: "var(--ink2)" }}>Vous souhaitez simplement découvrir ?</b>
        <p className="tiny" style={{ fontSize: 12 }}>Posez vos questions et comparez les formations sans vous inscrire. Le compte sert à sauvegarder et suivre votre candidature.</p>
        <Link className="bo" to="/formations">Continuer sans compte <img src={userPlus} alt="" /></Link>
        <p className="tiny"><Link to="/inscription" style={{ color: "var(--link)", fontWeight: 600 }}>Créer mon compte candidat →</Link></p>
      </form>

      <div className="fcardx">
        <div className="rowg" style={{ gap: 12, alignItems: "flex-start", flexWrap: "nowrap" }}>
          <img src={shield} alt="" width={23} height={23} />
          <div className="col" style={{ gap: 6 }}>
            <b style={{ fontSize: 13, color: "var(--ink2)" }}>Accès équipe IIT / ISB</b>
            <span className="tiny" style={{ fontSize: 12 }}>Pédagogie, entretiens, direction et administration : utilisez le compte associé à votre invitation.</span>
          </div>
        </div>
        <button type="button" className="bo" onClick={() => setTeam(true)}>Accéder à l’espace équipe <img src={arrowUpRight} alt="" /></button>
      </div>
      <p className="tiny" style={{ fontSize: 11, color: "var(--muted3)", margin: 0 }}>
        Confidentialité · Vos données servent à l’orientation et au suivi de votre candidature. Consulter la politique de confidentialité.
      </p>
    </AuthShell>
  );
}
