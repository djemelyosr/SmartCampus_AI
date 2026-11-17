import img1 from "../assets/formation-1.png";
import img2 from "../assets/formation-2.png";
import img3 from "../assets/formation-3.png";
import img4 from "../assets/formation-4.png";
import img5 from "../assets/formation-5.png";
import { api, type Program } from "./api";

export type Institution = "IIT" | "ISB";
export type Level = "Licence" | "Prépa" | "Ingénierie";

export interface Formation {
  id: string;
  institution: Institution;
  level: Level;
  domain: "Informatique & sciences" | "Gestion & finance";
  name: string;
  tagline: string;
  keywords: string;
  image: string;
  admission: string;
  duration: number | null;
}

const IMAGES = [img1, img2, img3, img4, img5];
const LEVELS: Record<string, Level> = { licence: "Licence", prepa: "Prépa", ingenierie: "Ingénierie" };

const toFormation = (p: Program, i: number): Formation => ({
  id: String(p.id),
  institution: p.institution,
  level: LEVELS[p.level] ?? "Licence",
  domain: p.institution === "IIT" ? "Informatique & sciences" : "Gestion & finance",
  name: p.name,
  tagline: p.description,
  keywords: p.career_outcomes.join(" · "),
  image: IMAGES[i % IMAGES.length]!,
  admission: p.admission_requirements,
  duration: p.duration_years,
});

/** Catalogue read from PostgreSQL through `GET /api/programs`. Filled in place by `loadCatalog()` before the app renders. */
export const FORMATIONS: Formation[] = [];

export async function loadCatalog(): Promise<void> {
  const programs = await api.programs();
  FORMATIONS.splice(0, FORMATIONS.length, ...programs.map(toFormation));
}

/** Legacy demo keys (“licence-info”, “prepa”, “gestion”) → id of the matching formation read from the database. */
export function resolveFormationId(key: string): string {
  const match: Record<string, (f: Formation) => boolean> = {
    "licence-info": (f) => f.institution === "IIT" && f.level === "Licence",
    prepa: (f) => f.institution === "IIT" && f.level === "Prépa",
    gestion: (f) => f.institution === "ISB",
  };
  return FORMATIONS.find((f) => f.id === key)?.id ?? (match[key] ? FORMATIONS.find(match[key])?.id : undefined) ?? key;
}
