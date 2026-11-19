import { useEffect, useMemo, useState, type FormEvent } from "react";
import Icon from "./Icon";
import { api, ApiError, type CatalogResource, type CatalogRow, type OfficialAction } from "../lib/api";

/** Catalogue management (SmartCampus.pdf §3): formations, specialties, teaching programmes, subjects, admission conditions.
 *  An academic head (`scope`) only changes their own institution; the administrator (no scope) changes everything. */
type Inst = "IIT" | "ISB";
type Opt = [string, string];
type FilterKey = "institution" | "program_id" | "curriculum_id" | "level" | "kind" | "semester" | "status" | "validity";
interface F {
  k: string; label: string; t: "text" | "area" | "num" | "sel" | "bool" | "list" | "ref" | "date";
  req?: boolean; opts?: Opt[]; ref?: "programs" | "specialties" | "curricula" | "fees"; once?: boolean; half?: boolean; hint?: string; step?: string; min?: string;
}
interface Refs { programs: CatalogRow[]; specialties: CatalogRow[]; curricula: CatalogRow[]; fees: CatalogRow[] }
interface X { prog: (id?: number | null) => string; spec: (id?: number | null) => string; cur: (id?: number | null) => string }
interface Ent {
  key: CatalogResource; label: string; one: string; cols: [string, string, string]; fields: F[]; filters: FilterKey[]; cascade?: string; official?: boolean;
  title: (r: CatalogRow, x: X) => string; sub: (r: CatalogRow, x: X) => string; mid: (r: CatalogRow) => string;
}

const INST: Opt[] = [["IIT", "IIT"], ["ISB", "ISB"]];
const LEVELS: Opt[] = [["licence", "Licence"], ["prepa", "Préparatoire"], ["ingenierie", "Ingénierie"], ["other", "Autre"]];
const KINDS: Opt[] = [["diploma", "Diplôme"], ["average", "Moyenne"], ["document", "Document"], ["exam", "Concours / test"], ["language", "Langue"], ["age", "Âge"], ["other", "Autre"]];
const PERIODS: Opt[] = [["annual", "Par an"], ["semester", "Par semestre"], ["one_time", "Paiement unique"]];
const money = (n: number) => new Intl.NumberFormat("fr-FR", { maximumFractionDigits: 2 }).format(n);
const SEMESTERS: Opt[] = Array.from({ length: 10 }, (_, i): Opt => [String(i + 1), `Semestre ${i + 1}`]);
const label = (o: Opt[], v: string) => o.find(([k]) => k === v)?.[1] ?? v;
const METHODS: Opt[] = [["bank_transfer", "Virement bancaire"], ["cash", "Espèces"], ["cheque", "Chèque"], ["card", "Carte bancaire"], ["online", "Paiement en ligne"], ["other", "Autre"]];
const STATUSES: Opt[] = [["draft", "Brouillon"], ["published", "Publié"], ["archived", "Archivé"]];
const VALIDITIES: Opt[] = [["current", "En vigueur"], ["upcoming", "À venir"], ["expired", "Expirés"]];

// Official information (fees, payment terms, admission conditions): a status and a validity period decide what candidates
// and the AI agent can see. Dates are calendar days in Tunisia, like on the server.
const todayTn = () => new Intl.DateTimeFormat("en-CA", { timeZone: "Africa/Tunis" }).format(new Date());
const fr = (d: string | null | undefined) => (d ? new Date(`${d}T00:00:00`).toLocaleDateString("fr-FR") : "");
/** What this item is right now for candidates and the agent: [label, chip class]. */
function badge(r: CatalogRow): [string, string] {
  if (r.status === "draft") return ["Brouillon", "warn"];
  if (r.status === "archived") return ["Archivé", "line"];
  if (!r.active) return ["Désactivé", "bad"];
  const t = todayTn();
  if (r.valid_from && r.valid_from > t) return ["À venir", "hl"];
  if (r.valid_until && r.valid_until < t) return ["Expiré", "bad"];
  return ["En vigueur", "ok"];
}
const validityText = (r: CatalogRow) =>
  r.valid_from && r.valid_until ? `Du ${fr(r.valid_from)} au ${fr(r.valid_until)}` : r.valid_from ? `Depuis le ${fr(r.valid_from)}` : r.valid_until ? `Jusqu’au ${fr(r.valid_until)}` : "Sans limite de date";
