import { useEffect, useRef, useState } from "react";
import { Link, Navigate, useNavigate } from "react-router-dom";
import Journey from "../../components/Journey";
import { api, ApiError, type QcmView } from "../../lib/api";
import { FORMATIONS } from "../../lib/catalog";
import { loadCandidature, saveCandidature } from "../../lib/candidature";
import circleCheckB from "../../assets/circle-check-b.svg";
import circleCheckW from "../../assets/circle-check-w.svg";
import arrowLeft from "../../assets/arrow-left.svg";
import arrowRight from "../../assets/arrow-right.svg";
import bookmark from "../../assets/bookmark.svg";
import lightbulb from "../../assets/lightbulb.svg";

const errText = (e: unknown) => (e instanceof ApiError ? e.message : "Le serveur est injoignable. Réessayez dans un instant.");

export default function QcmEnCours() {
  const nav = useNavigate();
  const f = FORMATIONS.find((x) => x.id === loadCandidature().formation) ?? FORMATIONS[0]!;
  const [qcm, setQcm] = useState<QcmView | null>(null);
  const [answers, setAnswers] = useState<Record<number, number>>({});
  const [review, setReview] = useState<number[]>(loadCandidature().qcm.review);
  const [cur, setCur] = useState(0);
  const [err, setErr] = useState("");
  const [needPre, setNeedPre] = useState(false);
  const [saved, setSaved] = useState<"idle" | "saving" | "ok" | "fail">("idle");
  const [busy, setBusy] = useState(false);
  const latest = useRef(answers);

  useEffect(() => {
    api.getQcm()
      .then((v) => {
        setQcm(v);
        setAnswers(v.answers);
        latest.current = v.answers;
        const open = v.questions.findIndex((_, i) => v.answers[i] === undefined);
        setCur(open === -1 ? 0 : open);
      })
      .catch((e) => (e instanceof ApiError && e.status === 409 ? setNeedPre(true) : setErr(errText(e))));
  }, []);

  if (needPre) {
    return (
      <div className="ws"><div className="panel" style={{ maxWidth: 560 }}>
        <h2>Une pré-inscription est nécessaire</h2>
        <p className="p-muted">Le QCM personnalisé est généré à partir de votre pré-inscription. Envoyez-la d’abord, puis revenez ici.</p>
        <div><Link className="b pri" to="/espace/preinscription">Aller à ma pré-inscription</Link></div>
      </div></div>
    );
  }
  if (!qcm) return <p className="ws small" role="status">{err || "Chargement du QCM…"}</p>;
  if (qcm.finished) return <Navigate to="/espace/qcm/resultats" replace />;

  const N = qcm.questions.length;
  const q = qcm.questions[cur]!;
  const answered = Object.keys(answers).length;
  const pct = Math.round((answered / N) * 100);
  const last = cur === N - 1;
  const sections = [...new Set(qcm.questions.map((x) => x.section))];

  async function persist(next: Record<number, number>, finish = false) {
    setSaved("saving");
    try {
      const v = await api.saveAnswers(qcm!.id, next, finish);
      setSaved("ok");
      return v;
    } catch (e) {
      setSaved("fail");
      throw e;
    }
  }
  async function choose(i: number) {
    const next = { ...answers, [cur]: i };
    setAnswers(next);
    latest.current = next;
    setErr("");
    try { await persist(next); } catch (e) { setErr(`Réponse non enregistrée : ${errText(e)}`); }
  }
  function toggleReview() {
    const r = review.includes(cur) ? review.filter((x) => x !== cur) : [...review, cur];
    setReview(r);
    saveCandidature({ qcm: { ...loadCandidature().qcm, review: r } });
  }
  async function next() {
    if (!last) { setCur(cur + 1); setSaved("idle"); return; }
    setBusy(true); setErr("");
    try {
      await persist(latest.current, true);
      saveCandidature({ qcm: { answers: latest.current, review, doneAt: new Date().toISOString() } });
      nav("/espace/qcm/resultats");
    } catch (e) { setErr(errText(e)); }
    finally { setBusy(false); }
  }

  return (
    <div className="ws" style={{ gap: 22 }}>
      <div>
        <h1 style={{ margin: 0, fontSize: 28, fontWeight: 600, letterSpacing: -0.8, color: "var(--navy)" }}>Faisons le point sur vos acquis</h1>
        <p className="p-muted" style={{ margin: "6px 0 0", fontSize: 14, color: "var(--muted3)" }}>QCM personnalisé · {f.name}, {f.institution} · Dossier SC-2026-0426</p>
      </div>
      <Journey current={4} chevrons />
      <div className="notice" style={{ padding: 17, gap: 16, alignItems: "center" }}>
        <img src={circleCheckB} alt="" style={{ width: 18, height: 18 }} />
        <span style={{ flex: 1, color: "var(--ink2)" }}>Pré-inscription reçue · Vos réponses sont enregistrées automatiquement.</span>
        <span className="chip2 hl">QCM en cours</span>
      </div>
      {err && <p className="errbox" role="alert">{err}</p>}

      <div className="detail">
        <div className="l">
          <div className="panel">
            <div className="rowb"><span className="chip2 hl">{q.section}</span><span className="small" style={{ fontSize: 13.5 }}>Question {cur + 1} sur {N}</span></div>
            <div className="prog" style={{ background: "var(--line2)" }}><i style={{ width: `${((cur + 1) / N) * 100}%`, background: "var(--link)" }} /></div>
            <h2 style={{ fontSize: 25, lineHeight: 1.35 }}>{q.text}</h2>
            <p className="p-muted" style={{ fontSize: 14 }}>Une seule réponse possible. Prenez le temps de suivre chaque étape.</p>
            {q.code && <pre className="code">{q.code.join("\n")}</pre>}
            <div className="col" style={{ gap: 10 }} role="radiogroup" aria-label="Réponses">
              {q.options.map((o, i) => {
                const on = answers[cur] === i;
                return (
                  <button key={o} role="radio" aria-checked={on} className={`ans ${on ? "on" : ""}`} onClick={() => choose(i)}>
                    <span className="mk">{"ABCD"[i]}</span><span className="tx">{o}</span>{on && <img src={circleCheckW} alt="" width={19} height={19} />}
                  </button>
                );
              })}
            </div>
            <div className="rowb">
              <button className="b" style={{ borderRadius: 9 }} disabled={cur === 0} onClick={() => setCur(cur - 1)}>Précédente <img src={arrowLeft} alt="" /></button>
              <span className="small" style={{ flex: 1, paddingLeft: 12 }} role="status">
                {saved === "saving" ? "Enregistrement…" : saved === "fail" ? "Non enregistrée — réessayez" : answers[cur] !== undefined ? "Réponse enregistrée ✓" : "Choisissez une réponse"}
              </span>
              <button className="b pri" style={{ borderRadius: 9 }} onClick={next} disabled={answers[cur] === undefined || busy || saved === "saving"}>{last ? "Terminer le QCM" : "Question suivante"} <img src={arrowRight} alt="" /></button>
            </div>
          </div>
        </div>

        <div className="r">
          <div className="panel">
            <h2>Votre progression</h2>
            <div className="rowb"><span style={{ fontSize: 14, color: "var(--ink2)" }}>{answered} réponses sur {N}</span><span className="chip2 hl">{pct} %</span></div>
            <div className="qnav">
              {qcm.questions.map((_, i) => (
                <button key={i} className={`qn ${i === cur ? "cur" : answers[i] !== undefined ? "ok" : ""} ${review.includes(i) ? "rev" : ""}`} onClick={() => setCur(i)} aria-label={`Question ${i + 1}`}>{i + 1}</button>
              ))}
            </div>
            <p className="small" style={{ color: "var(--muted3)", fontSize: 12.5 }}>Bleu clair : répondue · Bleu foncé : en cours<br />Contour ocre : à revoir</p>
            <hr className="hr" />
            {sections.map((s) => {
              const idx = qcm.questions.map((x, i) => (x.section === s ? i : -1)).filter((i) => i >= 0);
              return <div className="rowb" key={s} style={{ fontSize: 13.5 }}><span style={{ color: "var(--ink2)" }}>{s}</span><span style={{ color: "var(--muted3)" }}>{idx.filter((i) => answers[i] !== undefined).length} / {idx.length}</span></div>;
            })}
            <div><button className="b" style={{ borderRadius: 9 }} onClick={toggleReview}>{review.includes(cur) ? "Retirer « à revoir »" : "Marquer à revoir"} <img src={bookmark} alt="" /></button></div>
          </div>
          <div className="panel tint" style={{ borderColor: "var(--line2)" }}>
            <h2>Ce n’est pas un verdict</h2>
            <img src={lightbulb} alt="" width={26} height={26} />
            <p className="p-body" style={{ fontSize: 14, color: "var(--ink2)" }}>Le QCM aide le conseiller à identifier vos points forts et les sujets à approfondir lors de l’entretien.</p>
            <p className="small" style={{ color: "var(--muted3)", fontSize: 12.5 }}>Aucune admission automatique à partir de ce résultat.</p>
          </div>
          <div><Link className="b" style={{ borderRadius: 9 }} to="/espace">Enregistrer et quitter</Link></div>
        </div>
      </div>
    </div>
  );
}
