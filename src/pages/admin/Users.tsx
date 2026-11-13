import { useCallback, useEffect, useMemo, useState, type FormEvent } from "react";
import AdminShell from "../../components/AdminShell";
import Icon from "../../components/Icon";
import { api, ApiError, type AdminUser, type RoleName } from "../../lib/api";
import { useAuth } from "../../lib/auth";

/** Roles of the platform (SmartCampus.pdf §3) with the rights each one is meant to have. */
const ROLES: Record<RoleName, { label: string; short: string; rights: string[] }> = {
  candidate: {
    label: "Candidat", short: "Candidats",
    rights: ["Dialoguer avec le chatbot (texte ou audio)", "Comparer les formations et se préinscrire", "Passer le QCM personnalisé", "Consulter son rendez-vous et ses notifications"],
  },
  iit_head: {
    label: "Responsable académique IIT", short: "Académiques IIT",
    rights: ["Consulter les candidats orientés vers l’IIT", "Voir profils, recommandations et résultats du QCM", "Confirmer ou ajuster une recommandation", "Gérer les formations IIT et leurs statistiques"],
  },
  isb_head: {
    label: "Responsable académique ISB", short: "Académiques ISB",
    rights: ["Consulter les candidats orientés vers l’ISB", "Voir profils, recommandations et résultats du QCM", "Confirmer ou ajuster une recommandation", "Gérer les formations ISB et leurs statistiques"],
  },
  interviewer: {
    label: "Responsable entretien", short: "Entretiens",
    rights: ["Consulter les candidats prêts pour un entretien", "Lire la synthèse, le profil et le QCM", "Planifier le rendez-vous et envoyer l’invitation", "Saisir le résultat et les observations"],
  },
  direction: {
    label: "Direction", short: "Direction",
    rights: ["Tableau de bord global du processus", "Suivre conversations, préinscriptions, entretiens, inscriptions", "Comparer les orientations IIT / ISB", "Rapports d’aide à la décision"],
  },
  admin: {
    label: "Administrateur", short: "Administrateurs",
    rights: ["Gérer les comptes, rôles et droits d’accès", "Configurer formations, campagnes et workflow", "Administrer les sources RAG, modèles et notifications", "Consulter journaux et erreurs"],
  },
};
const ROLE_KEYS = Object.keys(ROLES) as RoleName[];

const genPassword = () => {
  const alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnpqrstuvwxyz23456789";
  const bytes = crypto.getRandomValues(new Uint8Array(16));
  return Array.from(bytes, (b) => alphabet[b % alphabet.length]).join("");
};

const errText = (e: unknown) => {
  if (e instanceof ApiError) {
    if (e.status === 409 && /administrator/i.test(e.message)) return "Il doit rester au moins un administrateur actif.";
    if (e.status === 409) return "Cette adresse e-mail est déjà utilisée.";
    if (e.status === 422) return "Informations invalides (mot de passe : 12 caractères minimum).";
    if (e.status === 403) return "Action réservée aux administrateurs.";
  }
  return "Le serveur est injoignable.";
};

