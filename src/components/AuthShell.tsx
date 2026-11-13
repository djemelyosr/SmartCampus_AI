import type { ReactNode } from "react";

export interface AuthItem { icon?: string; num?: number; t: string; d: string }

interface Props {
  eyebrow: string;
  title: [string, string];
  lead: string;
  cardTitle: string;
  items: AuthItem[];
  cardFoot: ReactNode;
  below?: ReactNode;
  children: ReactNode;
  formWidth?: number;
}

/** Two-column shell shared by screens 06, 07, 08 (intro + dark card on the left, forms on the right). */
export default function AuthShell({ eyebrow, title, lead, cardTitle, items, cardFoot, below, children, formWidth = 560 }: Props) {
  return (
    <div className="auth2">
      <section className="auth2-l">
        <span className="chip2 hl line" style={{ fontSize: 11, alignSelf: "flex-start" }}>{eyebrow}</span>
        <h1 className="auth2-h1">{title[0]}<br />{title[1]}</h1>
        <p className="auth2-lead">{lead}</p>
        <div className="auth2-card">
          <h2>{cardTitle}</h2>
          {items.map((it) => (
            <div className="auth2-it" key={it.t}>
              {it.icon ? <img src={it.icon} alt="" /> : <i>{it.num}</i>}
              <div><b>{it.t}</b><span>{it.d}</span></div>
            </div>
          ))}
          <hr />
          <p>{cardFoot}</p>
        </div>
        {below}
      </section>
      <section className="auth2-r" style={{ width: formWidth }}>{children}</section>
    </div>
  );
}
