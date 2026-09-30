import { describe, expect, it } from "vitest";
import type { Station, StationConnection } from "../lib/types";
import { adjacency, linkTouches, neighborsFor, trunkTracks } from "../lib/connections";
import { edgeTrunk, lineColor, trunkForServices } from "../lib/lines";

const STATIONS: Station[] = [
  { id: "s1", code: "L01", name: "14 St-8 Av", line: "L", zone: "Z1", capacity_per_hour: 9000 },
  { id: "s2", code: "L02", name: "14 St-6 Av", line: "L", zone: "Z1", capacity_per_hour: 9000 },
  { id: "s3", code: "L03", name: "Union Sq-14 St", line: "L", zone: "Z1", capacity_per_hour: 9000 },
  { id: "s4", code: "L08", name: "Bedford Av", line: "L", zone: "Z1", capacity_per_hour: 9000 },
  { id: "s5", code: "127", name: "Times Sq-42 St", line: "1/2/3", zone: "Z1", capacity_per_hour: 11000 },
  { id: "s6", code: "128", name: "34 St-Penn Station", line: "1/2/3", zone: "Z1", capacity_per_hour: 11000 },
  { id: "s7", code: "631", name: "Grand Central-42 St", line: "4/5/6", zone: "Z1", capacity_per_hour: 11000 },
  { id: "s8", code: "635", name: "14 St-Union Sq", line: "4/5/6", zone: "Z1", capacity_per_hour: 11000 },
];

const CONNECTIONS: StationConnection[] = [
  { from_code: "L01", to_code: "L02", kind: "along_line", vias: "L" },
  { from_code: "L02", to_code: "L03", kind: "along_line", vias: "L" },
  { from_code: "127", to_code: "128", kind: "along_line", vias: "1;2;3" },
  { from_code: "127", to_code: "631", kind: "transfer", vias: "transfer" },
  { from_code: "635", to_code: "L03", kind: "transfer", vias: "transfer" },
];

describe("adjacency", () => {
  it("indexes every bidirectional edge", () => {
    const g = adjacency(CONNECTIONS);
    expect(g["L02"]).toHaveLength(2);
    expect(g["L01"]).toHaveLength(1);
    expect(g["L03"]).toHaveLength(2);
    expect(g["zzz"]).toBeUndefined();
  });
});

describe("neighborsFor", () => {
  it("resolves neighbour station names and kinds", () => {
    const n = neighborsFor("L03", CONNECTIONS, STATIONS);
    expect(n.map((x) => x.name).sort()).toEqual(["14 St-6 Av", "14 St-Union Sq"]);
    const transfer = n.find((x) => x.kind === "transfer");
    expect(transfer?.code).toBe("635");
    const along = n.find((x) => x.kind === "along_line");
    expect(along?.vias).toBe("L");
  });

  it("sorts along-line before transfer neighbours", () => {
    const kinds = neighborsFor("L03", CONNECTIONS, STATIONS).map((x) => x.kind);
    expect(kinds[0]).toBe("along_line");
  });

  it("returns an empty list for an unknown station", () => {
    expect(neighborsFor("ZZZ", CONNECTIONS, STATIONS)).toEqual([]);
  });
});

describe("trunkTracks", () => {
  it("keeps L01–L02–L03 as one contiguous segment and Bedford Av isolated", () => {
    const track = trunkTracks(STATIONS, CONNECTIONS).find((t) => t.line === "L");
    expect(track).toBeDefined();
    expect(track?.segments).toEqual([["L01", "L02", "L03"]]);
    expect(track?.isolated).toEqual(["L08"]);
  });

  it("does not invent track between stations that are not adjacent", () => {
    const track = trunkTracks(STATIONS, CONNECTIONS).find((t) => t.line === "L");
    const joined = (track?.segments ?? []).flat();
    expect(joined).not.toContain("L08");
  });

  it("leaves 1/2/3 to its single segment", () => {
    const track = trunkTracks(STATIONS, CONNECTIONS).find((t) => t.line === "1/2/3");
    expect(track?.segments).toEqual([["127", "128"]]);
  });
});

describe("trunkForServices", () => {
  it("maps route short names to trunk bullets", () => {
    expect(trunkForServices("2;3")).toBe("1/2/3");
    expect(trunkForServices("4;5")).toBe("4/5/6");
    expect(trunkForServices("N;W")).toBe("N/Q/R/W");
    expect(trunkForServices("E;F;FX")).toBe("A/C/E");
  });

  it("returns null for unknown or missing vias", () => {
    expect(trunkForServices("BG;XZ")).toBeNull();
    expect(trunkForServices("")).toBeNull();
    expect(trunkForServices(null)).toBeNull();
  });
});

describe("edgeTrunk", () => {
  it("prefers the from-station trunk when it is painted on the edge", () => {
    // Grand Central (4/5/6) to Times Sq via the 42 St Shuttle replacement:
    // the "4;5;6" via on a 4/5/6 station resolves to the green trunk.
    expect(edgeTrunk("1;2;3", "4/5/6")).toBe("1/2/3"); // via rules
    expect(edgeTrunk("4;5", "1/2/3")).toBe("4/5/6");
  });

  it("falls back to vias when the from-station trunk is not involved", () => {
    expect(edgeTrunk("B;Q", "4/5/6")).toBe("B/D/F/M");
  });

  it("returns the from-station trunk for transfer edges with 'transfer' vias", () => {
    expect(edgeTrunk("transfer", "L")).toBe("L");
  });

  it("can be fed through lineColor for paste-safe colours", () => {
    const red = lineColor(edgeTrunk("1;2;3", null) ?? "1/2/3");
    expect(red).toBe("#EE352E");
  });
});

describe("linkTouches", () => {
  it("lights an edge only when the selected code is one of its endpoints", () => {
    expect(linkTouches("L03", "L02", "L03")).toBe(true);
    expect(linkTouches("L03", "L03", "L02")).toBe(true);
    expect(linkTouches("L03", "L01", "L02")).toBe(false);
  });

  it("never lights an edge that merely passes through a neighbour", () => {
    // Chain: L01 - L02 - L03. With L03 selected, L02 is its neighbour, so the
    // L01-L02 edge touches a neighbour but is NOT incident to L03 and must dim.
    const neighbours = new Set(neighborsFor("L03", CONNECTIONS, STATIONS).map((n) => n.code));
    expect(neighbours.has("L02")).toBe(true);
    expect(linkTouches("L03", "L01", "L02")).toBe(false);
    // ...while L03's own link stays lit.
    expect(linkTouches("L03", "L02", "L03")).toBe(true);
  });

  it("returns false when nothing is selected", () => {
    expect(linkTouches("", "L02", "L03")).toBe(false);
    expect(linkTouches(null, "L02", "L03")).toBe(false);
    expect(linkTouches(undefined, "L02", "L03")).toBe(false);
  });

  it("agrees with the real edge set for every station in the fixture", () => {
    for (const s of STATIONS) {
      for (const c of CONNECTIONS) {
        const expected = c.from_code === s.code || c.to_code === s.code;
        expect(linkTouches(s.code, c.from_code, c.to_code)).toBe(expected);
      }
    }
  });
});