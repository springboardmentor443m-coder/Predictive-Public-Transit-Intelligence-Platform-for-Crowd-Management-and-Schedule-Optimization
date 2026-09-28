/**
 * The trunk palette is keyed on backend strings, so a mismatch or a bad sort
 * silently reorders the legend and mislabels every map track. These are cheap
 * invariants that were previously unchecked.
 */
import { describe, expect, it } from "vitest";
import {
  ALL_TRUNKS,
  compareLines,
  lineColor,
  lineCorridor,
  lineInk,
  lineStyle,
  orderedLines,
} from "../lib/lines";

describe("lineStyle", () => {
  it("resolves every trunk the palette declares", () => {
    for (const line of ALL_TRUNKS) {
      expect(lineStyle(line).color).toMatch(/^#[0-9A-Fa-f]{6}$/);
      expect(lineStyle(line).ink).toMatch(/^#[0-9A-Fa-f]{6}$/);
      expect(lineStyle(line).corridor).not.toBe("");
    }
  });

  it("returns the fallback for unknown and missing values", () => {
    for (const bad of [null, undefined, "", "ZZZ", "1/2/3/4/5"]) {
      expect(lineColor(bad)).toBe("#64748B");
      expect(lineInk(bad)).toBe("#475569");
    }
  });

  it("normalises case for lookup", () => {
    // Trunk keys arrive from the backend; a case drift must not fall through to
    // the grey fallback and silently mislabel a whole map track.
    expect(lineStyle("sir").color).toBe(lineStyle("SIR").color);
    expect(lineStyle("sir").corridor).toBe(lineStyle("SIR").corridor);
  });

  it("gives every trunk a distinct fill colour", () => {
    // Eight mutually distinguishable tracks on one map is the whole point of
    // the SIR/NQRW deviations documented in the module.
    const colors = ALL_TRUNKS.map(lineColor);
    expect(new Set(colors).size).toBe(ALL_TRUNKS.length);
  });

  it("keeps every ink variant distinct from its own fill", () => {
    for (const line of ALL_TRUNKS) {
      expect(lineInk(line)).not.toBe(lineColor(line));
    }
  });
});

describe("compareLines", () => {
  it("orders numbered trunks numerically before lettered ones", () => {
    const sorted = ["SIR", "A/C/E", "7", "4/5/6", "1/2/3", "L", "N/Q/R/W", "B/D/F/M"].sort(compareLines);
    expect(sorted).toEqual(["1/2/3", "4/5/6", "7", "A/C/E", "B/D/F/M", "L", "N/Q/R/W", "SIR"]);
  });

  it("is a total order (antisymmetric and reflexive)", () => {
    for (const a of ALL_TRUNKS) {
      expect(compareLines(a, a)).toBe(0);
      for (const b of ALL_TRUNKS) {
        // Antisymmetry: sign(a,b) must be the negation of sign(b,a).
        const ab = compareLines(a, b);
        const ba = compareLines(b, a);
        expect(Math.sign(ab) === 0).toBe(Math.sign(ba) === 0);
        expect(Math.sign(ab) === -Math.sign(ba)).toBe(true);
      }
    }
  });
});

describe("orderedLines", () => {
  it("de-duplicates, drops falsy values and sorts in MTA order", () => {
    expect(orderedLines(["SIR", "1/2/3", "SIR", null, undefined, "A/C/E", "1/2/3"])).toEqual([
      "1/2/3",
      "A/C/E",
      "SIR",
    ]);
  });

  it("returns an empty array for no input", () => {
    expect(orderedLines([])).toEqual([]);
  });

  it("is stable regardless of input order", () => {
    const input = ["L", "7", "4/5/6", "B/D/F/M", "1/2/3"];
    expect(orderedLines(input)).toEqual(orderedLines([...input].reverse()));
  });
});

describe("lineCorridor", () => {
  it("returns a description for known trunks and empty for unknown", () => {
    expect(lineCorridor("1/2/3")).toContain("Lexington");
    expect(lineCorridor("nope")).toBe("");
  });
});
