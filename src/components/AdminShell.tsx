import type { ReactNode } from "react";
import { NavLink } from "react-router-dom";
import Icon from "./Icon";

type IconName = Parameters<typeof Icon>[0]["name"];
const MENU: [string, string, IconName][] = [
  ["/admin/utilisateurs", "Utilisateurs & rôles", "users"],
  ["/admin/formations", "Programmes IIT / ISB", "cap"],
  ["/admin/campagnes", "Campagnes", "calendar"],
  ["/admin/campagnes#regles", "Règles de workflow", "workflow"],
  ["/admin", "Sources RAG", "db"],
  ["/admin/campagnes#qcm", "Modèles QCM", "list"],
  ["/admin/campagnes#emails", "E-mails & rappels", "mail"],
  ["/admin/ia", "Agents IA", "bot"],
  ["/admin/ia#audio", "Audio & langues", "mic"],
  ["/admin/ia#integrations", "Intégrations", "plug"],
  ["/admin/journal", "Journal d’activité", "clock"],
];

/** Admin screens 23-28: heading + left "Configuration" menu + content. */
export default function AdminShell({ title, sub, action, children, hideJournal }: { title: string; sub: string; action?: ReactNode; children: ReactNode; hideJournal?: boolean }) {
  return (
    <div className="ws" style={{ gap: 20 }}>
      <div className="rowb" style={{ alignItems: "flex-start" }}>
        <div>
          <h1 style={{ margin: 0, fontSize: 28, fontWeight: 600, letterSpacing: -0.8, color: "var(--navy)" }}>{title}</h1>
          <p className="p-muted" style={{ margin: "6px 0 0", fontSize: 14, color: "var(--muted3)" }}>{sub}</p>
        </div>
        {action}
      </div>
      <div className="layout">
        <aside className="side" style={{ width: 200 }}>
          <nav className="panel adm-menu" style={{ padding: 10, gap: 4 }}>
            <span className="eyebrow2" style={{ padding: "6px 10px", fontSize: 11 }}>Configuration</span>
            {MENU.filter(([, , ]) => !(hideJournal && false)).map(([to, label, icon]) => (
              <NavLink key={label} to={to} end={!to.includes("#")} className={({ isActive }) => `am ${isActive && !to.includes("#") ? "on" : ""}`}>
                <Icon name={icon} size={15} />{label}
              </NavLink>
            ))}
            <small style={{ padding: "10px 10px 4px", fontSize: 11, color: "var(--muted3)", lineHeight: 1.4 }}>Dernière modification<br />07 juillet 2026 · 09:41<br />par Amira Mansour</small>
          </nav>
        </aside>
        <div className="main" style={{ gap: 20 }}>{children}</div>
      </div>
    </div>
  );
}