const VALIDITY_FIELDS: F[] = [
  { k: "valid_from", label: "Valable à partir du", t: "date", half: true, hint: "Vide = déjà valable." },
  { k: "valid_until", label: "Valable jusqu’au", t: "date", half: true, hint: "Vide = sans fin." },
  { k: "academic_year", label: "Année universitaire", t: "text", hint: "Indicatif, format 2026-2027." },
];

const ENTS: Ent[] = [
  {
    key: "programs", label: "Formations", one: "formation", cols: ["Formation", "Durée", "État"], filters: ["institution", "level"],
    cascade: "Supprime aussi ses spécialités, programmes pédagogiques, matières et conditions d’admission.",
    fields: [
      { k: "name", label: "Intitulé de la formation", t: "text", req: true },
      { k: "institution", label: "Établissement", t: "sel", opts: INST, req: true, half: true },
      { k: "level", label: "Niveau", t: "sel", opts: LEVELS, req: true, half: true },
      { k: "description", label: "Présentation", t: "area" },
      { k: "admission_requirements", label: "Conditions d’accès (texte de présentation)", t: "area", hint: "Le détail se saisit dans l’onglet « Conditions d’admission »." },
      { k: "duration_years", label: "Durée (années)", t: "num" },
      { k: "career_outcomes", label: "Débouchés", t: "list", hint: "Séparés par des virgules." },
      { k: "active", label: "Formation active (visible des candidats)", t: "bool" },
    ],
    title: (r) => r.name, sub: (r) => `${r.institution} · ${label(LEVELS, r.level)}`, mid: (r) => (r.duration_years ? `${r.duration_years} an${r.duration_years > 1 ? "s" : ""}` : "—"),
  },
  {
    key: "specialties", label: "Spécialités", one: "spécialité", cols: ["Spécialité", "Établissement", "État"], filters: ["institution", "program_id"],
    cascade: "Supprime aussi ses programmes pédagogiques (et leurs matières) et ses conditions d’admission.",
    fields: [
      { k: "program_id", label: "Formation", t: "ref", ref: "programs", req: true, once: true },
      { k: "name", label: "Nom de la spécialité", t: "text", req: true },
      { k: "description", label: "Description", t: "area" },
      { k: "active", label: "Spécialité active", t: "bool" },
    ],
    title: (r) => r.name, sub: (r, x) => x.prog(r.program_id), mid: () => "",
  },
  {
    key: "curricula", label: "Programmes pédagogiques", one: "programme pédagogique", cols: ["Programme", "Année", "État"], filters: ["institution", "program_id"],
    cascade: "Supprime aussi toutes ses matières.",
    fields: [
      { k: "program_id", label: "Formation", t: "ref", ref: "programs", req: true, once: true },
      { k: "specialty_id", label: "Spécialité (optionnel)", t: "ref", ref: "specialties", hint: "Laisser vide pour un programme commun à toute la formation." },
      { k: "name", label: "Intitulé du programme", t: "text", req: true },
      { k: "academic_year", label: "Année universitaire", t: "text", hint: "Format 2026-2027." },
      { k: "description", label: "Description", t: "area" },
      { k: "active", label: "Programme actif", t: "bool" },
    ],
    title: (r) => r.name, sub: (r, x) => x.prog(r.program_id) + (r.specialty_id ? ` · ${x.spec(r.specialty_id)}` : ""), mid: (r) => r.academic_year || "—",
  },
  {
    key: "subjects", label: "Matières", one: "matière", cols: ["Matière", "Semestre · crédits", "État"], filters: ["institution", "program_id", "curriculum_id", "semester"],
    fields: [
      { k: "curriculum_id", label: "Programme pédagogique", t: "ref", ref: "curricula", req: true },
      { k: "name", label: "Intitulé de la matière", t: "text", req: true },
      { k: "code", label: "Code", t: "text", half: true },
      { k: "semester", label: "Semestre (1-12)", t: "num", half: true },
      { k: "credits", label: "Crédits", t: "num", half: true },
      { k: "coefficient", label: "Coefficient", t: "num", step: "0.5", half: true },
      { k: "hours", label: "Volume horaire (h)", t: "num" },
      { k: "description", label: "Contenu", t: "area" },
      { k: "active", label: "Matière active", t: "bool" },
    ],
    title: (r) => r.name, sub: (r, x) => (r.code ? `${r.code} · ` : "") + x.cur(r.curriculum_id),
    mid: (r) => [r.semester ? `S${r.semester}` : "", r.credits != null ? `${r.credits} crédits` : ""].filter(Boolean).join(" · ") || "—",
  },
  {
    key: "admission-conditions", label: "Conditions d’admission", one: "condition d’admission", cols: ["Condition", "Type", "Statut"], filters: ["institution", "program_id", "kind", "status", "validity"], official: true,
    fields: [
      { k: "program_id", label: "Formation", t: "ref", ref: "programs", req: true, once: true },
      { k: "specialty_id", label: "Spécialité (optionnel)", t: "ref", ref: "specialties", hint: "Laisser vide pour une condition valable pour toute la formation." },
      { k: "kind", label: "Type de condition", t: "sel", opts: KINDS, req: true },
      { k: "title", label: "Intitulé", t: "text", req: true },
      { k: "description", label: "Détail", t: "area" },
      { k: "threshold", label: "Seuil (ex. moyenne minimale)", t: "num", step: "0.01" },
      { k: "required", label: "Condition obligatoire", t: "bool" },
      ...VALIDITY_FIELDS,
      { k: "active", label: "Condition active", t: "bool" },
    ],
    title: (r) => r.title, sub: (r, x) => x.prog(r.program_id) + (r.specialty_id ? ` · ${x.spec(r.specialty_id)}` : ""),
    mid: (r) => label(KINDS, r.kind) + (r.threshold != null ? ` ≥ ${r.threshold}` : "") + (r.required ? "" : " (facultatif)"),
  },
  {
    key: "fees", label: "Frais de scolarité", one: "tarif", cols: ["Tarif", "Montant", "Statut"], filters: ["institution", "program_id", "status", "validity"], official: true,
    fields: [
      { k: "program_id", label: "Formation", t: "ref", ref: "programs", req: true, once: true },
      { k: "specialty_id", label: "Spécialité (optionnel)", t: "ref", ref: "specialties", hint: "Laisser vide pour un tarif valable pour toute la formation." },
      { k: "label", label: "Intitulé du tarif", t: "text", req: true },
      { k: "amount", label: "Montant", t: "num", step: "0.01", req: true, half: true },
      { k: "currency", label: "Devise", t: "text", req: true, half: true, hint: "Code à 3 lettres (TND)." },
      { k: "period", label: "Périodicité", t: "sel", opts: PERIODS, req: true },
      { k: "description", label: "Détail", t: "area" },
      ...VALIDITY_FIELDS,
      { k: "active", label: "Tarif actif", t: "bool" },
    ],
    title: (r) => r.label, sub: (r, x) => x.prog(r.program_id) + (r.specialty_id ? ` · ${x.spec(r.specialty_id)}` : ""),
    mid: (r) => `${money(r.amount)} ${r.currency} · ${label(PERIODS, r.period)}`,
  },
  {
    key: "payment-terms", label: "Modalités de paiement", one: "modalité de paiement", cols: ["Modalité", "Mode", "Statut"], filters: ["institution", "program_id", "status", "validity"], official: true,
    fields: [
      { k: "program_id", label: "Formation", t: "ref", ref: "programs", req: true, once: true },
      { k: "specialty_id", label: "Spécialité (optionnel)", t: "ref", ref: "specialties", hint: "Laisser vide pour une modalité valable pour toute la formation." },
      { k: "fee_id", label: "Tarif concerné (optionnel)", t: "ref", ref: "fees", hint: "Laisser vide si elle s’applique à l’ensemble des frais." },
      { k: "title", label: "Intitulé", t: "text", req: true },
      { k: "method", label: "Mode de paiement", t: "sel", opts: METHODS, req: true },
      { k: "installments", label: "Nombre de versements", t: "num", req: true, half: true, min: "1" },
      { k: "down_payment_percent", label: "Acompte (%)", t: "num", step: "0.5", half: true },
      { k: "due_date", label: "Date limite de paiement", t: "date" },
      { k: "description", label: "Détail", t: "area" },
      ...VALIDITY_FIELDS,
      { k: "active", label: "Modalité active", t: "bool" },
    ],
    title: (r) => r.title, sub: (r, x) => x.prog(r.program_id) + (r.specialty_id ? ` · ${x.spec(r.specialty_id)}` : ""),
    mid: (r) => `${label(METHODS, r.method)} · ${r.installments} versement${r.installments > 1 ? "s" : ""}`,
  },
];

