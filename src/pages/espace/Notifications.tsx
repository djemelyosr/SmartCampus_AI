import { useState } from "react";
import { Link } from "react-router-dom";
import Icon from "../../components/Icon";
import { useAuth } from "../../lib/auth";
import { loadCandidature, saveCandidature } from "../../lib/candidature";

type Kind = "Rappel" | "Information à compléter" | "Confirmation" | "QCM";
interface N { id: string; icon: Parameters<typeof Icon>[0]["name"]; title: string; body: string; when: string; chan: string; kind: Kind; cta: [string, string]; group: "Aujourd’hui" | "Précédemment"; rdv?: boolean; todo?: boolean }

const ITEMS: N[] = [
  { id: "n1", icon: "bell", title: "Votre entretien a lieu demain", body: "Jeudi 9 juillet à 10:00 · Visioconférence avec Amira Mansour, service admissions IIT. Le lien figure dans votre e-mail de confirmation.", when: "08 juillet · 10:00", chan: "E-mail + espace candidat", kind: "Rappel", cta: ["Voir mon rendez-vous", "/espace/entretien"], group: "Aujourd’hui", rdv: true },
  { id: "n2", icon: "filePlus", title: "Un relevé de notes est demandé", body: "L’équipe vous invite à ajouter votre relevé, si disponible, pour préparer l’échange. Si vous ne l’avez pas encore, signalez-le au conseiller.", when: "08 juillet · 09:15", chan: "Espace candidat", kind: "Information à compléter", cta: ["Ajouter un document", "/espace/documents"], group: "Aujourd’hui", todo: true },
  { id: "n3", icon: "calendar", title: "Votre rendez-vous est confirmé", body: "Jeudi 9 juillet 2026 à 10:00 · Entretien d’orientation de 30 minutes. Confirmation envoyée à {email}.", when: "07 juillet · 09:36", chan: "E-mail + espace candidat", kind: "Confirmation", cta: ["Consulter la confirmation", "/espace/entretien"], group: "Précédemment", rdv: true },
  { id: "n4", icon: "clipboard", title: "Votre QCM est terminé", body: "Vos 12 réponses sont enregistrées. Le bilan a été transmis au conseiller pour préparer l’entretien, sans décision automatique.", when: "07 juillet · 09:24", chan: "Espace candidat", kind: "QCM", cta: ["Consulter mes résultats", "/espace/qcm/resultats"], group: "Précédemment" },
  { id: "n5", icon: "folder", title: "Votre pré-inscription a bien été reçue", body: "Dossier SC-2026-0426 · Licence en informatique, IIT. L’équipe étudiera vos informations ; ceci ne vaut pas admission.", when: "06 juillet · 11:18", chan: "E-mail + espace candidat", kind: "Confirmation", cta: ["Voir ma candidature", "/espace/suivi"], group: "Précédemment" },
];
const FILTERS = ["Toutes", "Non lues", "À compléter", "Rendez-vous"] as const;
const CHANNELS: [string, string, string][] = [["espace", "Espace candidat", "Confirmations et suivi du dossier"], ["email", "E-mail", "{email}"], ["sms", "SMS", "+216 20 000 426"]];
const TOPICS: [string, string, string?][] = [["confirmations", "Confirmations de candidature"], ["rappels", "Rappels de rendez-vous"], ["complements", "Demandes de complément"], ["actus", "Actualités et invitations", "Facultatif"]];

function Sw({ on, onClick, label }: { on: boolean; onClick: () => void; label: string }) {
  return (
    <button type="button" role="switch" aria-checked={on} aria-label={label} onClick={onClick}
      style={{ width: 34, height: 20, borderRadius: 20, border: 0, padding: 3, display: "flex", justifyContent: on ? "flex-end" : "flex-start", background: on ? "var(--link)" : "var(--line)", flex: "none" }}>
      <span style={{ width: 14, height: 14, borderRadius: 14, background: "#fff" }} />
    </button>
  );
}

