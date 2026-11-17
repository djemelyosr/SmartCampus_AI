import { useEffect, useState } from "react";
import { Link, Navigate, useNavigate, useParams } from "react-router-dom";
import Journey from "../components/Journey";
import { FORMATIONS } from "../lib/catalog";
import { api, type ProgramCatalog } from "../lib/api";
import { useAuth } from "../lib/auth";
import arrowLeft from "../assets/arrow-left.svg";
import profileSpark from "../assets/profile-spark.svg";
import codeXml from "../assets/code-xml.svg";
import calculator from "../assets/calculator.svg";
import users from "../assets/users.svg";
import arrowRight from "../assets/arrow-right.svg";
import compareIcon from "../assets/icon-compare.svg";

const SKILLS = [
  { icon: codeXml, t: "Créer et expérimenter", d: "Écrire, tester et améliorer un programme." },
  { icon: calculator, t: "Raisonner avec méthode", d: "Décomposer un problème et expliquer une solution." },
  { icon: users, t: "Apprendre par les projets", d: "Collaborer et présenter un travail concret." },
];

const KIND_LABEL: Record<string, string> = {
  diploma: "Diplôme", average: "Moyenne", document: "Document", exam: "Épreuve", language: "Langue", age: "Âge", other: "Autre",
};

const PERIOD_LABEL: Record<string, string> = { annual: "par an", semester: "par semestre", one_time: "paiement unique" };
const METHOD_LABEL: Record<string, string> = {
  bank_transfer: "Virement bancaire", cash: "Espèces", cheque: "Chèque", card: "Carte bancaire", online: "Paiement en ligne", other: "Autre mode",
};
const fr = (d: string | null) => (d ? new Date(`${d}T00:00:00`).toLocaleDateString("fr-FR") : "");
const until = (d: string | null) => (d ? `Valable jusqu’au ${fr(d)}` : "");
const money = (n: number, cur: string) => `${new Intl.NumberFormat("fr-FR", { maximumFractionDigits: 2 }).format(n)} ${cur}`;

const num = (v: number | null) => (v === null || v === undefined ? "–" : String(v));

