/** Local candidate UI state (selected formation, notification prefs). The API is the source of truth. */
export interface Candidature {
  formation: string;
  preinscription: null | { sentAt: string; ref: string };
  qcm: { answers: Record<number, number>; review: number[]; doneAt: string | null };
  docs: { name: string; size: number; at: string; kind?: string }[];
  rdv: null | { slot: string; bookedAt: string };
  notifRead: string[];
  prefs: Record<string, boolean>;
}

const KEY = "sc_candidature";
const empty: Candidature = {
  formation: "",
  preinscription: null,
  qcm: { answers: {}, review: [], doneAt: null },
  docs: [],
  rdv: null,
  notifRead: [],
  prefs: { espace: true, email: true, sms: false, confirmations: true, rappels: true, complements: true, actus: false },
};

export function loadCandidature(): Candidature {
  try {
    const raw = localStorage.getItem(KEY);
    return raw ? { ...empty, ...JSON.parse(raw) } : structuredClone(empty);
  } catch {
    return structuredClone(empty);
  }
}

export function saveCandidature(patch: Partial<Candidature>): Candidature {
  const next = { ...loadCandidature(), ...patch };
  try { localStorage.setItem(KEY, JSON.stringify(next)); } catch { /* storage unavailable */ }
  return next;
}

export const frDate = (iso: string) =>
  new Date(iso).toLocaleDateString("fr-FR", { day: "2-digit", month: "long", year: "numeric" });