export default function Notifications() {
  const { user } = useAuth();
  const c0 = loadCandidature();
  const [read, setRead] = useState<string[]>(c0.notifRead.length ? c0.notifRead : ["n4", "n5"]);
  const [prefs, setPrefs] = useState(c0.prefs);
  const [filter, setFilter] = useState<(typeof FILTERS)[number]>("Toutes");
  const [saved, setSaved] = useState(false);
  const email = user?.email ?? "";
  const unread = (n: N) => !read.includes(n.id);
  const visible = ITEMS.filter((n) => filter === "Toutes" || (filter === "Non lues" && unread(n)) || (filter === "À compléter" && n.todo) || (filter === "Rendez-vous" && n.rdv));
  const counts = { Toutes: ITEMS.length, "Non lues": ITEMS.filter(unread).length, "À compléter": ITEMS.filter((n) => n.todo).length, "Rendez-vous": ITEMS.filter((n) => n.rdv).length };
  const mark = (ids: string[]) => { const r = [...new Set([...read, ...ids])]; setRead(r); saveCandidature({ notifRead: r }); };
  const toggle = (k: string) => { setPrefs((p) => ({ ...p, [k]: !p[k] })); setSaved(false); };

  return (
    <div className="ws" style={{ gap: 22 }}>
      <div className="rowb">
        <div>
          <h1 style={{ margin: 0, fontSize: 28, fontWeight: 600, letterSpacing: -0.8, color: "var(--navy)" }}>Gardez le fil de votre candidature</h1>
          <p className="p-muted" style={{ margin: "6px 0 0", fontSize: 14, color: "var(--muted3)" }}>Dossier SC-2026-0426 · Vos confirmations, rappels et informations à compléter.</p>
        </div>
        <button className="b" onClick={() => mark(ITEMS.map((n) => n.id))}>Tout marquer comme lu <Icon name="checks" size={16} /></button>
      </div>
      <div className="rowg" style={{ gap: 10 }}>
        {FILTERS.map((f) => (
          <button key={f} className={`b ${filter === f ? "pri" : ""}`} onClick={() => setFilter(f)}>{f} · {counts[f]}</button>
        ))}
      </div>

      <div className="detail">
        <div className="l" style={{ gap: 12, width: 850 }}>
          {(["Aujourd’hui", "Précédemment"] as const).map((g) => {
            const list = visible.filter((n) => n.group === g);
            if (!list.length) return null;
            return (
              <div key={g} className="col" style={{ gap: 14 }}>
                <span className="small" style={{ letterSpacing: 0.3, textTransform: "uppercase" }}>{g === "Aujourd’hui" ? "08 juillet 2026 · Aujourd’hui" : "Précédemment"}</span>
                {list.map((n) => (
                  <article key={n.id} className="notif" style={unread(n) ? { background: "var(--panel)" } : undefined}>
                    <div className="rowb" style={{ alignItems: "flex-start", flexWrap: "nowrap" }}>
                      <div className="rowg" style={{ gap: 14, flexWrap: "nowrap", alignItems: "flex-start" }}>
                        <Icon name={n.icon} size={18} color="var(--blue2)" />
                        <div className="kv" style={{ gap: 8 }}>
                          <b style={{ fontSize: 15, color: "var(--ink2)" }}>{n.title}</b>
                          <span style={{ fontSize: 14, color: "var(--ink2)", lineHeight: 1.45 }}>{n.body.replace("{email}", email)}</span>
                          <small style={{ fontSize: 12 }}>{n.when} · {n.chan}</small>
                        </div>
                      </div>
                      <span style={{ fontSize: 12.5, fontWeight: 600, whiteSpace: "nowrap", color: unread(n) ? "var(--blue2)" : "var(--muted3)" }}>{unread(n) ? "● Non lue" : "✓ Lue"}</span>
                    </div>
                    <div className="rowb" style={{ paddingLeft: 32 }}>
                      <Link to={n.cta[1]} onClick={() => mark([n.id])} style={{ color: "var(--blue2)", fontWeight: 600, fontSize: 14 }}>{n.cta[0]} →</Link>
                      <div className="rowg" style={{ gap: 16 }}>
                        <span className={`chip2 ${n.kind === "Information à compléter" ? "warn" : "hl"}`} style={n.kind === "Information à compléter" ? { background: "#fff4de", color: "#8d6417" } : { background: "#fff" }}>{n.kind}</span>
                        {unread(n) && <button className="lnk" style={{ color: "var(--muted3)", fontWeight: 400 }} onClick={() => mark([n.id])}>Marquer comme lue</button>}
                      </div>
                    </div>
                  </article>
                ))}
              </div>
            );
          })}
          {visible.length === 0 && <p className="p-muted">Aucune notification dans cette catégorie.</p>}
          <p className="small">Vous avez consulté toutes les notifications de cette démonstration.</p>
        </div>

        <div className="r" style={{ gap: 20 }}>
          <div className="panel">
            <h2 style={{ fontSize: 18 }}>Vos canaux de notification</h2>
            <p className="p-muted" style={{ fontSize: 14 }}>Choisissez comment recevoir les messages de suivi.</p>
            {CHANNELS.map(([k, t, d]) => (
              <div className="rowb" key={k} style={{ flexWrap: "nowrap" }}><div className="kv" style={{ gap: 4 }}><b style={{ fontSize: 14 }}>{t}</b><small style={{ fontSize: 13 }}>{d.replace("{email}", email)}</small></div><Sw on={!!prefs[k]} onClick={() => toggle(k)} label={t} /></div>
            ))}
            <hr className="hr" />
            <b style={{ fontSize: 14, color: "var(--ink2)" }}>Ce que vous souhaitez recevoir</b>
            {TOPICS.map(([k, t, d]) => (
              <div className="rowb" key={k} style={{ flexWrap: "nowrap" }}><div className="kv" style={{ gap: 4 }}><b style={{ fontSize: 14 }}>{t}</b>{d && <small style={{ fontSize: 13 }}>{d}</small>}</div><Sw on={!!prefs[k]} onClick={() => toggle(k)} label={t} /></div>
            ))}
            <hr className="hr" />
            <div><button className="b pri" style={{ borderRadius: 9 }} onClick={() => { saveCandidature({ prefs }); setSaved(true); }}>Enregistrer mes préférences</button></div>
            <p className="small" style={{ fontSize: 12.5 }}>{saved ? "Préférences enregistrées." : "Le suivi reste consultable dans votre espace, quels que soient les canaux choisis."}</p>
          </div>
          <div className="panel tint" style={{ borderRadius: 16 }}>
            <h2 style={{ fontSize: 18 }}>Votre prochain rendez-vous</h2>
            <div><span className="chip2 hl" style={{ background: "none" }}>Confirmé</span></div>
            <p style={{ fontSize: 22, fontWeight: 600, color: "var(--ink2)", lineHeight: 1.45 }}>Jeudi 9 juillet<br />10:00 – 10:30</p>
            <p className="p-body" style={{ fontSize: 14, color: "var(--ink2)", lineHeight: 1.45 }}>Avec Amira Mansour · Admissions IIT<br />Visioconférence · Heure de Tunis (UTC+1)</p>
            <div><Link className="b" style={{ borderRadius: 9 }} to="/espace/entretien">Voir les détails <Icon name="calendar" size={16} /></Link></div>
          </div>
          <div className="notice" style={{ borderRadius: 9, border: 0 }}><Icon name="shield" size={17} color="var(--blue2)" /><span style={{ fontSize: 14, color: "var(--ink2)" }}>Ces messages concernent le suivi du dossier. Seule une décision officielle de l’établissement peut confirmer une admission.</span></div>
          <div className="panel">
            <h2 style={{ fontSize: 18 }}>Besoin de préciser un point ?</h2>
            <p className="p-body" style={{ color: "var(--ink2)", fontSize: 14 }}>Une pièce indisponible ou un empêchement ? Prévenez le conseiller pour préparer la suite.</p>
            <div><a className="b" style={{ borderRadius: 9 }} href="mailto:admissions@iit.example">Contacter l’équipe</a></div>
          </div>
        </div>
      </div>
    </div>
  );
}
