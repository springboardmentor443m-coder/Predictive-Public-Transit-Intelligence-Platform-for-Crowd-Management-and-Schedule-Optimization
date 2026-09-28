/**
 * Presentation metadata for MTA trunk routes.
 *
 * The backend groups the subway into trunk routes (`1/2/3`, `A/C/E`, ...) and
 * each trunk is what a station, a train and a map track are keyed on, so the
 * palette is keyed on the same strings. Colours follow the official MTA
 * "bullet" colours for the dominant service in each trunk.
 *
 * Two deliberate deviations from the official palette, both to keep 8 tracks
 * mutually distinguishable on one map:
 *   - `SIR` is officially orange, which is already `B/D/F/M`'s bullet colour.
 *   - `N/Q/R/W`'s official bullet yellow (#FCCC0A) is illegible as text on a
 *     light background, so `ink` is a darkened variant.
 * `color` is for fills (map tracks, dots, bars); `ink` is the accessible
 * foreground for text and icons on either theme.
 */

export interface LineStyle {
  /** Official bullet colour. For fills: map tracks, chips, bars, dots. */
  color: string;
  /** Darkened variant with enough contrast to use as text in either theme. */
  ink: string;
  /** Which numbered/lettered services the trunk covers, for the legend. */
  services: string;
  /** The real routes this trunk aggregates. */
  corridor: string;
}

const STYLES: Record<string, LineStyle> = {
  "1/2/3": {
    color: "#EE352E",
    ink: "#B3271F",
    services: "1 · 2 · 3",
    corridor: "Broadway–Seventh Ave, Broadway–Junction Blvd, Lexington Ave",
  },
  "4/5/6": {
    color: "#00933C",
    ink: "#00662A",
    services: "4 · 5 · 6",
    corridor: "Lexington Ave, Broadway–Junction Blvd, Pelham Bay Park",
  },
  "7": {
    color: "#B933AD",
    ink: "#8A2282",
    services: "7",
    corridor: "7 Avenue Express, Flushing Local",
  },
  "A/C/E": {
    color: "#0039A6",
    ink: "#002D7A",
    services: "A · C · E",
    corridor: "8 Avenue, 8 Avenue Express, Central Park West",
  },
  "B/D/F/M": {
    color: "#FF6319",
    ink: "#C24A08",
    services: "B · D · F · M",
    corridor: "Central Park West, 6 Avenue, 6 Avenue Express, Myrtle Ave",
  },
  L: {
    color: "#A7A9AC",
    ink: "#63666B",
    services: "L",
    corridor: "14 Street–Canarsie",
  },
  "N/Q/R/W": {
    color: "#FCCC0A",
    ink: "#8A6D00",
    services: "N · Q · R · W",
    corridor: "Broadway, BMT 63rd St, Brighton",
  },
  SIR: {
    color: "#0D8A8A",
    ink: "#0A6666",
    services: "SIR",
    corridor: "Staten Island Railway",
  },
};

/** Shown for any line the palette doesn't know, e.g. a newly imported feed. */
const FALLBACK: LineStyle = {
  color: "#64748B",
  ink: "#475569",
  services: "",
  corridor: "",
};

export function lineStyle(line: string | null | undefined): LineStyle {
  if (!line) return FALLBACK;
  return STYLES[line] ?? STYLES[line.toUpperCase()] ?? FALLBACK;
}

export function lineColor(line: string | null | undefined): string {
  return lineStyle(line).color;
}

export function lineInk(line: string | null | undefined): string {
  return lineStyle(line).ink;
}

export function lineCorridor(line: string | null | undefined): string {
  return lineStyle(line).corridor;
}

/** Stable sort key: numbered services first (ascending), then lettered. */
function lineRank(line: string): [number, number, string] {
  const numeric = line.match(/\d+/);
  if (numeric) return [0, parseInt(numeric[0], 10), line];
  return [1, 0, line];
}

/**
 * Order trunk routes the way the MTA numbers them rather than lexicographically,
 * which would otherwise put "1/2/3" and "4/5/6" after "7" and "A/C/E".
 */
export function compareLines(a: string, b: string): number {
  const [aGroup, aNum, aName] = lineRank(a);
  const [bGroup, bNum, bName] = lineRank(b);
  return aGroup - bGroup || aNum - bNum || aName.localeCompare(bName);
}

/** Unique trunks present in a set of line names, in MTA order. */
export function orderedLines(lines: Iterable<string | null | undefined>): string[] {
  const seen = new Set<string>();
  for (const line of lines) {
    if (line) seen.add(line);
  }
  return Array.from(seen).sort(compareLines);
}

/** Every trunk this palette can style, in MTA order. */
export const ALL_TRUNKS = Object.keys(STYLES).sort(compareLines);
