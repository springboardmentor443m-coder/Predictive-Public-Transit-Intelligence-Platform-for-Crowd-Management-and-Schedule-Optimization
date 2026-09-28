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
  S: {
    color: "#808183",
    ink: "#5A5B5E",
    services: "S",
    corridor: "Franklin Ave, 42 St & Rockaway Park shuttles",
  },
};

/**
 * Route short names (the `vias` used by /crowd/connections) mapped to the trunk
 * bullet colour the route belongs to. An edge whose `vias` is "2;3" inherits the
 * 1/2/3 colour so the map reads like the real network.
 */
const ROUTE_TO_TRUNK: Record<string, string> = {
  "1": "1/2/3",
  "2": "1/2/3",
  "3": "1/2/3",
  "4": "4/5/6",
  "5": "4/5/6",
  "6": "4/5/6",
  "7": "7",
  "7X": "7",
  A: "A/C/E",
  C: "A/C/E",
  E: "A/C/E",
  B: "B/D/F/M",
  D: "B/D/F/M",
  F: "B/D/F/M",
  M: "B/D/F/M",
  FX: "B/D/F/M",
  L: "L",
  N: "N/Q/R/W",
  Q: "N/Q/R/W",
  R: "N/Q/R/W",
  W: "N/Q/R/W",
  SIR: "SIR",
  S: "S",
  H: "S",
};

/**
 * The trunk bullet colour for an edge's `vias` list ("2;3;4;5"), or null when
 * none of the listed routes is known.
 */
export function trunkForServices(vias: string | null | undefined): string | null {
  if (!vias) return null;
  const trunks = vias.split(";").map((r) => ROUTE_TO_TRUNK[r.trim().toUpperCase()]).filter(Boolean);
  const unique = Array.from(new Set(trunks));
  return unique[0] ?? null;
}

/**
 * Colour an edge between two stations. Prefers the trunk of the station you
 * arrive from when it is also painted on the edge (so a 4/5/6 stop's along-line
 * segment always draws green even when the vias also mention the 2/3), falling
 * back to the first known route listed in `vias`.
 */
export function edgeTrunk(vias: string | null | undefined, fromStationLine?: string | null): string | null {
  const direct =
    fromStationLine && Object.prototype.hasOwnProperty.call(STYLES, fromStationLine) ? fromStationLine : null;
  if (direct) {
    const routes = new Set(
      (vias ?? "").split(";").map((r) => ROUTE_TO_TRUNK[r.trim().toUpperCase()]).filter(Boolean)
    );
    if (routes.has(direct)) return direct;
  }
  return trunkForServices(vias) ?? direct;
}

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