const MSG: [RegExp, string][] = [
  [/already covers this period/i, "Un autre élément publié couvre déjà ces dates (même formation, spécialité et intitulé) : archivez-le ou ajustez les périodes de validité."],
  [/already over/i, "La période de validité est déjà terminée : prolongez la date de fin avant de publier."],
  [/valid_until must not be before/i, "La date de fin précède la date de début."],
  [/fee does not belong/i, "Le tarif choisi n’appartient pas à cette formation."],
  [/pre-registrations/i, "Cette formation est liée à des préinscriptions : désactivez-la plutôt que de la supprimer."],
  [/specialty with that name/i, "Une spécialité porte déjà ce nom dans cette formation."],
  [/fee/i, "Tarif introuvable ou non autorisé pour cet établissement."],
  [/subject with that code/i, "Ce code de matière existe déjà dans ce programme."],
  [/does not belong/i, "La spécialité choisie n’appartient pas à cette formation."],
  [/cannot be null/i, "Un champ obligatoire est vide."],
];
const errText = (e: unknown) => {
  if (e instanceof ApiError) {
    const m = MSG.find(([re]) => re.test(e.message));
    if (m) return m[1];
    if (e.status === 401) return "Session expirée : reconnectez-vous.";
    if (e.status === 403) return "Action réservée au responsable de cet établissement.";
    if (e.status === 404) return "Élément introuvable (peut-être déjà supprimé).";
    if (e.status === 409) return "Cet élément existe déjà.";
    if (e.status === 422) return "Informations invalides : vérifiez les champs (semestre de 1 à 12, année au format 2026-2027…).";
  }
  return "Le serveur est injoignable.";
};

