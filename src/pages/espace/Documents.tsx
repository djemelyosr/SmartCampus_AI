import { useEffect, useRef, useState, type DragEvent } from "react";
import { Link } from "react-router-dom";
import { api, ApiError, type Appointment, type Doc } from "../../lib/api";
import { useAuth } from "../../lib/auth";
import { fmtDay, fmtDayLong, fmtStamp, fmtTime } from "../../lib/dates";
import arrowLeft from "../../assets/arrow-left.svg";
import circleAlert from "../../assets/circle-alert.svg";
import uploadCloud from "../../assets/upload-cloud.svg";
import plus from "../../assets/p-plus.svg";
import upload from "../../assets/upload.svg";
import fileText from "../../assets/file-text.svg";
import eye from "../../assets/eye.svg";
import refresh from "../../assets/refresh-cw.svg";
import calendarDays from "../../assets/calendar-days.svg";
import messages from "../../assets/messages-square.svg";
import lock from "../../assets/lock-keyhole.svg";
import shield from "../../assets/shield-check.svg";

const MAX = 10 * 1024 * 1024;
const TYPES = ["application/pdf", "image/jpeg", "image/png"];
const KINDS = ["Relevé de notes", "Pièce d’identité", "Attestation de réussite", "Autre document"];
const fmt = (n: number) => (n >= 1048576 ? `${(n / 1048576).toFixed(1).replace(".", ",")} Mo` : `${Math.max(1, Math.round(n / 1024))} Ko`);
const errText = (e: unknown) => (e instanceof ApiError ? e.message : "Le serveur est injoignable. Réessayez dans un instant.");
const ext = (d: Doc) => (d.content_type === "application/pdf" ? "PDF" : d.content_type === "image/png" ? "PNG" : "JPG");

