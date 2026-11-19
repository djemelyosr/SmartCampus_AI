import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from "react";
import { DICT, LANGS } from "./locales";

export type Lang = "fr" | "en" | "ar";

const KEY = "sc_lang";

const initialLang = (): Lang => {
  try {
    const v = localStorage.getItem(KEY);
    if (v === "fr" || v === "en" || v === "ar") return v;
  } catch { /* storage unavailable */ }
  return "fr";
};

interface I18nCtx {
  lang: Lang;
  setLang: (l: Lang) => void;
  /** Translate a French source text (returns it unchanged in French or when no translation exists). */
  t: (fr: string) => string;
}

const Ctx = createContext<I18nCtx | null>(null);

export function LangProvider({ children }: { children: ReactNode }) {
  const [lang, setLangState] = useState<Lang>(initialLang);

  useEffect(() => {
    const meta = LANGS.find((l) => l.code === lang)!;
    document.documentElement.lang = lang;
    document.documentElement.dir = meta.dir;
  }, [lang]);

  const setLang = useCallback((l: Lang) => {
    setLangState(l);
    try { localStorage.setItem(KEY, l); } catch { /* storage unavailable */ }
  }, []);

  const value = useMemo<I18nCtx>(
    () => ({ lang, setLang, t: (fr) => (lang === "fr" ? fr : DICT[fr]?.[lang] ?? fr) }),
    [lang, setLang],
  );
  return <Ctx.Provider value={value}>{children}</Ctx.Provider>;
}

export function useI18n() {
  const v = useContext(Ctx);
  if (!v) throw new Error("useI18n outside LangProvider");
  return v;
}