type Form = Record<string, string | boolean>;
const toForm = (ent: Ent, r: CatalogRow): Form =>
  Object.fromEntries(ent.fields.map((f) => [f.k, f.t === "bool" ? !!r[f.k] : f.t === "list" ? (r[f.k] ?? []).join(", ") : r[f.k] == null ? "" : String(r[f.k])]));

/** Builds the request body: on update every editable field is sent (empty optional ones become null). */
function payload(ent: Ent, form: Form, creating: boolean): CatalogRow {
  const out: CatalogRow = {};
  for (const f of ent.fields) {
    if (creating ? f.k === "active" : f.once) continue;
    const v = form[f.k];
    const empty = v === "" || v === undefined;
    if (f.t === "bool") out[f.k] = !!v;
    else if (f.t === "list") out[f.k] = String(v ?? "").split(",").map((s) => s.trim()).filter(Boolean);
    else if (f.t === "num") out[f.k] = empty ? (creating ? undefined : null) : Number(v);
    else if (f.t === "ref") out[f.k] = empty ? (creating ? undefined : null) : Number(v);
    else if (f.t === "date") out[f.k] = empty ? (creating ? undefined : null) : String(v);
    else if (f.k === "code" || f.k === "academic_year") out[f.k] = empty ? (creating ? undefined : null) : String(v).trim();
    else if (f.k === "currency") out[f.k] = String(v ?? "").trim().toUpperCase();
    else out[f.k] = String(v ?? "").trim();
  }
  return out;
}