export default function Users() {
  const { user: me } = useAuth();
  const [users, setUsers] = useState<AdminUser[]>([]);
  const [loading, setLoading] = useState(true);
  const [sel, setSel] = useState<number | null>(null);
  const [q, setQ] = useState("");
  const [filter, setFilter] = useState<"all" | RoleName>("all");
  const [msg, setMsg] = useState("");
  const [err, setErr] = useState("");
  const [creating, setCreating] = useState(false);
  const [form, setForm] = useState({ email: "", full_name: "", role: "interviewer" as RoleName, password: "" });
  const [newPw, setNewPw] = useState("");

  const load = useCallback(async () => {
    try {
      const list = await api.adminUsers();
      setUsers(list);
      setSel((s) => s ?? list[0]?.id ?? null);
    } catch (e) { setErr(errText(e)); }
    finally { setLoading(false); }
  }, []);
  useEffect(() => { void load(); }, [load]);

  const count = (r: RoleName) => users.filter((u) => u.role === r).length;
  const list = useMemo(
    () => users.filter((u) => (filter === "all" || u.role === filter) && `${u.full_name} ${u.email}`.toLowerCase().includes(q.toLowerCase())),
    [users, q, filter],
  );
  const cur = users.find((u) => u.id === sel) ?? null;

  async function update(body: Parameters<typeof api.adminUpdateUser>[1], ok: string) {
    if (!cur) return;
    setErr(""); setMsg("");
    try {
      const u = await api.adminUpdateUser(cur.id, body);
      setUsers((all) => all.map((x) => (x.id === u.id ? u : x)));
      setMsg(ok);
    } catch (e) { setErr(errText(e)); }
  }

  async function create(e: FormEvent) {
    e.preventDefault();
    setErr(""); setMsg("");
    try {
      const u = await api.adminCreateUser(form);
      setUsers((all) => [...all, u]);
      setSel(u.id); setCreating(false);
      setMsg(`Compte créé pour ${u.email} (${ROLES[u.role].label}). Transmettez-lui son mot de passe temporaire.`);
      setForm({ email: "", full_name: "", role: "interviewer", password: "" });
    } catch (e2) { setErr(errText(e2)); }
  }

  const FILTERS: ["all" | RoleName, string][] = [["all", `Tous · ${users.length}`], ...ROLE_KEYS.map((r): ["all" | RoleName, string] => [r, `${ROLES[r].short} · ${count(r)}`])];
  const state = (u: AdminUser) => (u.is_active ? "Actif" : "Suspendu");

  return (
    <AdminShell title="Les bons accès, pour chaque rôle" sub="Comptes, rôles et droits d’accès · L’inscription publique crée uniquement des comptes candidat"
      action={<button className="b dark" onClick={() => { setCreating(true); setForm((f) => ({ ...f, password: genPassword() })); }}>Créer un compte <Icon name="userplus" size={14} color="#fff" /></button>}>
      <div className="grid g3" style={{ gap: 14 }}>
        <div className="stat"><span className="l">Utilisateurs</span><span className="v">{users.length}</span><small className="small" style={{ fontSize: 12 }}>{users.filter((u) => u.is_active).length} actifs · {users.filter((u) => !u.is_active).length} suspendus</small></div>
        <div className="stat"><span className="l">Rôles disponibles</span><span className="v">{ROLE_KEYS.length}</span><small className="small" style={{ fontSize: 12 }}>Des droits selon la mission</small></div>
        <div className="stat"><span className="l">Équipe</span><span className="v">{users.filter((u) => u.role !== "candidate").length}</span><small className="small" style={{ fontSize: 12 }}>Comptes non candidats</small></div>
      </div>
      <div className="notice" style={{ borderRadius: 8 }}><Icon name="shield" size={15} color="var(--blue2)" /><span style={{ fontSize: 13, color: "var(--ink2)" }}>Seul un administrateur attribue les rôles de l’équipe. Modifier un rôle ne délègue jamais une décision d’admission à l’IA.</span></div>
      {err && <p className="errbox" role="alert">{err}</p>}

      <div className="layout">
        <div className="main" style={{ gap: 12 }}>
          <label className="search" style={{ height: 40 }}><Icon name="search" size={15} color="var(--muted3)" /><input value={q} onChange={(e) => setQ(e.target.value)} placeholder="Rechercher par nom ou adresse e-mail…" aria-label="Rechercher un utilisateur" /></label>
          <div className="tabs2" style={{ flexWrap: "wrap" }}>{FILTERS.map(([k, l]) => <button key={k} className={filter === k ? "on" : ""} onClick={() => setFilter(k)}>{l}</button>)}</div>
          <div className="panel" style={{ padding: "10px 16px", gap: 0 }}>
            <div className="row-tbl head" style={{ gridTemplateColumns: "1.6fr 1.2fr .6fr 18px" }}><span>Utilisateur</span><span>Rôle</span><span>État</span><span /></div>
            {loading && <p className="p-muted" style={{ padding: 14 }}>Chargement…</p>}
            {list.map((u) => (
              <button key={u.id} className="row-tbl" onClick={() => { setSel(u.id); setMsg(""); setErr(""); setNewPw(""); }} style={{ gridTemplateColumns: "1.6fr 1.2fr .6fr 18px", background: u.id === sel ? "#f5f9fe" : "none", border: 0, borderBottom: "1px solid #eef3f8", textAlign: "left" }}>
                <span><b style={{ display: "block", fontSize: 13 }}>{u.full_name || u.email.split("@")[0]}</b><small style={{ fontSize: 11, color: "var(--muted3)" }}>{u.email}</small></span>
                <span>{ROLES[u.role]?.label ?? u.role}</span>
                <span style={{ fontWeight: 600, fontSize: 12, color: u.is_active ? "var(--blue2)" : "var(--danger)" }}>{state(u)}</span><span>›</span>
              </button>
            ))}
            {!loading && list.length === 0 && <p className="p-muted" style={{ padding: 14 }}>Aucun utilisateur.</p>}
            <div className="rowb" style={{ fontSize: 12, color: "var(--muted3)", paddingTop: 10 }}><span>{list.length} utilisateur{list.length > 1 ? "s" : ""}</span></div>
          </div>
        </div>

        <aside className="side" style={{ width: 380 }}>
          {creating ? (
            <form className="panel" style={{ gap: 12 }} onSubmit={create}>
              <h2 style={{ fontSize: 17 }}>Nouveau compte</h2>
              <label className="fld" style={{ fontSize: 12 }}>Adresse e-mail *<input type="email" required value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} /></label>
              <label className="fld" style={{ fontSize: 12 }}>Nom complet<input value={form.full_name} onChange={(e) => setForm({ ...form, full_name: e.target.value })} /></label>
              <label className="fld" style={{ fontSize: 12 }}>Rôle *
                <select className="sel" value={form.role} onChange={(e) => setForm({ ...form, role: e.target.value as RoleName })}>{ROLE_KEYS.map((r) => <option key={r} value={r}>{ROLES[r].label}</option>)}</select>
              </label>
              <label className="fld" style={{ fontSize: 12 }}>Mot de passe temporaire * (12 caractères min.)
                <input required minLength={12} value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} />
              </label>
              <div className="rowg" style={{ gap: 8 }}>
                <button type="button" className="b" style={{ borderRadius: 8 }} onClick={() => setForm({ ...form, password: genPassword() })}>Générer</button>
                <button className="b dark" style={{ borderRadius: 8 }}>Créer le compte</button>
                <button type="button" className="lnk" onClick={() => setCreating(false)}>Annuler</button>
              </div>
              <p className="small" style={{ fontSize: 11 }}>Communiquez le mot de passe par un canal sûr ; la personne pourra ensuite se connecter à son espace.</p>
            </form>
          ) : cur ? (
            <div className="panel" style={{ gap: 12 }}>
              <h2 style={{ fontSize: 17 }}>{cur.full_name || cur.email}</h2>
              <div><span className="chip2 hl line" style={{ fontSize: 11 }}>{state(cur)}</span></div>
              <span className="small" style={{ fontSize: 12 }}>{cur.email}</span>
              <label className="fld" style={{ fontSize: 12 }}>Rôle attribué
                <select className="sel" value={cur.role} onChange={(e) => void update({ role: e.target.value as RoleName }, `Rôle mis à jour : ${ROLES[e.target.value as RoleName].label}.`)}>
                  {ROLE_KEYS.map((r) => <option key={r} value={r}>{ROLES[r].label}</option>)}
                </select>
              </label>
              <b style={{ fontSize: 12 }}>Droits de ce rôle</b>
              {ROLES[cur.role].rights.map((r) => (
                <span key={r} className="cbx on" style={{ fontSize: 12.5, cursor: "default" }}><i><Icon name="check" size={12} color="#fff" /></i>{r}</span>
              ))}
              <hr className="hr" />
              <label className="fld" style={{ fontSize: 12 }}>Nouveau mot de passe (optionnel)
                <input value={newPw} onChange={(e) => setNewPw(e.target.value)} placeholder="12 caractères minimum" />
              </label>
              <div className="rowg" style={{ gap: 8 }}>
                <button className="b" style={{ borderRadius: 8 }} onClick={() => setNewPw(genPassword())}>Générer</button>
                <button className="b dark" style={{ borderRadius: 8 }} disabled={newPw.length < 12} onClick={() => void update({ password: newPw }, "Mot de passe réinitialisé.").then(() => setNewPw(""))}>Réinitialiser</button>
              </div>
              <div>
                <button className="b" style={{ borderRadius: 8 }} disabled={cur.id === me?.id && cur.is_active}
                  title={cur.id === me?.id ? "Vous ne pouvez pas suspendre votre propre compte" : undefined}
                  onClick={() => void update({ is_active: !cur.is_active }, cur.is_active ? "Accès suspendu." : "Accès rétabli.")}>
                  {cur.is_active ? "Suspendre l’accès" : "Rétablir l’accès"}
                </button>
              </div>
              <p className="small" style={{ fontSize: 11 }}>{msg || "Les comptes suspendus ne peuvent plus se connecter."}</p>
            </div>
          ) : (
            <div className="panel"><p className="p-muted">Sélectionnez un utilisateur.</p></div>
          )}
          <div className="notice" style={{ borderRadius: 9 }}><Icon name="shield" size={15} color="var(--blue2)" /><span style={{ fontSize: 12.5, color: "var(--ink2)" }}>La décision officielle d’admission relève d’une personne habilitée par l’établissement, jamais d’un score ou d’un agent IA.</span></div>
        </aside>
      </div>
    </AdminShell>
  );
}
