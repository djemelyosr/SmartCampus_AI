import { useEffect, useState } from "react";
import { Link, Navigate } from "react-router-dom";
import Journey from "../../components/Journey";
import { api, ApiError, type QcmResults, type QcmView } from "../../lib/api";
import { useAuth } from "../../lib/auth";
import { FORMATIONS } from "../../lib/catalog";
import { loadCandidature } from "../../lib/candidature";
import { fmtDayLong, fmtTime } from "../../lib/dates";
import calendarDays from "../../assets/calendar-days.svg";
import lightbulb from "../../assets/lightbulb.svg";
import shield from "../../assets/shield-check.svg";
import upload from "../../assets/upload.svg";

export default function QcmResultats() {
  const { user } = useAuth();
  const f = FORMATIONS.find((x) => x.id === loadCandidature().formation) ?? FORMATIONS[0]!;
  const [view, setView] = useState<QcmView | null>(null);
  const [res, setRes] = useState<QcmResults | null>(null);
  const [err, setErr] = useState("");

  useEffect(() => {
    api.getQcm()
      .then(async (v) => { setView(v); if (v.finished) setRes(await api.qcmResults(v.id)); })
      .catch((e) => setErr(e instanceof ApiError ? e.message : "Le serveur est injoignable."));
  }, []);

  if (err) return <p className="ws errbox" role="alert">{err}</p>;
  if (!view) return <p className="ws small" role="status">Chargement des résultats…</p>;
  if (!view.finished) return <Navigate to="/espace/qcm" replace />;
  if (!res) return <p className="ws small" role="status">Calcul du bilan…</p>;

  const first = (user?.full_name ?? "").split(/\s+/)[0];
  const done = res.finished_at;
  const ex = view.questions.find((x) => x.code?.some((l) => l.includes("total"))) ?? view.questions[4];
  const exIdx = ex ? view.questions.indexOf(ex) : -1;
  const given = ex && view.answers[exIdx] !== undefined ? ex.options[view.answers[exIdx]!] : undefined;
  const exOk = given === "10";

  return (
    <div className="ws" style={{ gap: 22 }}>
      <div className="rowb">
        <div>
          <h1 style={{ margin: 0, fontSize: 28, fontWeight: 600, letterSpacing: -0.8, color: "var(--ink2)" }}>Vos acquis, un point de départ</h1>
          <p className="p-muted" style={{ margin: "6px 0 0", fontSize: 14, color: "var(--muted3)" }}>QCM personnalisé · {f.name}, {f.institution} · Dossier SC-2026-0426</p>
        </div>
        <button className="b" onClick={() => window.print()}>Télécharger mes résultats <img src={upload} alt="" style={{ transform: "rotate(180deg)" }} /></button>
      </div>
      <Journey current={4} chevrons />
      <div className="notice" style={{ padding: 22, gap: 16, alignItems: "center" }}>
        <span className="avatar" style={{ background: "var(--navy)", color: "#fff", width: 44, height: 44 }}>✓</span>
        <div style={{ flex: 1 }}>
          <b style={{ fontSize: 20, color: "var(--ink2)", fontWeight: 600 }}>Merci {first}, vos réponses sont enregistrées.</b>
          <div className="p-muted" style={{ fontSize: 14, color: "var(--muted3)" }}>{done ? `Terminé le ${fmtDayLong(done).toLowerCase()} à ${fmtTime(done)} · ` : ""}{Object.keys(view.answers).length} questions répondues · Résultats transmis au conseiller.</div>
        </div>
        <span className="chip2" style={{ background: "none", color: "var(--blue2)" }}>QCM terminé</span>
      </div>

      <div className="detail">
        <div className="l">
          <div className="panel">
            <h2>Votre bilan par thème</h2>
            <div className="rowg" style={{ gap: 24, alignItems: "flex-start", flexWrap: "nowrap" }}>
              <div className="kv" style={{ gap: 6, flex: "none" }}><b style={{ fontSize: 44, fontWeight: 600, color: "var(--ink2)", lineHeight: 1 }}>{res.good} / {res.total}</b><small style={{ fontSize: 12.5 }}>{res.pct} % de bonnes réponses</small></div>
              <div className="col" style={{ gap: 10, alignItems: "flex-start" }}><span className="chip2 hl">Repère pédagogique</span><span style={{ fontSize: 14, color: "var(--ink2)" }}>{res.summary}</span></div>
            </div>
            <hr className="hr" />
            {res.by_section.map((b) => (
              <div className="col" key={b.section} style={{ gap: 10 }}>
                <div className="rowb"><span style={{ fontSize: 14, color: "var(--ink2)" }}>{b.section}</span><b style={{ fontSize: 13.5, color: "var(--ink2)", fontWeight: 600 }}>{b.good} / {b.total} · {b.pct} %</b></div>
                <div className="prog" style={{ background: "#eef4f9" }}><i style={{ width: `${b.pct}%` }} /></div>
                <span className="small" style={{ fontSize: 13.5, color: "var(--muted3)" }}>{b.advice}</span>
              </div>
            ))}
            <hr className="hr" />
            <p className="small" style={{ color: "var(--muted3)", fontSize: 12.5 }}>Scores et feedback illustratifs · Aucun seuil officiel d’admission n’est présenté.</p>
          </div>

          {ex && (
            <div className="panel">
              <h2>Un exemple pour progresser</h2>
              <div className="rowb"><span className="chip2 hl">Question {exIdx + 1} · {ex.section}</span><span className={`chip2 ${exOk ? "hl" : "warn"}`}>{exOk ? "Réponse correcte" : "À revoir"}</span></div>
              <b style={{ fontSize: 14, color: "var(--ink2)", fontWeight: 600 }}>Que vaut « total » après une boucle de 1 à 4 ?</b>
              <p className="p-body" style={{ fontSize: 14, color: "var(--ink2)" }}>
                {given ? `Vous avez répondu ${given}. ` : ""}En additionnant successivement 1, 2, 3 et 4, la variable « total » passe par 1, 3, 6 puis 10.
              </p>
              <div className="notice" style={{ borderRadius: 8, border: 0 }}><img src={shield} alt="" /><span style={{ color: "var(--ink2)", fontSize: 13.5 }}>À essayer avant l’entretien : que changerait une boucle allant de 0 à 4 ? Expliquez votre raisonnement à voix haute.</span></div>
            </div>
          )}
        </div>

        <div className="r">
          <div className="panel tint" style={{ borderColor: "var(--line2)" }}>
            <h2>Ce n’est pas un verdict</h2>
            <img src={lightbulb} alt="" width={26} height={26} />
            <p className="p-body" style={{ fontSize: 14, color: "var(--ink2)" }}>Le QCM aide le conseiller à identifier vos points forts et les sujets à approfondir lors de l’entretien.</p>
            <b style={{ fontSize: 13.5, color: "var(--ink2)", fontWeight: 600 }}>Aucune admission automatique à partir de ce résultat.</b>
            <p className="small" style={{ color: "var(--muted3)", fontSize: 12.5 }}>La décision appartient à l’établissement après examen humain du dossier.</p>
          </div>
          <div className="panel">
            <h2>Préparons votre entretien</h2>
            <div><span className="chip2 hl">Prochaine étape · Rendez-vous</span></div>
            <p className="p-body" style={{ fontSize: 14, color: "var(--ink2)" }}>Un temps pour parler de vos envies, de vos acquis et de vos questions sur le parcours.</p>
            <hr className="hr" />
            <div className="p-body" style={{ color: "var(--ink2)", fontSize: 14 }}>• Un exemple de projet qui vous inspire<br />• Votre relevé de notes, si disponible<br />• Vos questions sur la Licence et la Prépa<br />• Votre budget et votre mobilité</div>
            <div><Link className="b pri" style={{ borderRadius: 9 }} to="/espace/entretien/reserver">Choisir mon rendez-vous <img src={calendarDays} alt="" style={{ filter: "invert(1)" }} /></Link></div>
            <p className="small" style={{ color: "var(--muted3)", fontSize: 12.5 }}>Le créneau sera confirmé après votre réservation.</p>
          </div>
          <div className="panel">
            <h2>Une difficulté à signaler ?</h2>
            <p className="p-body" style={{ fontSize: 14, color: "var(--ink2)" }}>Si un problème technique a affecté votre QCM, informez l’équipe avant l’entretien.</p>
            <div><a className="b" style={{ borderRadius: 9 }} href="mailto:admissions@iit.example">Contacter un conseiller</a></div>
          </div>
        </div>
      </div>
    </div>
  );
}
