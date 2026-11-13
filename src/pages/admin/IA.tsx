import { useState } from "react";
import { Link } from "react-router-dom";
import AdminShell from "../../components/AdminShell";
import Icon from "../../components/Icon";

const Tog = ({ on, onClick, label, locked }: { on: boolean; onClick: () => void; label: string; locked?: boolean }) => <button type="button" role="switch" aria-checked={on} aria-label={label} disabled={locked} className={`tog ${on ? "on" : ""}`} style={locked ? { opacity: 0.45, cursor: "not-allowed" } : undefined} onClick={onClick}><i /></button>;
const Row = ({ t, d, on, set, locked }: { t: string; d: string; on: boolean; set: () => void; locked?: boolean }) => <div className="rowb" style={{ flexWrap: "nowrap" }}><div className="kvx"><b style={{ fontSize: 13 }}>{t}</b><small>{d}</small></div><Tog on={on} onClick={set} label={t} locked={locked} /></div>;
function Sel({ label, value, options, onChange }: { label: string; value: string; options: string[]; onChange: (v: string) => void }) {
  return <label className="fld" style={{ fontSize: 12 }}>{label}<select className="sel" value={value} onChange={(e) => onChange(e.target.value)}>{options.map((o) => <option key={o}>{o}</option>)}</select></label>;
}

