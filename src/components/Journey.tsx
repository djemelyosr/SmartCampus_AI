import chevron from "../assets/chevron-right.svg";

export const JOURNEY = ["Orientation", "Choix du parcours", "Pré-inscription", "QCM personnalisé", "Rendez-vous"];

/** 5-step candidate journey bar (Figma screens 04, 05). `current` is 1-based. */
export default function Journey({ current, chevrons = false }: { current: number; chevrons?: boolean }) {
  return (
    <div className="journey">
      {JOURNEY.map((label, i) => {
        const n = i + 1;
        const state = n < current ? "done" : n === current ? "cur" : "todo";
        return (
          <div className={`jstep ${state}`} key={label}>
            <span className="ind">{state === "done" ? "✓" : n}</span>
            <span className="lbl">{label}</span>
            {chevrons && n < JOURNEY.length && <img src={chevron} alt="" width={12} height={12} />}
          </div>
        );
      })}
    </div>
  );
}
