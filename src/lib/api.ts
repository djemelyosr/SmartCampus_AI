import { ApiError } from "./errors";

const TOKEN_KEY = "sc_token";

export const getToken = () => localStorage.getItem(TOKEN_KEY);
export const setToken = (t: string | null) =>
  t ? localStorage.setItem(TOKEN_KEY, t) : localStorage.removeItem(TOKEN_KEY);

export { ApiError } from "./errors";

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const headers = new Headers(init.headers);
  const token = getToken();
  if (token) headers.set("Authorization", `Bearer ${token}`);
  const res = await fetch(`/api${path}`, { ...init, headers });
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      detail = typeof body.detail === "string" ? body.detail : JSON.stringify(body.detail);
    } catch { /* keep statusText */ }
    throw new ApiError(res.status, detail);
  }
  return res.json() as Promise<T>;
}

const json = (method: string, body: unknown): RequestInit => ({
  method,
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify(body),
});

export type RoleName = "candidate" | "iit_head" | "isb_head" | "interviewer" | "direction" | "admin";
export interface User { id: number; email: string; full_name: string; role: string; is_active?: boolean }
export interface AdminUser extends User { role: RoleName; is_active: boolean }
export interface Profile {
  id: number; user_id: number; phone: string | null; school_level: string | null;
  favorite_subjects: string[]; interests: string[]; career_goal: string | null;
  constraints: Record<string, unknown>; consent_given: boolean;
}
export interface Message { id: number; role: string; content: string; modality: string; meta: Record<string, unknown>; created_at: string }
export interface Conversation { id: number; language: string | null; created_at: string; messages: Message[] }
export interface Program {
  id: number; institution: "IIT" | "ISB"; level: string; name: string; description: string;
  admission_requirements: string; duration_years: number | null; career_outcomes: string[];
}

export interface QcmQuestion { section: string; text: string; code?: string[]; options: string[] }
export interface QcmView { id: number; questions: QcmQuestion[]; answers: Record<number, number>; finished: boolean }
export interface QcmResults {
  good: number; total: number; pct: number; summary: string; finished_at: string | null;
  by_section: { section: string; good: number; total: number; pct: number; advice: string }[];
}
export interface Slot { slot: string; available: boolean }
export interface Appointment { id: number; scheduled_at: string; ends_at: string; status: string }
export interface Doc { id: number; kind: string; filename: string; content_type: string; size: number; status: string; created_at?: string | null }

export interface Stats {
  scope: string;
  totals: { conversations: number; orientations: number; preinscriptions: number; interviews: number; enrollments: number; pending: number; conversion: number };
  funnel: { label: string; value: number }[];
  programs: { institution: "IIT" | "ISB"; name: string; orientations: number; preinscriptions: number; validated: number; interest: number }[];
  pending: { candidate: string; institution: string | null; step: string; action: string }[];
  agents: { handoffs: number; sourced_pct: number | null; messages: number };
  by_institution?: Record<"IIT" | "ISB", Stats["totals"]>;
}
export interface InterviewItem {
  id: number; reference: string; name: string; program: string; institution: string; status: string;
  qcm: { good: number; total: number } | null; appointment: { id: number; scheduled_at: string; status: string } | null;
}
export interface InterviewDetail extends InterviewItem {
  language: string | null; summary: string; school_level: string | null; career_goal: string | null;
  recommendation: { chosen: string; shortlist: string[]; validated_by_human: boolean };
  qcm_result: { good: number; total: number; pct: number; by_section: { section: string; good: number; total: number; pct: number }[] } | null;
  points: string[]; disclaimer: string;
}

export const api = {
  register: (email: string, password: string, full_name: string) =>
    request<User>("/auth/register", json("POST", { email, password, full_name })),
  login: async (email: string, password: string) => {
    const form = new URLSearchParams({ username: email, password });
    const r = await request<{ access_token: string }>("/auth/login", { method: "POST", body: form });
    setToken(r.access_token);
  },
  me: () => request<User>("/auth/me"),
  getProfile: () => request<Profile>("/auth/me/profile"),
  saveProfile: (p: Omit<Profile, "id" | "user_id">) => request<Profile>("/auth/me/profile", json("PUT", p)),
  programs: () => request<Program[]>("/programs"),
  createPreinscription: (program_id: number) => request<{ id: number }>("/preinscriptions", json("POST", { program_id })),
  startConversation: () => request<Conversation>("/conversations", { method: "POST" }),
  sendMessage: (id: number, content: string, modality = "text") =>
    request<Message>(`/conversations/${id}/messages`, json("POST", { content, modality })),

  getQcm: () => request<QcmView>("/qcm/current"),
  saveAnswers: (id: number, answers: Record<number, number>, finish = false) =>
    request<QcmView>(`/qcm/${id}/answers`, json("PUT", { answers, finish })),
  qcmResults: (id: number) => request<QcmResults>(`/qcm/${id}/results`),

  slots: (start: string, days = 7) => request<Slot[]>(`/appointments/slots?start=${start}&days=${days}`),
  myAppointments: () => request<Appointment[]>("/appointments/me"),
  bookSlot: (slot: string) => request<Appointment>("/appointments", json("POST", { slot })),
  cancelAppointment: (id: number) => request<Appointment>(`/appointments/${id}`, { method: "DELETE" }),

  stats: (institution?: string) => request<Stats>(institution ? `/stats/overview?institution=${institution}` : "/stats/overview"),
  interviewCandidates: () => request<InterviewItem[]>("/interviews/candidates"),
  interviewCandidate: (id: number) => request<InterviewDetail>(`/interviews/candidates/${id}`),

  listDocuments: () => request<Doc[]>("/documents"),
  uploadDocument: (kind: string, file: File) => {
    const form = new FormData();
    form.set("kind", kind);
    form.set("file", file);
    return request<Doc>("/documents", { method: "POST", body: form });
  },
  /** Administrator: accounts, roles and access (GET/POST/PATCH /api/admin/users). */
  adminUsers: () => request<AdminUser[]>("/admin/users"),
  adminCreateUser: (body: { email: string; password: string; full_name: string; role: RoleName }) =>
    request<AdminUser>("/admin/users", json("POST", body)),
  adminUpdateUser: (id: number, body: Partial<{ full_name: string; role: RoleName; is_active: boolean; password: string }>) =>
    request<AdminUser>(`/admin/users/${id}`, json("PATCH", body)),
  /** Files need the Bearer token, so fetch the bytes and open them as a blob URL. */
  openDocument: async (id: number): Promise<void> => {
    const token = getToken();
    const res = await fetch(`/api/documents/${id}/file`, { headers: token ? { Authorization: `Bearer ${token}` } : {} });
    if (!res.ok) throw new ApiError(res.status, "Document indisponible");
    const url = URL.createObjectURL(await res.blob());
    window.open(url, "_blank", "noopener");
    setTimeout(() => URL.revokeObjectURL(url), 60_000);
  },
};