export default function Fiche() {
  const { id } = useParams();
  const nav = useNavigate();
  const { user } = useAuth();
  const f = FORMATIONS.find((x) => x.id === id);

  const [cat, setCat] = useState<ProgramCatalog | null>(null);
  const [catError, setCatError] = useState(false);
  const [spec, setSpec] = useState<number | "all">("all");
  const pid = f ? Number(f.id) : NaN;

  useEffect(() => {
    if (!Number.isFinite(pid)) return;
    let alive = true;
    setCat(null);
    setCatError(false);
    setSpec("all");
    api.programCatalog(pid).then((c) => alive && setCat(c)).catch(() => alive && setCatError(true));
    return () => { alive = false; };
  }, [pid]);

  if (!f) return <Navigate to="/formations" replace />;

  const specs = cat?.specialties ?? [];
  const inScope = (sid: number | null) => spec === "all" || sid === null || sid === spec;
  const curricula = (cat?.curricula ?? []).filter((c) => inScope(c.specialty_id));
  const conditions = (cat?.conditions ?? []).filter((c) => inScope(c.specialty_id));
  const fees = (cat?.fees ?? []).filter((t) => inScope(t.specialty_id));
  const paymentTerms = (cat?.paymentTerms ?? []).filter((t) => inScope(t.specialty_id));
  const subjectsOf = (cid: number) =>
    (cat?.subjects ?? []).filter((s) => s.curriculum_id === cid).sort((a, b) => (a.semester ?? 99) - (b.semester ?? 99) || a.name.localeCompare(b.name));
  const specName = (sid: number | null) => specs.find((s) => s.id === sid)?.name;
  const countFor = (sid: number) => (cat?.curricula ?? []).filter((c) => c.specialty_id === sid).flatMap((c) => subjectsOf(c.id)).length;
  const sibling = FORMATIONS.find((x) => x.institution === f.institution && x.level === "Prépa" && x.id !== f.id);
  const compareTo = sibling ? `/comparaison?ids=${f.id},${sibling.id}` : `/comparaison?ids=${f.id}`;
  const loading = cat === null && !catError;

  return (
    <div className="ws" style={{ gap: 22 }}>
      <div className="rowb">
        <div>
          <h1 style={{ margin: 0, fontSize: 28, fontWeight: 600, letterSpacing: -0.8, color: "var(--ink2)" }}>{f.name}</h1>
          <p className="p-muted" style={{ margin: "6px 0 0", fontSize: 14 }}>Mes formations / Catalogue / {f.name} · {f.institution}</p>
        </div>
        <Link className="b" to="/formations">Retour au catalogue <img src={arrowLeft} alt="" /></Link>
      </div>

      <Journey current={2} />

      <section className="hero-dark">
        <div className="ov">
          <div className="rowg" style={{ gap: 8 }}>
            <span className="chip2 hl">{f.institution}</span>
            <span className="chip2 hl">{f.level}{f.duration ? ` · ${f.duration} an${f.duration > 1 ? "s" : ""}` : ""}</span>
          </div>
          <h2>{f.tagline}</h2>
          <p>{f.keywords ? `Débouchés : ${f.keywords}.` : `Découvrez les spécialités, matières et conditions d’accès de ${f.institution}.`}</p>
        </div>
        <aside className="aff">
          <img src={profileSpark} alt="" width={24} height={24} />
          <b>En lien avec votre profil</b>
          <p>Maths, informatique et apprentissage progressif : des points à explorer ensemble.</p>
          <small>Affinité indicative · Pas une admission</small>
        </aside>
      </section>

      <div className="detail">
        <div className="l">
          <div className="panel">
            <h2>Ce que vous pourriez explorer</h2>
            <p className="p-body" style={{ fontSize: 14, color: "var(--ink2)" }}>
              Une approche pédagogique envisagée autour de la programmation, de la logique et de la résolution de problèmes. Le contenu officiel et l’organisation sont à confirmer avec {f.institution}.
            </p>
            <div className="grid g3" style={{ gap: 16 }}>
              {SKILLS.map((s) => (
                <div className="skill" key={s.t}><img src={s.icon} alt="" /><b>{s.t}</b><span>{s.d}</span></div>
              ))}
            </div>
          </div>

          <div className="panel">
            <div className="rowb">
              <h2>Spécialités</h2>
              {specs.length > 0 && <span className="chip2 hl">{specs.length} spécialité{specs.length > 1 ? "s" : ""}</span>}
            </div>
            {loading && <p className="p-muted">Chargement des spécialités…</p>}
            {catError && <p className="p-muted">Les spécialités sont momentanément indisponibles. Réessayez plus tard.</p>}
            {cat && specs.length === 0 && <p className="p-muted">Aucune spécialité n’est publiée pour cette formation : le parcours est commun.</p>}
            {specs.length > 0 && (
              <>
                <div className="rowg" style={{ gap: 8 }}>
                  <button type="button" className={`chip2 btn ${spec === "all" ? "hl" : "line"}`} onClick={() => setSpec("all")}>Toutes</button>
                  {specs.map((s) => (
                    <button type="button" key={s.id} className={`chip2 btn ${spec === s.id ? "hl" : "line"}`} onClick={() => setSpec(s.id)}>{s.name}</button>
                  ))}
                </div>
                <div className="grid g2" style={{ gap: 16 }}>
                  {specs.filter((s) => spec === "all" || s.id === spec).map((s) => (
                    <div className="skill" key={s.id}>
                      <b>{s.name}</b>
                      <span>{s.description || "Description à venir."}</span>
                      <small className="small">{countFor(s.id)} matière{countFor(s.id) > 1 ? "s" : ""} propre{countFor(s.id) > 1 ? "s" : ""} à cette spécialité</small>
                    </div>
                  ))}
                </div>
              </>
            )}
          </div>

          <div className="panel">
            <div className="rowb">
              <h2>Matières</h2>
              {cat && <span className="chip2 hl">{curricula.reduce((n, c) => n + subjectsOf(c.id).length, 0)} matières</span>}
            </div>
            {loading && <p className="p-muted">Chargement des matières…</p>}
            {cat && curricula.length === 0 && <p className="p-muted">Le programme détaillé de cette formation n’est pas encore publié.</p>}
            {curricula.map((c) => {
              const subs = subjectsOf(c.id);
              return (
                <div key={c.id} className="cur">
                  <div className="rowb">
                    <b style={{ color: "var(--ink2)", fontSize: 14 }}>{c.name}</b>
                    <span className="rowg" style={{ gap: 6 }}>
                      {c.academic_year && <span className="chip2 line">{c.academic_year}</span>}
                      <span className="chip2 hl">{specName(c.specialty_id) ?? "Tronc commun"}</span>
                    </span>
                  </div>
                  {c.description && <p className="small">{c.description}</p>}
                  {subs.length === 0 ? (
                    <p className="p-muted">Aucune matière publiée pour ce programme.</p>
                  ) : (
                    <div className="subj-wrap">
                      <div className="subj head"><span>Matière</span><span>Sem.</span><span>Crédits</span><span>Coef.</span><span>Heures</span></div>
                      {subs.map((s) => (
                        <div className="subj" key={s.id} title={s.description || undefined}>
                          <span>{s.code ? <small className="small">{s.code} · </small> : null}{s.name}</span>
                          <span>{num(s.semester)}</span><span>{num(s.credits)}</span><span>{num(s.coefficient)}</span><span>{num(s.hours)}</span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              );
            })}
          </div>

          <div className="panel">
            <div className="rowb">
              <h2>Conditions d’admission</h2>
              {conditions.length > 0
                ? <span className="chip2 ok">Officielles · en vigueur</span>
                : <span className="chip2 warn" style={{ background: "#fff4de", color: "#8d6417" }}>À confirmer</span>}
            </div>
            {f.admission && <p className="p-body" style={{ color: "var(--ink2)" }}>{f.admission}</p>}
            {loading && <p className="p-muted">Chargement des conditions…</p>}
            {cat && conditions.length === 0 && <p className="p-muted">Aucune condition détaillée n’est publiée. Échangez avec l’établissement.</p>}
            {conditions.map((c) => (
              <div className="chk" key={c.id}>
                <div className="rowb">
                  <b>{c.title}</b>
                  <span className="rowg" style={{ gap: 6 }}>
                    <span className="chip2 line">{KIND_LABEL[c.kind] ?? "Autre"}</span>
                    {c.threshold !== null && <span className="chip2 line">Seuil : {c.threshold}</span>}
                    <span className={`chip2 ${c.required ? "bad" : "ok"}`}>{c.required ? "Obligatoire" : "Souhaité"}</span>
                    {c.specialty_id !== null && <span className="chip2 hl">{specName(c.specialty_id)}</span>}
                    {c.valid_until && <span className="chip2 line">{until(c.valid_until)}</span>}
                  </span>
                </div>
                {c.description && <span>{c.description}</span>}
              </div>
            ))}
            <p className="small">Des repères pour réfléchir, pas des critères d’éligibilité définitifs.</p>
          </div>

          <div className="panel">
            <div className="rowb">
              <h2>Tarifs</h2>
              {fees.length > 0 && <span className="chip2 ok">Officiels · en vigueur</span>}
            </div>
            {loading && <p className="p-muted">Chargement des tarifs…</p>}
            {cat && fees.length === 0 && <p className="p-muted">Les tarifs ne sont pas encore publiés. Renseignez-vous auprès de l’établissement.</p>}
            {fees.map((t) => (
              <div className="chk" key={t.id}>
                <div className="rowb">
                  <b>{t.label}</b>
                  <span className="rowg" style={{ gap: 6 }}>
                    {t.specialty_id !== null && <span className="chip2 hl">{specName(t.specialty_id)}</span>}
                    <span className="chip2 line">{PERIOD_LABEL[t.period] ?? t.period}</span>
                    {t.valid_until && <span className="chip2 line">{until(t.valid_until)}</span>}
                    <span className="chip2 ok">{money(t.amount, t.currency)}</span>
                  </span>
                </div>
                {t.description && <span>{t.description}</span>}
              </div>
            ))}
            <p className="small">Tarifs publiés par {f.institution}{cat ? ` et en vigueur au ${fr(cat.asOf)}` : ""}. En cas de doute, confirmez auprès de l’établissement.</p>
          </div>

          <div className="panel">
            <div className="rowb">
              <h2>Modalités de paiement</h2>
              {paymentTerms.length > 0 && <span className="chip2 ok">Officielles · en vigueur</span>}
            </div>
            {loading && <p className="p-muted">Chargement des modalités…</p>}
            {cat && paymentTerms.length === 0 && <p className="p-muted">Les modalités de paiement ne sont pas encore publiées. Renseignez-vous auprès de l’établissement.</p>}
            {paymentTerms.map((t) => (
              <div className="chk" key={t.id}>
                <div className="rowb">
                  <b>{t.title}</b>
                  <span className="rowg" style={{ gap: 6 }}>
                    {t.specialty_id !== null && <span className="chip2 hl">{specName(t.specialty_id)}</span>}
                    <span className="chip2 line">{METHOD_LABEL[t.method] ?? t.method}</span>
                    {t.installments > 1 && <span className="chip2 line">{t.installments} versements</span>}
                    {t.down_payment_percent !== null && <span className="chip2 line">Acompte {t.down_payment_percent} %</span>}
                    {t.due_date && <span className="chip2 warn">Avant le {fr(t.due_date)}</span>}
                    {t.valid_until && <span className="chip2 line">{until(t.valid_until)}</span>}
                  </span>
                </div>
                {t.description && <span>{t.description}</span>}
              </div>
            ))}
          </div>

          <div className="grid g2">
            <div className="panel">
              <h2>Cette piste vous parle si…</h2>
              <div className="p-body" style={{ color: "var(--ink2)" }}>
                • Vous aimez les maths et l’informatique.<br />• Vous avez envie de créer des logiciels.<br />• Vous préférez avancer par la pratique.
              </div>
              <p className="small">Des repères pour réfléchir, pas des critères d’éligibilité.</p>
            </div>
            <div className="panel">
              <h2>Des perspectives à explorer</h2>
              <p className="p-body" style={{ color: "var(--ink2)" }}>{f.keywords || "Développement logiciel, projets numériques et poursuite d’études selon votre parcours."}</p>
              <p className="small">Débouchés indicatifs. Aucune promesse d’emploi ni de passerelle vers l’ingénierie.</p>
            </div>
          </div>

          <div className="panel">
            <h2>Informations à vérifier</h2>
            {[
              ...(paymentTerms.length > 0 ? [] : [["Organisation et paiement", "Calendrier et modalités de paiement à confirmer auprès de l’établissement."]]),
              ["Poursuite en ingénierie", "Possibilités à étudier selon le dossier, sans passerelle garantie."],
            ].map(([t, d]) => (
              <div className="chk" key={t}><b>{t}</b><span>{d}</span></div>
            ))}
          </div>
        </div>

        <div className="r">
          <div className="panel tint">
            <h2>Votre prochaine étape</h2>
            <div><span className="chip2 hl">{f.institution} · Parcours à explorer</span></div>
            <p className="big">Une préférence,<br />pas un engagement définitif.</p>
            <p className="p-body" style={{ fontSize: 14, color: "var(--ink2)" }}>
              Pour transmettre votre préinscription, créez un compte ou connectez-vous. Votre choix ne vaut pas admission.
            </p>
            <div><button className="b pri" style={{ borderRadius: 9 }} onClick={() => nav(user ? `/preinscription?formation=${f.id}` : "/inscription")}>Me pré-inscrire <img src={arrowRight} alt="" /></button></div>
            <div><Link className="b" to={`/comparaison?ids=${f.id}`}>Ajouter à ma comparaison <img src={compareIcon} alt="" /></Link></div>
            <p className="small">Rentrée visée : septembre 2026 · Campagne démo</p>
          </div>
          {f.level !== "Prépa" && sibling && (
            <div className="panel">
              <h2>Et la Prépa ?</h2>
              <p className="p-body" style={{ color: "var(--ink2)" }}>Le cycle préparatoire est une autre piste si vous souhaitez approfondir vos bases scientifiques avant de vous spécialiser.</p>
              <div><Link className="b" to={compareTo}>Comparer avec {sibling.name}</Link></div>
            </div>
          )}
          <div className="panel">
            <h2>Une question sur ce parcours ?</h2>
            <p className="p-body" style={{ color: "var(--ink2)" }}>Un conseiller peut vous aider à vérifier les conditions d’accès, le rythme et les poursuites possibles.</p>
            <div><a className="b" href="mailto:admissions@iit.example">Contacter un conseiller</a></div>
            <hr className="hr" />
            <p className="small">Documentation {f.institution} · à vérifier<br />Informations publiées par les responsables académiques.</p>
          </div>
        </div>
      </div>
    </div>
  );
}
