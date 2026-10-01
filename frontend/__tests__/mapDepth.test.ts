import { describe, expect, it } from "vitest";
import {
  FLOOR_LIFT,
  linkDepth,
  needsRiser,
  nodeDepth,
  planeFilter,
  planeTransform,
} from "../lib/mapDepth";

describe("linkDepth", () => {
  it("puts a link incident to the selection on the raised focus plane", () => {
    const s = linkDepth(true, true, { kind: "along_line" });
    expect(s.plane).toBe("focus");
    expect(s.flow).toBe(true);
    expect(s.width).toBeGreaterThan(1.6);
    expect(s.opacity).toBe(1);
  });

  it("pushes every non-incident link to the floor, never the focus plane", () => {
    const s = linkDepth(false, true, { kind: "along_line" });
    expect(s.plane).toBe("floor");
    expect(s.flow).toBe(false);
    expect(s.opacity).toBeLessThan(0.5);
  });

  it("keeps all links on one plane when nothing is selected", () => {
    const s = linkDepth(false, false, { kind: "along_line" });
    expect(s.plane).toBe("focus");
    expect(s.opacity).toBe(1);
    expect(s.flow).toBe(false);
  });

  it("never animates a floor link, even for a transfer", () => {
    expect(linkDepth(false, true, { kind: "transfer" }).flow).toBe(false);
  });

  it("gives the focus plane a thicker line than the floor for both kinds", () => {
    for (const kind of ["along_line", "transfer"] as const) {
      expect(linkDepth(true, true, { kind }).width).toBeGreaterThan(
        linkDepth(false, true, { kind }).width
      );
    }
  });
});

describe("nodeDepth", () => {
  it("raises the selected station and its direct neighbours", () => {
    expect(nodeDepth(true, false, true).plane).toBe("focus");
    expect(nodeDepth(false, true, true).plane).toBe("focus");
  });

  it("sinks unrelated stations to the floor and drops their labels", () => {
    const d = nodeDepth(false, false, true);
    expect(d.plane).toBe("floor");
    expect(d.labelled).toBe(false);
    expect(d.opacity).toBeLessThan(1);
  });

  it("gives the selected station the largest marker", () => {
    const sel = nodeDepth(true, false, true);
    const nbr = nodeDepth(false, true, true);
    const other = nodeDepth(false, false, true);
    expect(sel.core).toBeGreaterThan(nbr.core);
    expect(nbr.core).toBeGreaterThan(other.core);
    expect(sel.halo).toBeGreaterThan(nbr.halo);
  });

  it("puts everything on one plane and labels it when idle", () => {
    const d = nodeDepth(false, false, false);
    expect(d.plane).toBe("focus");
    expect(d.labelled).toBe(true);
  });
});

describe("risers", () => {
  it("ties raised nodes to the floor only when a selection is active", () => {
    expect(needsRiser(true, false, true)).toBe(true);
    expect(needsRiser(false, true, true)).toBe(true);
    expect(needsRiser(false, false, true)).toBe(false);
    expect(needsRiser(true, false, false)).toBe(false);
  });
});

describe("plane geometry", () => {
  it("pushes the floor down and blurs it, leaving the focus plane flat", () => {
    expect(planeTransform("floor")).toBe(`translate(0 ${FLOOR_LIFT})`);
    expect(planeFilter("floor")).toBe("url(#depth-floor)");
    expect(planeTransform("focus")).toBeUndefined();
    expect(planeFilter("focus")).toBeUndefined();
  });

  it("lifts the floor by a visible but modest distance", () => {
    expect(FLOOR_LIFT).toBeGreaterThanOrEqual(8);
    expect(FLOOR_LIFT).toBeLessThanOrEqual(48);
  });
});