export default function CatalogueManager({ scope }: { scope?: Inst }) {
  const [tab, setTab] = useState<CatalogResource>("programs");
  const ent = ENTS.find((e) => e.key === tab)!;
  const [q, setQ] = useState("");
  const [filters, setFilters] = useState<Record<string, string>>({});
  const [rows, setRows] = useState<CatalogRow[]>([]);
  const [refs, setRefs] = useState<Refs>({ programs: [], specialties: [], curricula: [], fees: [] });
  const [loading, setLoading] = useState(true);
  const [reload, setReload] = useState(0);
  const [sel, setSel] = useState<number | "new" | null>(null);
  const [form, setForm] = useState<Form>({});
  const [confirmDel, setConfirmDel] = useState(false);
  const [msg, setMsg] = useState("");
  const [err, setErr] = useState("");

  // Parents used by the forms and the labels (all institutions are read, an academic head can only edit their own).
  useEffect(() => {
    Promise.all([api.catalogList("programs"), api.catalogList("specialties"), api.catalogList("curricula"), api.catalogList("fees")])
      .then(([programs, specialties, curricula, fees]) => setRefs({ programs, specialties, curricula, fees }))
      .catch((e) => setErr(errText(e)));
  }, [reload]);

  // Server-side search + filters (debounced).
  useEffect(() => {
    let alive = true;
    const t = setTimeout(() => {
      setLoading(true);
      api.catalogList(ent.key, { q: q.trim(), institution: scope ?? filters.institution, program_id: filters.program_id, curriculum_id: filters.curriculum_id, level: filters.level, kind: filters.kind, semester: filters.semester, status: filters.status, validity: filters.validity })
        .then((r) => { if (alive) setRows(r); })
        .catch((e) => { if (alive) setErr(errText(e)); })
        .finally(() => { if (alive) setLoading(false); });
    }, 250);
    return () => { alive = false; clearTimeout(t); };
  }, [ent.key, q, filters, scope, reload]);

  const x: X = useMemo(() => ({
    prog: (id) => refs.programs.find((p) => p.id === id)?.name ?? "—",
    spec: (id) => refs.specialties.find((s) => s.id === id)?.name ?? "—",
    cur: (id) => refs.curricula.find((c) => c.id === id)?.name ?? "—",
  }), [refs]);
  const instOf = (key: CatalogResource, r: CatalogRow): string | undefined => {
    if (key === "programs") return r.institution;
    const pid = key === "subjects" ? refs.curricula.find((c) => c.id === r.curriculum_id)?.program_id : r.program_id;
    return refs.programs.find((p) => p.id === pid)?.institution;
  };

  const progOpts = refs.programs.filter((p) => !scope || p.institution === scope);
  const options = (f: F): Opt[] => {
    if (f.ref === "programs") return progOpts.map((p): Opt => [String(p.id), `${p.institution} · ${p.name}`]);
    if (f.ref === "fees") return refs.fees.filter((t) => String(t.program_id) === String(form.program_id)).map((t): Opt => [String(t.id), `${t.label} · ${money(t.amount)} ${t.currency}`]);
    if (f.ref === "specialties") return refs.specialties.filter((s) => String(s.program_id) === String(form.program_id)).map((s): Opt => [String(s.id), s.name]);
    return refs.curricula.filter((c) => !scope || instOf("curricula", c) === scope).map((c): Opt => [String(c.id), `${x.prog(c.program_id)} · ${c.name}`]);
  };

  const creating = sel === "new";
  const cur = typeof sel === "number" ? rows.find((r) => r.id === sel) : undefined;
  const readOnly = !!cur && !!scope && instOf(ent.key, cur) !== scope;
  // Unsaved edits: a status action reloads the item from the server, so it is disabled until they are saved.
  const orig = cur ? toForm(ent, cur) : null;
  const dirty = !creating && !!orig && ent.fields.some((f) => !f.once && form[f.k] !== orig[f.k]);
  const grid = ent.official ? "1.6fr 1.1fr .8fr 18px" : "1.8fr 1.1fr .6fr 18px";

  const clear = () => { setMsg(""); setErr(""); setConfirmDel(false); };
  const switchTab = (k: CatalogResource) => { setTab(k); setSel(null); setQ(""); setFilters({}); setRows([]); clear(); };
  const open = (r: CatalogRow) => { setSel(r.id); setForm(toForm(ent, r)); clear(); };
  const startNew = () => {
    const d: Form = {};
    for (const f of ent.fields) d[f.k] = f.t === "bool" ? true : f.t === "sel" ? (f.k === "institution" ? scope ?? f.opts![0][0] : f.opts![0][0]) : f.k === "currency" ? "TND" : f.k === "installments" ? "1" : "";
    if (filters.program_id && ent.fields.some((f) => f.k === "program_id")) d.program_id = filters.program_id;
    if (filters.curriculum_id && ent.fields.some((f) => f.k === "curriculum_id")) d.curriculum_id = filters.curriculum_id;
    setSel("new"); setForm(d); clear();
  };
  const setField = (k: string, v: string | boolean) => setForm((f) => ({ ...f, [k]: v, ...(k === "program_id" ? { specialty_id: "", fee_id: "" } : {}) }));
  const setFilter = (k: string, v: string) => setFilters((f) => ({ ...f, [k]: v, ...(k === "program_id" ? { curriculum_id: "" } : {}) }));

  async function save(e: FormEvent) {
    e.preventDefault(); clear();
    try {
      let body = payload(ent, form, creating);
      if (!creating && orig) {
        // Only what changed is sent: for official items any sent content field sends a published item back to draft.
        body = Object.fromEntries(Object.entries(body).filter(([k]) => form[k] !== orig[k]));
        if (Object.keys(body).length === 0) { setMsg("Aucune modification à enregistrer."); return; }
      }
      const wasPublished = cur?.status === "published";
      const saved = creating ? await api.catalogCreate(ent.key, body) : await api.catalogUpdate(ent.key, sel as number, body);
      setSel(saved.id); setForm(toForm(ent, saved)); setReload((n) => n + 1);
      setMsg(creating
        ? (ent.official ? "Brouillon créé : publiez-le pour le rendre visible des candidats et de l’agent IA." : "Élément ajouté.")
        : wasPublished && saved.status === "draft" ? "Modifications enregistrées. L’élément est repassé en brouillon : republiez-le pour qu’il soit de nouveau visible."
        : "Modifications enregistrées.");
    } catch (e2) { setErr(errText(e2)); }
  }
  /** Publication workflow (publish / archive / back to draft) of an official item. */
  async function act(action: OfficialAction) {
    if (typeof sel !== "number") return;
    clear();
    try {
      const saved = await api.catalogAction(ent.key, sel, action);
      setForm(toForm(ent, saved)); setReload((n) => n + 1);
      setMsg(action === "publish" ? "Publié : visible des candidats et de l’agent IA pendant sa période de validité."
        : action === "archive" ? "Archivé : n’est plus visible, conservé pour l’historique." : "Repassé en brouillon : n’est plus visible.");
    } catch (e2) { setErr(errText(e2)); }
  }
  async function remove() {
    if (typeof sel !== "number") return;
    clear();
    try {
      await api.catalogDelete(ent.key, sel);
      setSel(null); setReload((n) => n + 1); setMsg("Élément supprimé.");
    } catch (e) { setErr(errText(e)); }
  }

  const FILTER_UI: Record<FilterKey, { all: string; opts: () => Opt[] }> = {
    institution: { all: "Tous les établissements", opts: () => INST },
    program_id: { all: "Toutes les formations", opts: () => progOpts.map((p): Opt => [String(p.id), p.name]) },
    curriculum_id: { all: "Tous les programmes", opts: () => refs.curricula.filter((c) => !filters.program_id || String(c.program_id) === filters.program_id).map((c): Opt => [String(c.id), c.name]) },
    level: { all: "Tous les niveaux", opts: () => LEVELS },
    kind: { all: "Tous les types", opts: () => KINDS },
    semester: { all: "Tous les semestres", opts: () => SEMESTERS },
    status: { all: "Tous les statuts", opts: () => STATUSES },
    validity: { all: "Toutes les périodes", opts: () => VALIDITIES },
  };

  const groups: F[][] = [];
  for (const f of ent.fields) {
    if (creating && f.k === "active") continue;
    const last = groups[groups.length - 1];
    if (f.half && last && last.length === 1 && last[0].half) last.push(f); else groups.push([f]);
  }
  const control = (f: F) => {
    const v = form[f.k];
    if (f.t === "bool") return (
      <label key={f.k} className={`cbx ${v ? "on" : ""}`} style={{ fontSize: 12.5 }}>
        <input type="checkbox" checked={!!v} onChange={() => setField(f.k, !v)} /><i>{v && <Icon name="check" size={12} color="#fff" />}</i>{f.label}
      </label>
    );
    return (
      <label key={f.k} className="fld" style={{ fontSize: 12 }}>{f.label}{f.req ? " *" : ""}
        {f.t === "area" ? <textarea rows={3} value={String(v ?? "")} onChange={(e) => setField(f.k, e.target.value)} />
          : f.t === "num" ? <input type="number" min={f.min ?? 0} step={f.step ?? "1"} required={f.req} value={String(v ?? "")} onChange={(e) => setField(f.k, e.target.value)} />
          : f.t === "date" ? <input type="date" value={String(v ?? "")} onChange={(e) => setField(f.k, e.target.value)} />
          : f.t === "sel" || f.t === "ref" ? (
            <select required={f.req} disabled={!creating && f.once} value={String(v ?? "")} onChange={(e) => setField(f.k, e.target.value)}>
              {f.t === "ref" && <option value="">{f.req ? "— Choisir —" : "— Aucune —"}</option>}
              {(f.t === "ref" ? options(f) : f.opts!).map(([k, l]) => <option key={k} value={k} disabled={f.k === "institution" && !!scope && k !== scope}>{l}</option>)}
            </select>
          ) : <input required={f.req} maxLength={255} value={String(v ?? "")} onChange={(e) => setField(f.k, e.target.value)} />}
        {f.hint && <span className="hint">{f.hint}</span>}
      </label>
    );
  };

  return (
    <div className="layout">
      <div className="main" style={{ gap: 12 }}>
        <div className="tabs2" style={{ flexWrap: "wrap" }}>{ENTS.map((e) => <button key={e.key} className={tab === e.key ? "on" : ""} onClick={() => switchTab(e.key)}>{e.label}</button>)}</div>
        <div className="rowg" style={{ gap: 10, flexWrap: "nowrap" }}>
          <label className="search" style={{ height: 40 }}><Icon name="search" size={15} color="var(--muted3)" /><input value={q} onChange={(e) => setQ(e.target.value)} placeholder={`Rechercher parmi les ${ent.label.toLowerCase()}…`} aria-label={`Rechercher : ${ent.label}`} /></label>
          <button className="b dark" onClick={startNew}>Ajouter <Icon name="plus" size={14} color="#fff" /></button>
        </div>
        <div className="rowg" style={{ gap: 8 }}>
          {ent.filters.filter((k) => !(k === "institution" && scope)).map((k) => (
            <select key={k} className="sel" value={filters[k] ?? ""} onChange={(e) => setFilter(k, e.target.value)} aria-label={FILTER_UI[k].all}>
              <option value="">{FILTER_UI[k].all}</option>
              {FILTER_UI[k].opts().map(([v, l]) => <option key={v} value={v}>{l}</option>)}
            </select>
          ))}
        </div>
        <div className="panel" style={{ padding: "10px 16px", gap: 0 }}>
          <div className="row-tbl head" style={{ gridTemplateColumns: grid }}><span>{ent.cols[0]}</span><span>{ent.cols[1]}</span><span>{ent.cols[2]}</span><span /></div>
          {loading && <p className="p-muted" style={{ padding: 14 }}>Chargement…</p>}
          {!loading && rows.map((r) => (
            <button key={r.id} className="row-tbl" onClick={() => open(r)} style={{ gridTemplateColumns: grid, background: r.id === sel ? "#f5f9fe" : "none", border: 0, borderBottom: "1px solid #eef3f8", textAlign: "left" }}>
              <span><b style={{ display: "block", fontSize: 13 }}>{ent.title(r, x)}</b><small style={{ fontSize: 11, color: "var(--muted3)" }}>{ent.sub(r, x)}</small></span>
              <span style={{ fontSize: 12.5 }}>{ent.key === "specialties" ? instOf(ent.key, r) ?? "—" : ent.mid(r)}</span>
              {ent.official
                ? <span><span className={`chip2 ${badge(r)[1]}`} style={{ fontSize: 11.5, padding: "3px 9px" }}>{badge(r)[0]}</span></span>
                : <span style={{ fontWeight: 600, fontSize: 12, color: r.active ? "var(--blue2)" : "var(--danger)" }}>{r.active ? "Actif" : "Désactivé"}</span>}<span>›</span>
            </button>
          ))}
          {!loading && rows.length === 0 && <p className="p-muted" style={{ padding: 14 }}>Aucun résultat.</p>}
          <div className="rowb" style={{ fontSize: 12, color: "var(--muted3)", paddingTop: 10 }}><span>{rows.length} élément{rows.length > 1 ? "s" : ""}</span></div>
        </div>
      </div>

      <aside className="side" style={{ width: 400 }}>
        {sel === null ? (
          <div className="panel"><p className="p-muted">Sélectionnez un élément pour le consulter ou le modifier, ou ajoutez-en un.</p>{err && <p className="errbox" role="alert">{err}</p>}{msg && <p className="okbox">{msg}</p>}</div>
        ) : (
          <form className="panel" style={{ gap: 12 }} onSubmit={save}>
            <h2 style={{ fontSize: 17 }}>{creating ? `Ajouter : ${ent.one}` : cur ? ent.title(cur, x) : ent.label}</h2>
            {!creating && cur && <div className="rowg" style={{ gap: 8 }}><span className={`chip2 ${cur.active ? "ok" : "warn"}`}>{cur.active ? "Actif" : "Désactivé"}</span>{readOnly && <span className="chip2 line" style={{ fontSize: 11 }}>Lecture seule : autre établissement</span>}</div>}
            {creating && ent.key !== "programs" && progOpts.length === 0 && <p className="errbox">Créez d’abord une formation.</p>}
            {!creating && cur && ent.official && (
              <div className="col" style={{ gap: 8 }}>
                <div className="rowg" style={{ gap: 8, flexWrap: "wrap" }}>
                  <span className={`chip2 ${badge(cur)[1]}`}>{badge(cur)[0]}</span>
                  <span className="chip2 line" style={{ fontSize: 11 }}>{validityText(cur)}</span>
                </div>
                {!readOnly && (
                  <div className="rowg" style={{ gap: 8, flexWrap: "wrap" }}>
                    {cur.status !== "published" && <button type="button" className="b pri" style={{ borderRadius: 8 }} disabled={dirty} onClick={() => void act("publish")}>Publier</button>}
                    {cur.status === "published" && <button type="button" className="b" style={{ borderRadius: 8 }} disabled={dirty} onClick={() => void act("draft")}>Repasser en brouillon</button>}
                    {cur.status !== "archived" && <button type="button" className="b" style={{ borderRadius: 8 }} disabled={dirty} onClick={() => void act("archive")}>Archiver</button>}
                  </div>
                )}
                <p className="hint" style={{ fontSize: 11.5, color: "var(--muted3)", margin: 0 }}>
                  {dirty && !readOnly ? "Enregistrez vos modifications avant de changer le statut. "
                    : ""}{cur.status === "published" ? "Visible des candidats et de l’agent IA pendant sa période de validité. Modifier son contenu le repasse en brouillon."
                    : cur.status === "draft" ? "Invisible des candidats et de l’agent IA tant qu’il n’est pas publié."
                    : "Retiré : conservé pour l’historique, jamais montré."}
                </p>
              </div>
            )}
            {creating && ent.official && <p className="p-muted" style={{ fontSize: 12, margin: 0 }}>Le nouvel élément est créé en brouillon : publiez-le ensuite pour le rendre visible des candidats et de l’agent IA.</p>}
            <fieldset disabled={readOnly} style={{ display: "contents" }}>
              {groups.map((g) => g.length === 2
                ? <div key={g[0].k} className="grid g2" style={{ gap: 12 }}>{g.map(control)}</div>
                : control(g[0]))}
            </fieldset>
            <div className="rowg" style={{ gap: 8 }}>
              <button className="b dark" style={{ borderRadius: 8 }} disabled={readOnly}>{creating ? "Ajouter" : "Enregistrer"} <Icon name="save" size={14} color="#fff" /></button>
              <button type="button" className="lnk" onClick={() => { setSel(null); clear(); }}>{creating ? "Annuler" : "Fermer"}</button>
            </div>
            {!creating && !readOnly && (confirmDel ? (
              <div className="col" style={{ gap: 8 }}>
                <p className="errbox">Supprimer définitivement cet élément ? {ent.cascade ?? ""} Pour le masquer seulement, décochez « actif ».</p>
                <div className="rowg" style={{ gap: 8 }}>
                  <button type="button" className="b" style={{ borderRadius: 8, color: "var(--danger)" }} onClick={() => void remove()}>Confirmer la suppression</button>
                  <button type="button" className="lnk" onClick={() => setConfirmDel(false)}>Annuler</button>
                </div>
              </div>
            ) : <div><button type="button" className="b" style={{ borderRadius: 8 }} onClick={() => setConfirmDel(true)}>Supprimer</button></div>)}
            {err && <p className="errbox" role="alert">{err}</p>}
            {msg && <p className="okbox">{msg}</p>}
          </form>
        )}
        <div className="notice" style={{ borderRadius: 9 }}><Icon name="shield" size={15} color="var(--blue2)" /><span style={{ fontSize: 12.5, color: "var(--ink2)" }}>Frais, modalités de paiement et conditions d’admission ne sont visibles des candidats et de l’agent IA que publiés et dans leur période de validité. Un élément désactivé n’est jamais visible ; durées et matières doivent être confirmées par l’établissement avant d’être activées.</span></div>
      </aside>
    </div>
  );
}
