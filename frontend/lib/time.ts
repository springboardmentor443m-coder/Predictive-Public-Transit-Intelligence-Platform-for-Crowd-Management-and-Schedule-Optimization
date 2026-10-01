/**
 * Timezone helpers for the operations console.
 *
 * The product deliberately runs on two clocks and the app must never hide that:
 *
 * - **NYC** — every dataset, chart axis and simulated hour belongs to the New York
 *   operating day. This is the time that actually explains the numbers on screen.
 * - **IST** — the reviewer's own wall clock. Useful for "when did I open this", but
 *   it is *not* the time the data is describing.
 *
 * Rendering both, each explicitly labelled, stops the single most common source of
 * confusion: a clock reading 14:20 next to a "morning peak" chart whose x-axis says
 * 07:00, with nothing stating which timezone either belongs to.
 */

export const NYC_TZ = "America/New_York";
export const IST_TZ = "Asia/Kolkata";

/** India has no daylight saving, so IST is always UTC+05:30. */
export const IST_LABEL = "IST";

export interface ZonedClock {
  /** e.g. "14:23:05" */
  time: string;
  /** Short zone label, e.g. "EDT" / "EST" / "IST". */
  zone: string;
  /** Offset label, e.g. "UTC-4" / "UTC+5:30". */
  offset: string;
}

function parts(date: Date, timeZone: string, timeZoneName: "short" | "shortOffset") {
  const fmt = new Intl.DateTimeFormat("en-US", {
    timeZone,
    hour12: false,
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
    timeZoneName,
  });
  const out: Record<string, string> = {};
  for (const p of fmt.formatToParts(date)) out[p.type] = p.value;
  return out;
}

/** Abbreviation for the zone at this instant: "EDT" in summer, "EST" in winter. */
function zoneAbbrev(date: Date, timeZone: string): string {
  return parts(date, timeZone, "short").timeZoneName ?? "";
}

/** `UTC-4`, `UTC+5:30` — normalised from the runtime's `shortOffset` output. */
function offsetLabel(timeZone: string, date: Date): string {
  const p = parts(date, timeZone, "shortOffset").timeZoneName ?? "";
  // Intl emits "GMT-4" or "GMT+5:30".
  const m = p.match(/GMT([+-])(\d{1,2})(?::(\d{2}))?/);
  if (!m) return "UTC";
  const [, sign, hh, mm] = m;
  return `UTC${sign}${Number(hh)}${mm ? `:${mm}` : ""}`;
}

/** Current clock reading in New York, including the EDT/EST daylight-saving label. */
export function nycClock(date: Date = new Date()): ZonedClock {
  const p = parts(date, NYC_TZ, "short");
  return {
    time: `${p.hour}:${p.minute}:${p.second}`,
    zone: zoneAbbrev(date, NYC_TZ) || "ET",
    offset: offsetLabel(NYC_TZ, date),
  };
}

/** Current clock reading in India Standard Time (fixed UTC+05:30). */
export function istClock(date: Date = new Date()): ZonedClock {
  const p = parts(date, IST_TZ, "short");
  return {
    time: `${p.hour}:${p.minute}:${p.second}`,
    zone: IST_LABEL,
    offset: offsetLabel(IST_TZ, date),
  };
}

/** Both clocks, so a caller can render them together without recomputing. */
export function dualClock(date: Date = new Date()): { ist: ZonedClock; nyc: ZonedClock } {
  return { ist: istClock(date), nyc: nycClock(date) };
}

/** Hour label (e.g. "07:00") for a data timestamp, always in New York time. */
export function nycHourLabel(d: Date): string {
  return new Intl.DateTimeFormat("en-GB", {
    timeZone: NYC_TZ,
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
  }).format(d);
}

/** Full date + hour label in New York time, for tooltips that need the day too. */
export function nycDateHourLabel(d: Date): string {
  return new Intl.DateTimeFormat("en-GB", {
    timeZone: NYC_TZ,
    day: "2-digit",
    month: "short",
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
  }).format(d);
}