import { useEffect, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import Icon from "../../components/Icon";
import { api, type InterviewDetail, type InterviewItem } from "../../lib/api";

const POINTS = [
  "Explorer un projet logiciel qui la motive et sa façon d’apprendre.",
  "Discuter du rythme, de la théorie et des différences Licence / Prépa.",
  "Revenir sur les conditions en algorithmique et la sécurité numérique.",
  "Confirmer la mobilité, le budget et la disponibilité du relevé de notes.",
];
const SUITES = ["En attente de l’entretien", "Avis favorable à l’étude", "Autre orientation proposée", "Pièce complémentaire demandée"];
const DEMO_SECTIONS: [string, number, number][] = [["Logique & algorithmique", 4, 5], ["Mathématiques", 3, 4], ["Culture numérique", 2, 3]];
const when = (iso: string) => new Date(iso).toLocaleString("fr-FR", { timeZone: "Africa/Tunis", weekday: "long", day: "2-digit", month: "long", year: "numeric", hour: "2-digit", minute: "2-digit" });

export default function Entretien() {
  const [params] = useSearchParams();
  const [list, setList] = useState<InterviewItem[]>([]);
  const [d, setD] = useState<InterviewDetail | null>(null);
  useEffect(() => { api.interviewCandidates().then(setList).catch(() => setList([])); }, []);
  const curId = Number(params.get("id")) || list[0]?.id;
  useEffect(() => { if (curId) api.interviewCandidate(curId).then(setD).catch(() => setD(null)); else setD(null); }, [curId]);
  const points = d ? d.points : POINTS;
  const initials = d ? d.name.split(/\s+/).map((w) => w[0]).slice(0, 2).join("").toUpperCase() : "FK";
  const sections: [string, number, number][] = d?.qcm_result ? d.qcm_result.by_section.map((s) => [s.section, s.good, s.total]) : d ? [] : DEMO_SECTIONS;
  const [done, setDone] = useState<boolean[]>([]);
  const [prep, setPrep] = useState("Avant l’échange : clarifier la préférence pour une progression pratique et recueillir un exemple de projet. Mobilité et budget à confirmer avec le candidat.");
  const [cr, setCr] = useState("");
  const [suite, setSuite] = useState(SUITES[0]!);
  const [motif, setMotif] = useState("");
  const [read, setRead] = useState(false);
  const [msg, setMsg] = useState("");
  const [draft, setDraft] = useState(true);

  return (
    <div className="ws" style={{ gap: 16 }}>
      <div className="rowb">
        <div>
          <h1 style={{ margin: 0, fontSize: 26, fontWeight: 600, letterSpacing: -0.8, color: "var(--navy)" }}>Un échange pour éclairer la suite</h1>
          <p className="p-muted" style={{ margin: "6px 0 0", fontSize: 12.5, color: "var(--muted3)" }}>Entretiens / Fatma Kchaou · Jeudi 09 juillet 2026 · Heure de Tunis (UTC+1)</p>
        </div>
        <Link className="b" to="/equipe/planning">Retour aux entretiens <Icon name="left" size={14} /></Link>
      </div>

      <div className="panel" style={{ flexDirection: "row", alignItems: "center", justifyContent: "space-between", flexWrap: "wrap", gap: 16 }}>
        <div className="rowg" style={{ gap: 14, flexWrap: "nowrap" }}>
          <span className="avatar">FK</span>
          <div className="kvx"><b style={{ fontSize: 20, fontWeight: 600 }}>Fatma Kchaou</b><small>SC-2026-0426 · Sfax · Licence en informatique, IIT</small></div>
        </div>
        <div className="rowg" style={{ gap: 16 }}>
          <div className="kvx" style={{ textAlign: "right" }}><b>10:00 – 10:30 · Visioconférence</b><small>Avec Amira Mansour · Service admissions IIT</small></div>
          <span className="chip2 hl line">Entretien confirmé</span>
          <button className="b dark" style={{ borderRadius: 6 }} onClick={() => setMsg("Ouverture de la visioconférence : lien indisponible dans la démonstration.")}>Ouvrir la visioconférence <Icon name="msg" size={14} color="#fff" /></button>
        </div>
      </div>

      <div className="layout">
        <div className="main" style={{ gap: 14 }}>
          <div className="panel" style={{ gap: 12 }}>
            <div className="rowb"><h2>Synthèse de la conversation</h2></div>
            <div className="rowb"><span className="chip2 hl line">Synthèse IA · À relire</span><Link to="/equipe/examen" className="lnk">Voir les échanges →</Link></div>
            <p className="p-body" style={{ fontSize: 13, color: "var(--ink2)" }}>Fatma aime les mathématiques et l’informatique. Elle hésite entre Prépa et Licence, souhaite créer des logiciels et préfère apprendre progressivement sur des projets concrets.</p>
            <div className="grid g3" style={{ gap: 12 }}>
              <div className="kvx"><small>NIVEAU DÉCLARÉ</small><b>Bac mathématiques</b></div>
              <div className="kvx"><small>MOYENNE DÉCLARÉE</small><b>15,20 / 20 · non vérifiée</b></div>
              <div className="kvx"><small>OBJECTIF</small><b>Ingénierie logicielle</b></div>
            </div>
          </div>

          <div className="panel" style={{ gap: 12 }}>
            <h2>Recommandation et avis académique</h2>
            <div><span className="chip2" style={{ background: "#fff4de", color: "#8d6417", border: "1px solid #f3c85b" }}>Validation humaine en attente</span></div>
            <b style={{ fontSize: 13 }}>Préférence candidat : Licence en informatique · IIT</b>
            <p className="p-muted" style={{ fontSize: 12.5 }}>Piste proposée par l’IA : cohérente avec l’envie de coder et une progression pratique. Alternative discutée : Prépa IIT.</p>
            <div className="notice" style={{ borderRadius: 8 }}><Icon name="shield" size={14} color="var(--blue2)" /><span style={{ fontSize: 12.5, color: "var(--ink2)" }}>L’avis académique reste à confirmer. Vérifier les prérequis, le relevé et les possibilités de poursuite en ingénierie, sans passerelle garantie.</span></div>
            <p className="small" style={{ fontSize: 11 }}>Documentation IIT · à vérifier · Aucune décision d’admission à ce stade.</p>
          </div>

          <div className="panel" style={{ gap: 12 }}>
            <h2>Points à aborder pendant l’échange</h2>
            {POINTS.map((p, i) => (
              <label key={p} className={`cbx ${done[i] ? "on" : ""}`} style={{ fontSize: 12.5, alignItems: "flex-start" }}>
                <input type="checkbox" checked={done[i]} onChange={() => setDone(done.map((d, j) => (j === i ? !d : d)))} /><i>{done[i] && <Icon name="check" size={12} color="#fff" />}</i>{p}
              </label>
            ))}
          </div>

          <div className="panel" style={{ gap: 12 }}>
            <div className="rowb"><div><h2>Notes d’entretien</h2><small className="small" style={{ fontSize: 11 }}>Notes internes · Équipe autorisée uniquement</small></div><span className="chip2 hl line">{draft ? "Brouillon" : "Enregistré"}</span></div>
            <label className="fld" style={{ fontSize: 12 }}>Préparation / observations<textarea rows={3} value={prep} onChange={(e) => { setPrep(e.target.value); setDraft(true); }} /></label>
            <label className="fld" style={{ fontSize: 12 }}>Compte rendu de l’entretien<textarea rows={3} value={cr} onChange={(e) => { setCr(e.target.value); setDraft(true); }} placeholder="À compléter pendant l’échange : motivation, acquis, questions du candidat et points restant à vérifier…" /></label>
            <div><button className="b" style={{ fontSize: 12.5 }} onClick={() => { setDraft(false); setMsg("Notes enregistrées (démonstration)."); }}>Enregistrer les notes <Icon name="save" size={14} /></button></div>
          </div>
        </div>

        <aside className="side" style={{ width: 360, gap: 14 }}>
          <div className="panel" style={{ gap: 10 }}>
            <div className="rowb"><h2>QCM · Terminé le 07 juillet</h2></div>
            <div className="rowb"><b style={{ fontSize: 28, color: "var(--ink2)" }}>9 / 12</b><span className="chip2 hl">Repère pédagogique</span></div>
            {[["Logique & algorithmique", 4, 5], ["Mathématiques", 3, 4], ["Culture numérique", 2, 3]].map(([n, g, t]) => (
              <div key={n as string} className="col" style={{ gap: 6 }}><div className="rowb" style={{ fontSize: 12.5 }}><span>{n}</span><span>{g} / {t}</span></div><div className="hbar"><i style={{ width: `${((g as number) / (t as number)) * 100}%` }} /></div></div>
            ))}
            <p className="small" style={{ fontSize: 11 }}>Score illustratif · Ne vaut pas admission</p>
          </div>

          <div className="panel tint" style={{ borderRadius: 12, gap: 10 }}>
            <h2 style={{ fontSize: 16 }}>Issue de l’entretien</h2>
            <p className="p-muted" style={{ fontSize: 12 }}>À renseigner par Amira Mansour après échange. Aucun résultat n’a encore été enregistré.</p>
            <label className="fld" style={{ fontSize: 12 }}>Suite proposée<select className="sel" value={suite} onChange={(e) => setSuite(e.target.value)}>{SUITES.map((s) => <option key={s}>{s}</option>)}</select></label>
            <label className="fld" style={{ fontSize: 12 }}>Motif / éléments à vérifier<textarea rows={3} value={motif} onChange={(e) => setMotif(e.target.value)} placeholder="Ajouter une justification avant de transmettre le compte rendu…" /></label>
            <button className="b" style={{ fontSize: 12.5, alignSelf: "flex-start" }} onClick={() => setSuite(SUITES[1]!)}>Avis favorable à l’étude</button>
            <button className="b" style={{ fontSize: 12.5, alignSelf: "flex-start" }} onClick={() => setSuite(SUITES[2]!)}>Proposer une autre orientation</button>
            <button className="b" style={{ fontSize: 12.5, alignSelf: "flex-start" }} onClick={() => setSuite(SUITES[3]!)}>Demander une pièce <Icon name="file" size={13} /></button>
            <hr className="hr" />
            <label className={`cbx ${read ? "on" : ""}`} style={{ fontSize: 12 }}><input type="checkbox" checked={read} onChange={() => setRead(!read)} /><i>{read && <Icon name="check" size={12} color="#fff" />}</i>J’ai relu le compte rendu et vérifié la suite proposée.</label>
            <button className="b dark" style={{ fontSize: 12.5, alignSelf: "flex-start", borderRadius: 8 }} disabled={!read || (suite !== SUITES[0] && !motif.trim() && false)} onClick={() => setMsg(`Compte rendu transmis · suite : ${suite}. (démonstration, aucune décision d’admission)`)}>Transmettre le compte rendu <Icon name="right" size={13} color="#fff" /></button>
            <p className="small" style={{ fontSize: 11 }}>La transmission sera tracée. L’avis d’entretien ne constitue pas une admission officielle.</p>
          </div>

          <div className="panel" style={{ gap: 10 }}>
            <h2 style={{ fontSize: 16 }}>Documents du dossier</h2>
            <div className="rowg" style={{ gap: 10, flexWrap: "nowrap" }}><Icon name="file" size={16} /><div className="kvx"><b style={{ fontSize: 12.5 }}>Document candidat (1)</b><small>Contenu et conformité à vérifier.</small></div></div>
            <button className="b" style={{ fontSize: 12.5, alignSelf: "flex-start" }} onClick={() => setMsg("Consultation des documents : aperçu indisponible dans la démonstration.")}>Consulter les documents</button>
          </div>
        </aside>
      </div>
      {msg && <p className="okbox" role="status">{msg}</p>}
      <div className="notice" style={{ borderRadius: 9 }}><Icon name="shield" size={15} color="var(--blue2)" /><span style={{ fontSize: 12.5, color: "var(--ink2)" }}>Validation humaine obligatoire avant toute décision d’admission. Le compte rendu documente l’échange ; l’établissement garde la décision finale.</span></div>
    </div>
  );
}
