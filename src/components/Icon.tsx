/** Minimal stroke icons (Lucide-style paths) for glyphs not exported from Figma. */
const P: Record<string, string> = {
  video: "M16 10l5-3v10l-5-3M3 6h11a2 2 0 012 2v8a2 2 0 01-2 2H3a2 2 0 01-2-2V8a2 2 0 012-2z",
  mail: "M4 4h16a2 2 0 012 2v12a2 2 0 01-2 2H4a2 2 0 01-2-2V6a2 2 0 012-2zM22 7l-10 6L2 7",
  bell: "M6 8a6 6 0 0112 0c0 7 3 9 3 9H3s3-2 3-9M10.3 21a1.94 1.94 0 003.4 0",
  calendar: "M8 2v4M16 2v4M3 10h18M5 4h14a2 2 0 012 2v14a2 2 0 01-2 2H5a2 2 0 01-2-2V6a2 2 0 012-2z",
  folder: "M6 14l1.5-2.9A2 2 0 019.2 10H20a2 2 0 011.9 2.6l-1.6 5.2A2 2 0 0118.4 19H4a2 2 0 01-2-2V5a2 2 0 012-2h3.9a2 2 0 011.7.9l.8 1.2a2 2 0 001.7.9H18a2 2 0 012 2v2",
  clipboard: "M9 2h6a1 1 0 011 1v2a1 1 0 01-1 1H9a1 1 0 01-1-1V3a1 1 0 011-1zM16 4h2a2 2 0 012 2v14a2 2 0 01-2 2H6a2 2 0 01-2-2V6a2 2 0 012-2h2M9 14l2 2 4-4",
  filePlus: "M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8zM14 2v6h6M12 18v-6M9 15h6",
  checks: "M18 6L7 17l-5-5M22 10l-7.5 7.5L13 16",
  left: "M15 18l-6-6 6-6",
  right: "M9 18l6-6-6-6",
  shield: "M20 13c0 5-3.5 7.5-7.7 8.9a1 1 0 01-.6 0C7.5 20.5 4 18 4 13V6a1 1 0 011-1c2 0 4.5-1.2 6.2-2.7a1.2 1.2 0 011.6 0C14.5 3.8 17 5 19 5a1 1 0 011 1zM9 12l2 2 4-4",
  upload: "M12 3v12M7 8l5-5 5 5M5 21h14",
  users: "M16 21v-2a4 4 0 00-4-4H6a4 4 0 00-4 4v2M9 11a4 4 0 100-8 4 4 0 000 8zM22 21v-2a4 4 0 00-3-3.9M16 3.1a4 4 0 010 7.8",
  cap: "M22 10L12 5 2 10l10 5 10-5zM6 12v5c3 2 9 2 12 0v-5",
  workflow: "M3 3h6v6H3zM15 15h6v6h-6zM6 9v3a3 3 0 003 3h6",
  db: "M12 8c4.4 0 8-1.3 8-3s-3.6-3-8-3-8 1.3-8 3 3.6 3 8 3zM4 5v14c0 1.7 3.6 3 8 3s8-1.3 8-3V5M4 12c0 1.7 3.6 3 8 3s8-1.3 8-3",
  list: "M8 6h13M8 12h13M8 18h13M3 6h.01M3 12h.01M3 18h.01",
  bot: "M12 8V4H8M4 8h16a2 2 0 012 2v8a2 2 0 01-2 2H4a2 2 0 01-2-2v-8a2 2 0 012-2zM2 14h2M20 14h2M15 13v2M9 13v2",
  mic: "M12 2a3 3 0 00-3 3v7a3 3 0 006 0V5a3 3 0 00-3-3zM19 10v2a7 7 0 01-14 0v-2M12 19v3",
  plug: "M12 22v-5M9 8V2M15 8V2M18 8v4a6 6 0 01-12 0V8z",
  search: "M11 19a8 8 0 100-16 8 8 0 000 16zM21 21l-4.3-4.3",
  msg: "M21 15a2 2 0 01-2 2H7l-4 4V5a2 2 0 012-2h14a2 2 0 012 2z",
  chart: "M3 3v18h18M7 14l4-4 4 4 5-6",
  clock: "M12 22a10 10 0 100-20 10 10 0 000 20zM12 6v6l4 2",
  download: "M12 15V3M7 10l5 5 5-5M5 21h14",
  plus: "M12 5v14M5 12h14",
  dots: "M12 12h.01M19 12h.01M5 12h.01",
  refresh: "M3 12a9 9 0 019-9 9.75 9.75 0 016.7 2.7L21 8M21 3v5h-5M21 12a9 9 0 01-9 9 9.75 9.75 0 01-6.7-2.7L3 16M3 21v-5h5",
  lock: "M5 11h14a2 2 0 012 2v7a2 2 0 01-2 2H5a2 2 0 01-2-2v-7a2 2 0 012-2zM7 11V7a5 5 0 0110 0v4",
  file: "M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8zM14 2v6h6",
  ur: "M7 17L17 7M7 7h10v10",
  userplus: "M16 21v-2a4 4 0 00-4-4H6a4 4 0 00-4 4v2M9 11a4 4 0 100-8 4 4 0 000 8zM19 8v6M22 11h-6",
  save: "M19 21H5a2 2 0 01-2-2V5a2 2 0 012-2h11l5 5v11a2 2 0 01-2 2zM17 21v-8H7v8M7 3v5h8",
  check: "M20 6L9 17l-5-5",
  trend: "M22 7l-8.5 8.5-5-5L2 17M16 7h6v6",
};

export default function Icon({ name, size = 18, color = "currentColor" }: { name: keyof typeof P; size?: number; color?: string }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth={1.8} strokeLinecap="round" strokeLinejoin="round" aria-hidden="true" style={{ flex: "none" }}>
      <path d={P[name]} />
    </svg>
  );
}