export default function Documents() {
  const { user } = useAuth();
  const [docs, setDocs] = useState<Doc[] | null>(null);
  const [appt, setAppt] = useState<Appointment | null>(null);
  const [file, setFile] = useState<File | null>(null);
  const [kind, setKind] = useState(KINDS[0]!);
  const [err, setErr] = useState("");
  const [busy, setBusy] = useState(false);
  const [note, setNote] = useState("Je ne dispose pas encore de mon relevé. Je souhaite connaître les prochaines étapes.");
  const [sent, setSent] = useState(false);
  const input = useRef<HTMLInputElement>(null);
  const replacing = useRef(false);

  useEffect(() => {
    api.listDocuments().then(setDocs).catch((e) => { setDocs([]); setErr(errText(e)); });
    api.myAppointments().then((l) => setAppt(l.find((a) => a.status === "confirmed") ?? null)).catch(() => setAppt(null));
  }, []);

  const hasTranscript = !!docs?.some((d) => d.kind === "Relevé de notes");

  function pick(f?: File | null) {
    setErr("");
    if (!f) return;
    if (!TYPES.includes(f.type)) return setErr("Format non accepté : PDF, JPG ou PNG uniquement.");
    if (f.size > MAX) return setErr("Fichier trop volumineux : 10 Mo maximum.");
    setFile(f);
    if (replacing.current) { replacing.current = false; void transmit(f); }
  }
  const onDrop = (e: DragEvent) => { e.preventDefault(); pick(e.dataTransfer.files[0]); };

  async function transmit(f = file) {
    if (!f) return;
    setBusy(true); setErr("");
    try {
      const d = await api.uploadDocument(kind, f);
      setDocs((l) => [d, ...(l ?? [])]);
      setFile(null);
    } catch (e) { setErr(errText(e)); }
    finally { setBusy(false); }
  }
  async function consult(id: number) {
    setErr("");
    try { await api.openDocument(id); } catch (e) { setErr(errText(e)); }
  }
  function replace() { replacing.current = true; input.current?.click(); }

  return (
    <div className="ws" style={{ gap: 22 }}>
      <div className="rowb">
        <div>
          <h1 style={{ margin: 0, fontSize: 28, fontWeight: 600, letterSpacing: -0.8, color: "var(--navy)" }}>Les pièces pour préparer la suite</h1>
          <p className="p-muted" style={{ margin: "6px 0 0", fontSize: 14, color: "var(--muted3)" }}>Dossier SC-2026-0426 · {user?.full_name} · Campagne 2026–2027</p>
        </div>
        <Link className="b" to="/espace/suivi">Retour à ma candidature <img src={arrowLeft} alt="" /></Link>
      </div>
      <div className="rowg" style={{ gap: 8 }}>
        <Link className="b" style={{ padding: "11px 12px", borderRadius: 8, fontWeight: 400, fontSize: 12.5, color: "var(--muted3)" }} to="/espace/suivi">Vue du dossier</Link>
        <span className="b" style={{ padding: "11px 12px", borderRadius: 8, fontSize: 12.5, background: "var(--panel)", color: "var(--blue2)" }}>Documents ({docs?.length ?? 0})</span>
        <Link className="b" style={{ padding: "11px 12px", borderRadius: 8, fontWeight: 400, fontSize: 12.5, color: "var(--muted3)" }} to="/espace/notifications">Historique</Link>
      </div>

      {!hasTranscript && docs && (
        <div className="notice" style={{ background: "#fff4de", border: 0, borderRadius: 9, color: "#8d6417" }}>
          <img src={circleAlert} alt="" /><span>Un relevé de notes est encore demandé. Les autres documents déposés ne le remplacent pas ; leur conformité reste à vérifier par l’équipe.</span>
        </div>
      )}

      <div className="detail">
        <div className="l">
          <div className="panel">
            <h2>Ajouter mon relevé de notes</h2>
            <div className="rowb"><span className="chip2 warn" style={{ background: "#fff4de", color: "#8d6417" }}>Pièce demandée</span><span className="small">Demandé par le service admissions</span></div>
            <p className="p-body" style={{ fontSize: 14, color: "var(--ink2)" }}>L’équipe souhaite consulter votre relevé pour préparer l’entretien. Ajoutez-le si vous en disposez ; sinon, prévenez votre conseiller.</p>
            <label className="fld" style={{ fontSize: 13.5, color: "var(--ink2)" }}>Type de document
              <select value={kind} onChange={(e) => setKind(e.target.value)}>{KINDS.map((o) => <option key={o}>{o}</option>)}</select>
            </label>
            <div className="drop" onDragOver={(e) => e.preventDefault()} onDrop={onDrop}>
              <img src={uploadCloud} alt="" width={30} height={30} />
              <b>{file ? file.name : `Glissez votre ${kind.toLowerCase()} ici`}</b>
              <span>{file ? `${fmt(file.size)} prêt à être transmis` : "ou sélectionnez un fichier · PDF, JPG, PNG · 10 Mo maximum"}</span>
              <button type="button" className="b" style={{ borderRadius: 9 }} onClick={() => { replacing.current = false; input.current?.click(); }}>Choisir un fichier <img src={plus} alt="" /></button>
              <input ref={input} type="file" accept=".pdf,.jpg,.jpeg,.png" hidden onChange={(e) => { pick(e.target.files?.[0]); e.target.value = ""; }} />
            </div>
            {err ? <p className="errbox" role="alert">{err}</p> : <p className="small" style={{ color: "var(--muted3)", fontSize: 12.5 }}>{file ? "Vérifiez que toutes les pages et les notes sont lisibles." : "Aucun fichier sélectionné. Vérifiez que toutes les pages et les notes sont lisibles."}</p>}
            <div className="rowg" style={{ gap: 12, flexWrap: "nowrap" }}>
              <button className="b" style={{ borderRadius: 9, background: file ? "var(--blue2)" : "#f8fafc", color: file ? "#fff" : "var(--muted3)" }} disabled={!file || busy} onClick={() => transmit()}>{busy ? "Transmission…" : "Transmettre le document"} <img src={upload} alt="" style={file ? { filter: "invert(1)" } : undefined} /></button>
              <span className="small" style={{ color: "var(--muted3)", fontSize: 12.5 }}>{file ? "Le fichier sera transmis à l’équipe IIT." : "Disponible après la sélection d’un fichier."}</span>
            </div>
          </div>

          <div className="panel">
            <h2>Documents déposés ({docs?.length ?? 0})</h2>
            {docs === null && <p className="small" role="status">Chargement…</p>}
            {docs?.length === 0 && <p className="p-muted" style={{ fontSize: 14 }}>Aucun document déposé pour le moment.</p>}
            {docs?.map((d) => (
              <div className="col" key={d.id} style={{ gap: 16, paddingBottom: 12, borderBottom: "1px solid #eef3f8" }}>
                <div className="rowg" style={{ gap: 14, flexWrap: "nowrap" }}>
                  <div style={{ background: "var(--panel)", width: 42, height: 48, borderRadius: 8, display: "flex", alignItems: "center", justifyContent: "center", flex: "none" }}><img src={fileText} alt="" width={24} height={24} /></div>
                  <div className="kv" style={{ flex: 1, gap: 5, minWidth: 0 }}><b style={{ color: "var(--ink2)" }}>{d.kind}</b><small style={{ fontSize: 12.5, color: "var(--muted3)", overflowWrap: "anywhere" }}>{d.filename} · {ext(d)} · {fmt(d.size)}</small></div>
                  <span className="chip2" style={{ background: "#fff4de", color: "#8d6417" }}>{d.status === "conforme" ? "Vérifié" : d.status === "refuse" ? "À remplacer" : "À vérifier"}</span>
                </div>
                <div className="grid g2" style={{ gap: 20 }}>
                  <div className="kv" style={{ gap: 4 }}><small style={{ fontSize: 11.5 }}>DÉPÔT</small><b style={{ fontSize: 13.5, color: "var(--ink2)" }}>{d.created_at ? fmtStamp(d.created_at) : "—"}</b></div>
                  <div className="kv" style={{ gap: 4 }}><small style={{ fontSize: 11.5 }}>REVUE HUMAINE</small><b style={{ fontSize: 13.5, color: "var(--ink2)" }}>{d.status === "conforme" ? "Validé par l’équipe IIT" : "En attente de l’équipe IIT"}</b></div>
                </div>
                <p className="small" style={{ color: "var(--muted3)", fontSize: 13.5 }}>Contenu et conformité à vérifier. Ce dépôt ne vaut pas admission.</p>
                <div className="rowg" style={{ gap: 10 }}>
                  <button className="b" style={{ borderRadius: 9 }} onClick={() => consult(d.id)}>Consulter <img src={eye} alt="" /></button>
                  <button className="b" style={{ borderRadius: 9 }} onClick={replace} disabled={busy}>Remplacer <img src={refresh} alt="" /></button>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="r">
          <div className="panel tint" style={{ borderRadius: 16 }}>
            <h2>Votre prochaine rencontre</h2>
            {appt ? (
              <>
                <div><span className="chip2 hl">Entretien confirmé</span></div>
                <p style={{ fontSize: 21, fontWeight: 600, color: "var(--ink2)", lineHeight: 1.45 }}>{fmtDayLong(appt.scheduled_at)}<br />{fmtTime(appt.scheduled_at)} – {fmtTime(appt.ends_at)}</p>
                <p className="p-body" style={{ fontSize: 14, color: "var(--ink2)", lineHeight: 1.45 }}>Avec Amira Mansour · Admissions IIT<br />Visioconférence · Heure de Tunis (UTC+1)</p>
                <div><Link className="b" style={{ borderRadius: 9 }} to="/espace/entretien">Voir mon rendez-vous <img src={calendarDays} alt="" /></Link></div>
              </>
            ) : (
              <>
                <p className="p-body" style={{ fontSize: 14, color: "var(--ink2)" }}>Aucun entretien n’est réservé pour le moment.</p>
                <div><Link className="b" style={{ borderRadius: 9 }} to="/espace/entretien/reserver">Choisir mon rendez-vous <img src={calendarDays} alt="" /></Link></div>
              </>
            )}
          </div>
          <div className="panel">
            <h2>Vous n’avez pas encore la pièce ?</h2>
            <p className="p-body" style={{ fontSize: 14, color: "var(--ink2)" }}>Signalez-le à l’équipe : elle vous indiquera la marche à suivre. Ne déposez pas un document sans rapport à la place du relevé.</p>
            <label className="fld" style={{ fontSize: 13.5, color: "var(--ink2)" }}>Message au conseiller<textarea rows={3} value={note} onChange={(e) => setNote(e.target.value)} /></label>
            <div><button className="b" style={{ borderRadius: 9 }} onClick={() => setSent(true)}>Signaler une pièce indisponible <img src={messages} alt="" /></button></div>
            <p className="small" style={{ color: "var(--muted3)", fontSize: 11.5 }}>{sent ? "Signalement noté sur cet écran : l’envoi de messages au conseiller n’est pas encore disponible." : "L’envoi de messages au conseiller n’est pas encore disponible."}</p>
          </div>
          <div className="panel">
            <h2>Vos documents restent confidentiels</h2>
            <img src={lock} alt="" width={24} height={24} />
            <p className="p-body" style={{ color: "var(--ink2)" }}>Accès limité à vous et aux équipes habilitées pour votre dossier. Les pièces ne sont pas publiées dans le catalogue ni utilisées comme sources RAG.</p>
            <hr className="hr" />
            <p className="small" style={{ color: "var(--muted3)", fontSize: 12.5 }}>Consulter la politique de confidentialité et les modalités d’exercice de vos droits.</p>
          </div>
        </div>
      </div>
      <div className="notice" style={{ borderRadius: 9, color: "var(--ink2)" }}><img src={shield} alt="" /><span>Le dépôt et la vérification d’une pièce ne valent pas admission. Seule l’équipe habilitée de l’établissement peut prendre une décision officielle.</span></div>
    </div>
  );
}
