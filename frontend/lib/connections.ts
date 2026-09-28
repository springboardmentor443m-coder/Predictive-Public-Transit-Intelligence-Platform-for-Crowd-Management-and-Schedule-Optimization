import type { Station, StationConnection } from "./types";
import { orderedLines } from "./lines";

export interface Neighbor {
  code: string;
  name: string | null;
  line: string | null;
  kind: "along_line" | "transfer";
  vias: string;
}

/**
 * Index an undirected graph: each station code maps to every connection it
 * participates in. Shared, tested pure logic keeps MetroMap and the telemetry
 * "Connects to" panel looking at the same graph.
 */
export function adjacency(connections: StationConnection[]): Record<string, StationConnection[]> {
  const map: Record<string, StationConnection[]> = {};
  for (const c of connections) {
    (map[c.from_code] = map[c.from_code] ?? []).push(c);
    (map[c.to_code] = map[c.to_code] ?? []).push(c);
  }
  return map;
}

/** The stations reachable from `code` in one hop, resolved against the station list. */
export function neighborsFor(
  code: string,
  connections: StationConnection[],
  stations: Station[]
): Neighbor[] {
  const byCode = new Map(stations.map((s) => [s.code, s]));
  const out: Neighbor[] = [];
  for (const c of adjacency(connections)[code] ?? []) {
    const other = c.from_code === code ? c.to_code : c.from_code;
    const st = byCode.get(other);
    out.push({
      code: other,
      name: st?.name ?? null,
      line: st?.line ?? null,
      kind: c.kind,
      vias: c.vias,
    });
  }
  return out.sort((a, b) => {
    const byKind = (a.kind === b.kind ? 0 : a.kind === "along_line" ? -1 : 1);
    if (byKind) return byKind;
    return a.name?.localeCompare(b.name ?? "") ?? 0;
  });
}

/** Max vertex degree among a set of codes, using only along-line edges. */
function maxAlongDegree(adj: Record<string, string[]>, codes: string[]): number {
  return Math.max(0, ...codes.map((c) => (adj[c] ?? []).length));
}

/**
 * Linearise one fully-connected (within a trunk) component of along-line edges
 * into travel order using a simple forward walk from a path endpoint.
 */
function linearize(adj: Record<string, string[]>, start: string): string[] {
  const order: string[] = [];
  let prev: string | null = null;
  let cur = start;
  const guard = new Set<string>();
  while (cur && !guard.has(cur)) {
    guard.add(cur);
    order.push(cur);
    const next = (adj[cur] ?? []).find((n) => n !== prev) ?? null;
    prev = cur;
    cur = next ?? "";
  }
  return order;
}

export interface TrunkTrack {
  line: string;
  /** Contiguous station-code runs connected by real along-line edges. */
  segments: string[][];
  /** Codes on this trunk with no along-line edge to another monitored stop. */
  isolated: string[];
}

/**
 * Group stations by trunk and carve the real GTFS graph into contiguous,
 * travel-ordered segments. Drawing the schematic band only across these
 * segments — instead of blindly connecting every station in row order —
 * prevents phantom track between stations that are not actually adjacent
 * (e.g. L05 Bedford Av is not a neighbour of L08, so they must not be joined).
 */
export function trunkTracks(stations: Station[], connections: StationConnection[]): TrunkTrack[] {
  const byLine: Record<string, Station[]> = {};
  for (const s of stations) {
    (byLine[s.line] = byLine[s.line] ?? []).push(s);
  }

  const along = connections
    .filter((c) => c.kind === "along_line")
    .map((c) => [c.from_code, c.to_code] as const);

  const tracks: TrunkTrack[] = [];
  for (const line of orderedLines(Object.keys(byLine))) {
    const codes = byLine[line].map((s) => s.code);
    const codeSet = new Set(codes);
    const adj: Record<string, string[]> = {};
    for (const [a, b] of along) {
      if (codeSet.has(a) && codeSet.has(b)) {
        (adj[a] = adj[a] ?? []).push(b);
        (adj[b] = adj[b] ?? []).push(a);
      }
    }
    if (maxAlongDegree(adj, codes) > 2) {
      // Not a simple path in this subset; fall back to drawing one segment per
      // edge so nothing is silently reordered or dropped.
      const segments = along
        .filter(([a, b]) => codeSet.has(a) && codeSet.has(b))
        .map(([a, b]) => [a, b]);
      tracks.push({ line, segments, isolated: codes.filter((c) => !adj[c]) });
      continue;
    }
    const visited = new Set<string>();
    const segments: string[][] = [];
    for (const code of codes) {
      if (visited.has(code) || !adj[code]) continue;
      const start = (adj[code].length === 1 ? code : adj[code].find((n) => (adj[n] ?? []).length === 1)) ?? code;
      const order = linearize(adj, start);
      order.forEach((c) => visited.add(c));
      if (order.length >= 2) segments.push(order);
    }
    tracks.push({ line, segments, isolated: codes.filter((c) => !visited.has(c)) });
  }
  return tracks;
}