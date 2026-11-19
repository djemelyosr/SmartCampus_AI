import { useCallback, useEffect, useMemo, useState } from "react";
import { Link, Navigate, useNavigate } from "react-router-dom";
import Icon from "../../components/Icon";
import Journey from "../../components/Journey";
import { api, ApiError, type Appointment, type Slot } from "../../lib/api";
import { useAuth } from "../../lib/auth";
import { FORMATIONS } from "../../lib/catalog";
import { loadCandidature } from "../../lib/candidature";
import { addDays, dayNumber, fmtDay, fmtDayLong, fmtDayMonth, fmtTime, mondayOf, tunisDate, weekdayShort } from "../../lib/dates";

const errText = (e: unknown) => (e instanceof ApiError ? e.message : "Le serveur est injoignable. Réessayez dans un instant.");
const plus30 = (iso: string) => new Date(Date.parse(iso) + 30 * 60_000).toISOString();

/** Screen 15 (booking) and screen 16 (confirmed) share one layout; data comes from the API. */
export default function Rendezvous({ confirmed }: { confirmed: boolean }) {
  // Remount when switching between booking and confirmed views, so the appointment is fetched again.
  return <RendezvousView key={confirmed ? "confirmed" : "booking"} confirmed={confirmed} />;
}

function RendezvousView({ confirmed }: { confirmed: boolean }) {
  const { user } = useAuth();
  const nav = useNavigate();
  const c = loadCandidature();
  const f = FORMATIONS.find((x) => x.id === c.formation) ?? FORMATIONS[0]!;
  const first = (user?.full_name ?? "").split(/\s+/)[0];
  const thisWeek = mondayOf(tunisDate(Date.now()));

  const [appt, setAppt] = useState<Appointment | null | undefined>(undefined); // undefined = loading
  const [week, setWeek] = useState(thisWeek);
  const [slots, setSlots] = useState<Slot[]>([]);
  const [pick, setPick] = useState<string | null>(null);
  const [err, setErr] = useState("");
  const [busy, setBusy] = useState(false);
  const [added, setAdded] = useState(false);

  useEffect(() => {
    api.myAppointments()
      .then((l) => {
        const a = l.find((x) => x.status === "confirmed" || x.status === "proposed") ?? null;
        setAppt(a);
        if (a) setWeek(mondayOf(tunisDate(a.scheduled_at)));
      })
      .catch((e) => { setErr(errText(e)); setAppt(null); });
  }, []);

  const loadSlots = useCallback(() => {
    api.slots(week, 7)
      .then((s) => { setSlots(s); setPick((p) => (p && s.some((x) => x.slot === p && x.available) ? p : s.find((x) => x.available)?.slot ?? null)); })
      .catch((e) => setErr(errText(e)));
  }, [week]);
  useEffect(() => { if (appt !== undefined) loadSlots(); }, [appt, loadSlots]);

  const days = useMemo(() => Array.from({ length: 7 }, (_, i) => {
    const d = addDays(week, i);
    const ds = slots.filter((s) => s.slot.slice(0, 10) === d);
    const state = !ds.length ? "—" : ds.some((s) => s.available) ? "Libre" : Date.parse(ds[ds.length - 1]!.slot) < Date.now() ? "Passé" : "Complet";
    return { d, ds, state };
  }), [week, slots]);

  if (appt === undefined) return <p className="ws small">Chargement…</p>;
  if (confirmed && !appt) return <Navigate to="/espace/entretien/reserver" replace />;
  if (!confirmed && appt) return <Navigate to="/espace/entretien" replace />;

  const sel = confirmed ? appt!.scheduled_at : pick;
  const selDay = sel ? tunisDate(sel) : null;
  const dayChoice = days.find((x) => x.d === selDay);
  const label = sel ? fmtDay(sel) : "Aucun créneau";

  async function confirmSlot() {
    if (!pick) return;
    setBusy(true); setErr("");
    try { await api.bookSlot(pick); nav("/espace/entretien"); }
    catch (e) { setErr(errText(e)); loadSlots(); }
    finally { setBusy(false); }
  }
  async function modify() {
    setBusy(true); setErr("");
    try { await api.cancelAppointment(appt!.id); nav("/espace/entretien/reserver"); }
    catch (e) { setErr(errText(e)); setBusy(false); }
  }
  function ics() {
    const z = (iso: string) => new Date(iso).toISOString().replace(/[-:]/g, "").replace(/\.\d{3}/, "");
    const body = ["BEGIN:VCALENDAR", "VERSION:2.0", "BEGIN:VEVENT", `DTSTART:${z(appt!.scheduled_at)}`, `DTEND:${z(appt!.ends_at)}`, "SUMMARY:Entretien d’orientation SmartCampus", "DESCRIPTION:Visioconférence avec Amira Mansour (Admissions IIT)", "END:VEVENT", "END:VCALENDAR"].join("\r\n");
    const a = document.createElement("a");
    a.href = URL.createObjectURL(new Blob([body], { type: "text/calendar" }));
    a.download = "entretien-smartcampus.ics";
    a.click();
    setAdded(true);
  }

  const preAt = c.preinscription?.sentAt;
  const qcmAt = c.qcm.doneAt;
  const stamp = (iso?: string | null) => (iso ? `${fmtDayMonth(iso)} · ${fmtTime(iso)}` : "—");
  const steps: [string, string, string][] = [
    ["Pré-inscription reçue", stamp(preAt), `Votre choix : ${f.name}, ${f.institution}.`],
    ["QCM terminé", stamp(qcmAt), "Résultats transmis au conseiller."],
    [confirmed ? "Rendez-vous confirmé" : "Rendez-vous à réserver", sel ? (confirmed ? `${fmtDayMonth(sel)} · ${fmtTime(sel)}` : `Créneau proposé : ${fmtDayMonth(sel)} · ${fmtTime(sel)}`) : "Aucun créneau choisi", confirmed ? "Un temps d’échange sur votre projet." : "Le rendez-vous sera créé après confirmation."],
  ];

  return (
    <div className="ws" style={{ gap: 22 }}>
      <div className="rowb">
        <div>
          <h1 style={{ margin: 0, fontSize: 28, fontWeight: 600, letterSpacing: -0.8, color: "var(--navy)" }}>{confirmed ? `Votre projet avance, ${first}.` : "Choisissez votre rendez-vous"}</h1>
          <p className="p-muted" style={{ margin: "6px 0 0", fontSize: 14, color: "var(--muted3)" }}>
            {confirmed ? `Dossier SC-2026-0426 · ${f.name} · ${f.institution} · Mis à jour le ${fmtDayMonth(appt!.scheduled_at)}` : `QCM terminé · ${user?.full_name} · Étape suivante : réserver un entretien`}
          </p>
        </div>
        {confirmed
          ? <button className="b" onClick={() => window.print()}>Télécharger le récapitulatif <Icon name="upload" size={14} /></button>
          : <Link className="b" to="/espace/qcm/resultats">Revenir à mes résultats <Icon name="right" size={14} /></Link>}
      </div>
      <Journey current={5} chevrons />

      <div className="notice" style={{ padding: 22, gap: 16, alignItems: "center" }}>
        {confirmed && <span className="avatar" style={{ background: "var(--blue2)", color: "#fff", width: 44, height: 44 }}>✓</span>}
        <div style={{ flex: 1 }}>
          <b style={{ fontSize: 20, color: "var(--ink2)", fontWeight: 600 }}>{confirmed ? "Votre rendez-vous est confirmé" : "Sélectionnez un créneau disponible"}</b>
          <div style={{ fontSize: 14, color: "var(--muted3)" }}>{confirmed ? `${fmtDayLong(appt!.scheduled_at)} à ${fmtTime(appt!.scheduled_at)} · En visioconférence avec Amira Mansour, service admissions IIT.` : "Choisissez le jour et l’heure, vérifiez le récapitulatif, puis confirmez votre réservation."}</div>
        </div>
        <span style={{ fontSize: 13.5, fontWeight: 600, color: "var(--blue2)" }}>{confirmed ? "Confirmation envoyée par e-mail" : "Aucune réservation à ce stade"}</span>
      </div>
      {err && <p className="errbox" role="alert">{err}</p>}

      <div className="layout">
        <aside className="side" style={{ width: 378 }}>
          <div className="panel">
            <h2 style={{ fontSize: 18 }}>Les étapes de votre dossier</h2>
            {steps.map(([t, when, d]) => (
              <div className="rowg" key={t} style={{ alignItems: "flex-start", flexWrap: "nowrap", gap: 12, borderBottom: "1px solid var(--line)", paddingBottom: 12 }}>
                <span className="avatar" style={{ width: 25, height: 25, fontSize: 12, background: "var(--panel)", border: 0 }}>✓</span>
                <div className="kv" style={{ gap: 4 }}><b style={{ color: "var(--ink2)" }}>{t}</b><small style={{ color: "var(--link)" }}>{when}</small><small>{d}</small></div>
              </div>
            ))}
            <div className="rowg" style={{ alignItems: "flex-start", flexWrap: "nowrap", gap: 12 }}>
              <span className="avatar" style={{ width: 25, height: 25, fontSize: 12, background: "var(--panel)", border: 0 }}>4</span>
              <div className="kv" style={{ gap: 4 }}><b style={{ color: "var(--ink2)" }}>Décision de l’établissement</b><small style={{ color: "var(--link)" }}>Après étude humaine</small><small>Aucune décision d’admission à ce stade.</small></div>
            </div>
          </div>
          <div className="panel tint" style={{ borderRadius: 16 }}>
            <h2>À préparer pour l’échange</h2>
            <p className="p-muted" style={{ lineHeight: 1.45 }}>• Votre relevé de notes, si disponible<br />• Un exemple de projet qui vous inspire<br />• Vos questions sur la Licence et la Prépa</p>
            <div><Link className="b" to="/espace/documents" style={{ borderRadius: 9 }}>Ajouter un document <Icon name="upload" size={15} /></Link></div>
          </div>
        </aside>

        <section className="main" style={{ gap: 20 }}>
          <div className="panel">
            <h2 style={{ fontSize: 18 }}>{confirmed ? "Votre créneau réservé" : `Créneaux disponibles · ${label}`}</h2>
            <div className="rowb">
              <b style={{ fontSize: 14, color: "var(--ink2)" }}>{new Date(`${week}T12:00:00Z`).toLocaleDateString("fr-FR", { month: "long", year: "numeric", timeZone: "UTC" }).replace(/^./, (m) => m.toUpperCase())}</b>
              <span className="rowg" style={{ gap: 12 }}>
                <button className="lnk" aria-label="Semaine précédente" disabled={week <= thisWeek} style={{ opacity: week <= thisWeek ? 0.35 : 1 }} onClick={() => setWeek(addDays(week, -7))}>‹</button>
                <span className="small" style={{ fontSize: 13.5 }}>Semaine du {dayNumber(week)} {new Date(`${week}T12:00:00Z`).toLocaleDateString("fr-FR", { month: "long", timeZone: "UTC" })}</span>
                <button className="lnk" aria-label="Semaine suivante" onClick={() => setWeek(addDays(week, 7))}>›</button>
              </span>
            </div>
            <div className="week">
              {days.map(({ d, ds, state }) => {
                const on = d === selDay;
                const free = !confirmed && state === "Libre";
                return (
                  <button key={d} className={`wd ${on ? "on" : ""}`} disabled={!free} onClick={() => setPick(ds.find((s) => s.available)!.slot)}>
                    <small>{weekdayShort(d)}</small><b>{dayNumber(d)}</b><small>{on ? (confirmed ? "Réservé" : "Choisi") : state}</small>
                  </button>
                );
              })}
            </div>
            <div className="times">
              {(dayChoice?.ds ?? []).map((s) => {
                const on = !!sel && Date.parse(s.slot) === Date.parse(sel);
                return <button key={s.slot} className={`tm ${on ? "on" : ""}`} disabled={confirmed || !s.available} onClick={() => setPick(s.slot)} style={!s.available && !on ? { opacity: 0.4 } : undefined}>{fmtTime(s.slot)}{on && " ✓"}</button>;
              })}
              {!dayChoice?.ds.length && <span className="small">Aucun créneau cette semaine : essayez la semaine suivante.</span>}
            </div>
            <hr className="hr" />
            <div className="rowb" style={{ alignItems: "flex-start" }}>
              <div className="rowg" style={{ gap: 14, alignItems: "flex-start", flexWrap: "nowrap" }}>
                <Icon name="video" size={26} color="var(--muted3)" />
                <div className="kv" style={{ gap: 6 }}>
                  <b style={{ fontSize: 16, color: "var(--ink2)" }}>Entretien d’orientation · 30 minutes</b>
                  <small style={{ fontSize: 14, lineHeight: 1.5 }}>
                    Avec Amira Mansour · Heure de Tunis (UTC+1)<br />
                    {confirmed ? "Le lien de connexion figure dans votre e-mail de confirmation." : sel ? `${label} · ${fmtTime(sel)}–${fmtTime(plus30(sel))} · Visioconférence.` : "Choisissez un créneau pour continuer."}
                  </small>
                </div>
              </div>
              <span className="chip2 hl">{confirmed ? "Confirmé" : "À confirmer"}</span>
            </div>
            <div className="rowg" style={{ gap: 12 }}>
              {confirmed ? (
                <>
                  <button className="b pri" onClick={ics}>{added ? "Ajouté ✓" : "Ajouter à mon calendrier"} <Icon name="calendar" size={16} /></button>
                  <button className="b" disabled={busy} onClick={modify}>Modifier le créneau</button>
                </>
              ) : (
                <>
                  <button className="b pri" disabled={!pick || busy} onClick={confirmSlot}>Confirmer ce rendez-vous <Icon name="calendar" size={16} /></button>
                  <button className="b" disabled={!dayChoice} onClick={() => { const a = dayChoice!.ds.filter((s) => s.available); if (a.length) setPick(a[(a.findIndex((s) => s.slot === pick) + 1) % a.length]!.slot); }}>Choisir une autre heure</button>
                </>
              )}
            </div>
          </div>
          <div className="panel">
            <h2 style={{ fontSize: 18 }}>{confirmed ? "Vos dernières notifications" : "Avant de confirmer"}</h2>
            <div className="rowg" style={{ gap: 12, alignItems: "flex-start", flexWrap: "nowrap" }}>
              <Icon name="mail" size={18} color="var(--blue2)" />
              <div className="kv" style={{ gap: 6 }}>
                <b style={{ fontSize: 15, color: "var(--ink2)" }}>{confirmed ? "Confirmation de rendez-vous envoyée" : "Une invitation sera envoyée après réservation"}</b>
                <small style={{ fontSize: 14 }}>{confirmed ? `${user?.email} · ${fmtDayMonth(new Date().toISOString())}` : `Destinataire : ${user?.email}`}</small>
              </div>
            </div>
            <hr className="hr" />
            <div className="rowg" style={{ gap: 12, flexWrap: "nowrap" }}><Icon name="bell" size={16} color="var(--muted3)" /><span style={{ fontSize: 14, color: "var(--muted3)" }}>{confirmed ? "Un rappel est prévu la veille de votre rendez-vous." : "Vous pourrez ensuite modifier le créneau depuis votre espace."}</span></div>
          </div>
        </section>
      </div>
    </div>
  );
}
