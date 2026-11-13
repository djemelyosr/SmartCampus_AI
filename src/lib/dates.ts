/** Date helpers in Tunisia time (UTC+1, no DST) — interviews are always shown in Tunis time. */
const TZ = "Africa/Tunis";
const cap = (s: string) => s.charAt(0).toUpperCase() + s.slice(1);

export const fmtDay = (iso: string) => cap(new Date(iso).toLocaleDateString("fr-FR", { weekday: "long", day: "numeric", month: "long", timeZone: TZ }));
export const fmtDayLong = (iso: string) => cap(new Date(iso).toLocaleDateString("fr-FR", { weekday: "long", day: "numeric", month: "long", year: "numeric", timeZone: TZ }));
export const fmtTime = (iso: string) => new Date(iso).toLocaleTimeString("fr-FR", { hour: "2-digit", minute: "2-digit", timeZone: TZ });
export const fmtDayMonth = (iso: string) => new Date(iso).toLocaleDateString("fr-FR", { day: "numeric", month: "long", timeZone: TZ });
export const fmtStamp = (iso: string) => `${fmtDayMonth(iso)} ${new Date(iso).toLocaleDateString("fr-FR", { year: "numeric", timeZone: TZ })} · ${fmtTime(iso)}`;

/** yyyy-mm-dd of an instant, in Tunis time. */
export const tunisDate = (iso: string | number | Date) => new Date(iso).toLocaleDateString("sv-SE", { timeZone: TZ });

export function addDays(dateStr: string, n: number): string {
  const d = new Date(`${dateStr}T12:00:00Z`);
  d.setUTCDate(d.getUTCDate() + n);
  return d.toISOString().slice(0, 10);
}

/** Monday (yyyy-mm-dd) of the week containing `dateStr`. */
export function mondayOf(dateStr: string): string {
  const dow = (new Date(`${dateStr}T12:00:00Z`).getUTCDay() + 6) % 7;
  return addDays(dateStr, -dow);
}

export const weekdayShort = (dateStr: string) => cap(new Date(`${dateStr}T12:00:00Z`).toLocaleDateString("fr-FR", { weekday: "short", timeZone: "UTC" }).replace(".", ""));
export const dayNumber = (dateStr: string) => Number(dateStr.slice(8, 10));
