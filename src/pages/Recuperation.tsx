import { useEffect, useState, type FormEvent } from "react";
import { Link } from "react-router-dom";
import AuthShell from "../components/AuthShell";
import mailW from "../assets/mail-w.svg";
import mailB from "../assets/mail-b.svg";
import rotate from "../assets/rotate-cw.svg";
import shield from "../assets/shield-check.svg";
import messages from "../assets/messages-square.svg";

export default function Recuperation() {
  const [email, setEmail] = useState("");
  const [sent, setSent] = useState(false);
  const [wait, setWait] = useState(0);

  useEffect(() => {
    if (wait <= 0) return;
    const t = setTimeout(() => setWait(wait - 1), 1000);
    return () => clearTimeout(t);
  }, [wait]);

  function submit(e?: FormEvent) {
    e?.preventDefault();
    // Demo: the backend has no reset endpoint yet, so no e-mail is sent.
    setSent(true);
    setWait(60);
  }

  return (
    <AuthShell
      eyebrow="RETROUVEZ VOTRE ESPACE EN CONFIANCE"
      title={["Un oubli arrive.", "Votre parcours reste là."]}
      lead="Demandez un lien sécurisé pour définir un nouveau mot de passe et reprendre votre projet là où vous l’avez laissé."
      cardTitle="Quelques étapes, simplement"
      items={[
        { num: 1, t: "Indiquez votre e-mail", d: "Utilisez l’adresse associée à votre espace." },
        { num: 2, t: "Consultez votre messagerie", d: "Si un compte correspond, vous recevrez un lien." },
        { num: 3, t: "Choisissez un nouveau mot de passe", d: "Le lien est personnel et à usage unique." },
      ]}
      cardFoot="Ne partagez jamais votre lien ni votre mot de passe. Notre équipe ne vous les demandera pas."
      below={<p className="small" style={{ fontSize: 11, color: "var(--muted3)" }}>Votre candidature et vos documents ne sont pas modifiés par une demande de récupération.</p>}
      formWidth={620}
    >
      <form className="fcardx" onSubmit={submit}>
        <h2 style={{ color: "var(--navy)" }}>Mot de passe oublié ?</h2>
        <p className="sub">Saisissez votre adresse e-mail. La réponse sera identique, qu’un compte existe ou non.</p>
        <label className="fld">Adresse e-mail
          <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} required autoComplete="email" />
        </label>
        <button className="bt">Demander un lien de récupération <img src={mailW} alt="" /></button>
        <Link to="/connexion" style={{ color: "var(--link)", fontSize: 13, fontWeight: 600 }}>← Retour à la connexion</Link>
      </form>

      <div className="fcardx tint">
        <h2>Consultez votre messagerie</h2>
        <div className="rowg" style={{ gap: 10 }}>
          <img src={mailB} alt="" width={24} height={24} />
          <span className="chip2 hl line" style={{ fontSize: 11 }}>Aperçu de confirmation · Démo</span>
        </div>
        <p style={{ fontSize: 13, color: "var(--ink2)" }}>
          {sent && email ? `Si un compte est associé à ${email}, un e-mail contenant les instructions de récupération vous sera envoyé.` : "Si un compte est associé à cette adresse, un e-mail contenant les instructions de récupération vous sera envoyé."}
        </p>
        <p className="sub">Patientez quelques minutes et vérifiez vos courriers indésirables. Pour votre sécurité, nous ne confirmons pas l’existence d’un compte.</p>
        <hr />
        <b style={{ fontSize: 12, color: "var(--ink2)" }}>Vous n’avez rien reçu ?</b>
        <button type="button" className="bo" disabled={!sent || wait > 0} onClick={() => submit()}>Renvoyer le lien <img src={rotate} alt="" /></button>
        <p className="tiny">{wait > 0 ? `Renvoi disponible dans ${wait} s.` : "Renvoi disponible après 60 secondes."} Aucun e-mail n’est envoyé depuis cet aperçu.</p>
      </div>

      <div className="infobox"><img src={shield} alt="" /><span>Vous n’avez plus accès à cette adresse ? Contactez l’équipe pour une vérification humaine de votre identité.</span></div>
      <a className="bo" href="mailto:admissions@iit.example">Contacter l’assistance <img src={messages} alt="" /></a>
    </AuthShell>
  );
}
