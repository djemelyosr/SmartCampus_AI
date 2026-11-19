import { useI18n, type Lang } from "../lib/i18n";
import { LANGS } from "../lib/locales";

/** Language dropdown (Français / English / العربية) shown in every navbar. */
export default function LangSwitcher() {
  const { lang, setLang, t } = useI18n();
  return (
    <select
      className="lang-select"
      value={lang}
      aria-label={t("Langue")}
      onChange={(e) => setLang(e.target.value as Lang)}
    >
      {LANGS.map((l) => (
        <option key={l.code} value={l.code}>{l.label}</option>
      ))}
    </select>
  );
}
