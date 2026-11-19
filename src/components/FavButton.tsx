import { useI18n } from "../lib/i18n";

/** Clickable heart to add / remove a formation from the favourites. */
export default function FavButton({ on, onToggle }: { on: boolean; onToggle: () => void }) {
  const { t } = useI18n();
  const label = on ? t("Retirer des favoris") : t("Ajouter aux favoris");
  return (
    <button
      type="button"
      className={`fav ${on ? "on" : ""}`}
      aria-pressed={on}
      aria-label={label}
      title={label}
      onClick={(e) => { e.preventDefault(); e.stopPropagation(); onToggle(); }}
    >
      <svg viewBox="0 0 24 24" width="20" height="20" aria-hidden="true">
        <path
          d="M12 21s-7.5-4.6-9.6-9.2C.9 8.3 2.7 4.5 6.4 4.5c2 0 3.6 1.1 4.6 2.6l1 1.4 1-1.4c1-1.5 2.6-2.6 4.6-2.6 3.7 0 5.5 3.8 4 7.3C19.5 16.4 12 21 12 21z"
          fill={on ? "currentColor" : "none"} stroke="currentColor" strokeWidth="1.8" strokeLinejoin="round"
        />
      </svg>
    </button>
  );
}
