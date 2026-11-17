// Aide à la lecture à voix haute des réponses en Arabizi (dérija écrite en lettres latines + chiffres).
// Une voix française lit « 3 » comme « trois » au lieu du son ع. Pour la synthèse vocale uniquement,
// on translittère donc le texte en lettres arabes (avec voyelles courtes) et on utilise une voix arabe.
// Heuristique : approximative, jamais utilisée pour l'affichage du texte.

const DIGITS: Record<string, string> = {
  "2": "ء",
  "3": "ع",
  "5": "خ",
  "6": "ط",
  "7": "ح",
  "8": "غ",
  "9": "ق",
};

const DIGRAPHS: Record<string, string> = {
  ch: "ش",
  sh: "ش",
  kh: "خ",
  gh: "غ",
  th: "ث",
  dh: "ذ",
  ou: "و",
  oo: "و",
  aa: "ا",
  ii: "ي",
  ee: "ي",
};

const LETTERS: Record<string, string> = {
  b: "ب", t: "ت", j: "ج", d: "د", r: "ر", z: "ز", s: "س", c: "س", f: "ف", q: "ق",
  k: "ك", l: "ل", m: "م", n: "ن", h: "ه", w: "و", y: "ي", g: "ڨ", p: "ب", v: "ف", x: "كس",
};

const FATHA = "\u064E";
const KASRA = "\u0650";
const DAMMA = "\u064F";

/** Un mot contient-il un chiffre d'Arabizi collé à au moins deux lettres, avec une minuscule ? */
function isArabiziToken(tok: string): boolean {
  if (!/[a-z]/.test(tok)) return false;
  if (/^\d+(e|eme|ème|er|ère|ere)$/i.test(tok)) return false; // 2ème, 3eme...
  return /[a-z]{2,}[235-9]|[235-9][a-z]{2,}/i.test(tok) || /[a-z][235-9][a-z]/i.test(tok);
}

/** Le texte est-il de l'Arabizi (au moins 2 mots typiques, ou 10 % des mots) ? */
export function looksArabizi(text: string): boolean {
  if (/[\u0600-\u06FF]/.test(text)) return false;
  const words = text.match(/[A-Za-zÀ-ÿ0-9]+/g) ?? [];
  if (!words.length) return false;
  const hits = words.filter(isArabiziToken).length;
  return hits >= 2 || hits / words.length >= 0.1;
}

function word(tok: string): string {
  const w = tok.toLowerCase();
  let out = "";
  let i = 0;
  while (i < w.length) {
    const two = w.slice(i, i + 2);
    const ch = w[i];
    if (DIGRAPHS[two]) { out += DIGRAPHS[two]; i += 2; continue; }
    if (DIGITS[ch]) { out += DIGITS[ch]; i += 1; continue; }
    if (LETTERS[ch]) { out += LETTERS[ch]; i += 1; continue; }
    if ("aeiouéèê".includes(ch)) {
      const start = out.length === 0;
      const mark = ch === "a" ? FATHA : ch === "o" || ch === "u" ? DAMMA : KASRA;
      if (start) out += (ch === "i" || ch === "e" || ch === "é" || ch === "è" ? "إ" : "أ") + mark;
      else out += mark;
      i += 1;
      continue;
    }
    out += ch; // ponctuation, chiffres isolés...
    i += 1;
  }
  return out;
}

/** Translittère un texte Arabizi en lettres arabes, mot par mot (pour la synthèse vocale seulement). */
export function arabiziToArabic(text: string): string {
  return text.replace(/[A-Za-zÀ-ÿ0-9]+/g, (tok) => (/^\d+$/.test(tok) ? tok : word(tok)));
}

/**
 * Variante pour les navigateurs SANS voix arabe : on garde les lettres latines mais on remplace les chiffres
 * par un son lisible par une voix française (7 -> h, 3 -> a, 9 -> k, 5 -> kh, 8 -> gh, 6 -> t, 2 -> a).
 */
export function arabiziToLatinSpeech(text: string): string {
  const SOUND: Record<string, string> = { "2": "a", "3": "a", "5": "kh", "6": "t", "7": "h", "8": "gh", "9": "k" };
  return text.replace(/[A-Za-zÀ-ÿ0-9]+/g, (tok) =>
    isArabiziToken(tok) ? tok.replace(/[235-9]/g, (d) => SOUND[d]) : tok,
  );
}