export default function IA() {
  const [langs, setLangs] = useState({ fr: true, tn: true, ar: true });
  const [t, setT] = useState({ detect: true, stt: true, relire: true, brut: false, justify: true, cite: true, roles: true, mask: true });
  const [def, setDef] = useState("Français · Choix candidat prioritaire");
  const [style, setStyle] = useState("Clair, rassurant, non prescriptif");
  const [depth, setDepth] = useState("Courte · Approfondir sur demande");
  const [scope, setScope] = useState("Sources IIT / ISB validées uniquement");
  const [note, setNote] = useState("");
  const [eval_, setEval] = useState("Évaluation réelle non effectuée");
  const [msg, setMsg] = useState("");
  const flip = (k: keyof typeof t) => setT({ ...t, [k]: !t[k] });
  const AG: [string, string, string][] = [["Orientation", "Profil et recommandations", "12 relais à examiner"], ["Admission", "Pré-inscription et QCM", "4 dossiers en attente"], ["Suivi", "Rappels et rendez-vous", "2 rappels à contrôler"]];

  return (
    <AdminShell title="Une IA encadrée, à votre écoute" sub="Conversation, audio et connexions · Paramètres illustratifs · Campagne 2026-2027"
      action={<button className="b gold" onClick={() => setMsg("Brouillon enregistré (démonstration).")}>Enregistrer le brouillon <Icon name="save" size={14} /></button>}>
      <div className="notice" style={{ borderRadius: 8 }}><Icon name="shield" size={15} color="var(--blue2)" /><span style={{ fontSize: 13, color: "var(--ink2)" }}>Les agents assistent l’orientation et le suivi. Toute décision officielle d’admission exige une personne habilitée ; cette règle ne peut pas être désactivée.</span></div>
      {msg && <p className="okbox" role="status">{msg}</p>}

      <div className="layout">
        <div className="panel" style={{ flex: "1 1 420px", gap: 12 }} id="audio">
          <h2 style={{ fontSize: 17 }}>Audio & langues</h2>
          <span className="small" style={{ fontSize: 12 }}>Langues proposées dans l’espace candidat</span>
          {([["fr", "Français"], ["tn", "Tunisien · Tounsi"], ["ar", "Arabizi · Tunisien translittéré"]] as const).map(([k, l]) => (
            <label key={k} className={`cbx ${langs[k] ? "on" : ""}`} style={{ fontSize: 13 }}><input type="checkbox" checked={langs[k]} onChange={() => setLangs({ ...langs, [k]: !langs[k] })} /><i>{langs[k] && <Icon name="check" size={12} color="#fff" />}</i>{l}</label>
          ))}
          <Sel label="Langue par défaut" value={def} options={["Français · Choix candidat prioritaire", "Tounsi", "Arabizi"]} onChange={setDef} />
          <Row t="Détection de langue" d="Proposer un changement, sans l’imposer" on={t.detect} set={() => flip("detect")} />
          <Row t="Transcription audio" d="Avec accord préalable du candidat" on={t.stt} set={() => flip("stt")} />
          <Row t="Relire avant envoi" d="Le candidat peut corriger la transcription" on={t.relire} set={() => flip("relire")} />
          <Row t="Conserver l’audio brut" d="Désactivé dans la configuration de la démo" on={t.brut} set={() => flip("brut")} locked />
          <p className="small" style={{ fontSize: 11 }}>En cas d’incertitude : demander une reformulation ou proposer un relais humain, sans déduire une réponse.</p>
        </div>

        <div className="panel" style={{ flex: "1 1 420px", gap: 12 }}>
          <h2 style={{ fontSize: 17 }}>Conversation & sources RAG</h2>
          <Sel label="Style conversationnel" value={style} options={["Clair, rassurant, non prescriptif", "Concis et factuel", "Chaleureux et détaillé"]} onChange={setStyle} />
          <Sel label="Profondeur des réponses" value={depth} options={["Courte · Approfondir sur demande", "Détaillée d’emblée"]} onChange={setDepth} />
          <Row t="Justifier les recommandations" d="Relier les pistes au profil déclaré" on={t.justify} set={() => flip("justify")} />
          <Row t="Citer les sources disponibles" d="Document et passage consultables" on={t.cite} set={() => flip("cite")} />
          <Sel label="Périmètre des sources" value={scope} options={["Sources IIT / ISB validées uniquement", "Toutes les sources indexées"]} onChange={setScope} />
          <div className="warnbox"><Icon name="shield" size={14} color="#8d6417" />Si une information n’est pas sourcée ou validée : l’indiquer et demander une vérification humaine. Ne pas inventer de conditions ni de frais.</div>
          <small className="small" style={{ fontSize: 11 }}>1 source en échec OCR reste exclue des réponses. Les dossiers candidats ne constituent pas des sources RAG.</small>
          <div><Link className="b" style={{ fontSize: 12.5 }} to="/admin">Consulter les sources <Icon name="db" size={14} /></Link></div>
        </div>
      </div>

      <div className="panel" style={{ gap: 12 }}>
        <h2 style={{ fontSize: 17 }}>Supervision des agents</h2>
        <div className="grid g3" style={{ gap: 14 }}>
          {AG.map(([n, d, r]) => <div key={n} className="prev" style={{ borderRadius: 8 }}><div className="rowb"><Icon name="bot" size={16} color="var(--muted3)" /><span className="chip2 hl" style={{ fontSize: 11 }}>Actif · Démo</span></div><b>{n}</b><span style={{ fontSize: 12 }}>{d}</span><span style={{ fontSize: 12, color: "var(--ink2)" }}>{r}</span><Link to="/admin/journal" style={{ fontSize: 12.5, fontWeight: 600, color: "var(--navy)" }}>Consulter l’activité →</Link></div>)}
        </div>
        <div className="grid g2" style={{ gap: 14 }}>
          <div className="kvx"><small style={{ fontSize: 11 }}>RELAIS PAR DÉFAUT</small><b>Équipe admissions IIT / ISB</b></div>
          <div className="kvx"><small style={{ fontSize: 11 }}>CAS PRIORITAIRES</small><b>Incertitude, demande explicite, données sensibles</b></div>
        </div>
      </div>

      <div className="layout" id="integrations">
        <div className="panel" style={{ flex: "1 1 460px", gap: 12 }}>
          <h2 style={{ fontSize: 17 }}>Intégrations & sécurité</h2>
          <div className="rowb"><span className="rowg" style={{ gap: 8 }}><Icon name="mail" size={16} color="var(--blue2)" /><b style={{ fontSize: 13 }}>E-mail</b></span><span className="chip2 hl" style={{ fontSize: 11 }}>Connecté · Bac à sable</span></div>
          <p className="small" style={{ fontSize: 11.5 }}>Confirmations et rappels · Dernier contrôle simulé : 08 juillet, 09:00.</p>
          <div className="rowb"><span className="rowg" style={{ gap: 8 }}><Icon name="calendar" size={16} color="var(--blue2)" /><b style={{ fontSize: 13 }}>Calendrier</b></span><span className="chip2" style={{ background: "#fff4de", color: "#8d6417", fontSize: 11 }}>À reconnecter</span></div>
          <p className="small" style={{ fontSize: 11.5 }}>La synchronisation est suspendue. Le rendez-vous confirmé de Fatma reste visible ; aucune nouvelle synchronisation n’est simulée.</p>
          <div className="rowg" style={{ gap: 10 }}><button className="b" style={{ fontSize: 12.5 }} onClick={() => setMsg("État des intégrations : e-mail OK (bac à sable), calendrier à reconnecter.")}>Consulter l’état</button><button className="b" style={{ fontSize: 12.5 }} onClick={() => setMsg("Reconnexion préparée (démonstration).")}>Reconnecter <Icon name="lock" size={13} /></button></div>
          <hr className="hr" />
          <Row t="Accès selon les rôles" d="Périmètres IIT / ISB et journalisation" on={t.roles} set={() => flip("roles")} />
          <Row t="Masquer les données sensibles" d="Dans les traces et les aperçus" on={t.mask} set={() => flip("mask")} />
          <small className="small" style={{ fontSize: 11 }}>Identifiants gérés dans un coffre sécurisé. Aucun secret ni jeton affiché sur cet écran.</small>
          <div><button className="b" style={{ fontSize: 12.5 }} onClick={() => setMsg("Politique de sécurité : document de démonstration.")}>Consulter la politique de sécurité <Icon name="shield" size={13} /></button></div>
        </div>

        <div className="panel" style={{ flex: "1 1 400px", gap: 12 }}>
          <h2 style={{ fontSize: 17 }}>Évaluation · Exemple illustratif</h2>
          <div><span className="chip2" style={{ background: "#fff4de", color: "#8d6417", fontSize: 11 }}>Données fictives · Pas des performances réelles</span></div>
          <p className="small" style={{ fontSize: 12 }}>Un exemple de tableau de contrôle pour préparer la recette. Ces valeurs ne mesurent pas le système en production.</p>
          {[["Compréhension de l’intention", 86], ["Réponses avec source citée", 92]].map(([n, v]) => <div key={n as string} className="col" style={{ gap: 6 }}><div className="rowb" style={{ fontSize: 12.5 }}><span>{n}</span><b>{v} %</b></div><div className="hbar"><i style={{ width: `${v}%` }} /></div></div>)}
          <div className="kvx"><small style={{ fontSize: 11 }}>JEU DE TEST FICTIF</small><b>50 échanges · Français, Tounsi, Arabizi</b></div>
          <p className="small" style={{ fontSize: 11.5 }}>Points à examiner : alternance des langues, transcription des noms propres et absence de source officielle.</p>
          <Sel label="État de la recette" value={eval_} options={["Évaluation réelle non effectuée", "Recette en préparation", "Recette en cours"]} onChange={setEval} />
          <div><button className="b" style={{ fontSize: 12.5 }} onClick={() => { setNote("Évaluation humaine préparée : jeu de 50 échanges à relire (démonstration)."); setMsg(""); }}>Préparer une évaluation humaine <Icon name="clipboard" size={13} /></button></div>
          <small className="small" style={{ fontSize: 11 }}>{note || "Aucun test lancé et aucun résultat réel n’est enregistré dans cette démonstration."}</small>
        </div>
      </div>
      <small className="small" style={{ fontSize: 11 }}>Version de configuration v0.8 · Modifications à relire avant activation · Les actions ci-dessus ne modifient aucun service réel.</small>
    </AdminShell>
  );
}
