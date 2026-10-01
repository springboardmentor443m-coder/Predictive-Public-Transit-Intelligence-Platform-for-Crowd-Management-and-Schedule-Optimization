import { describe, expect, it } from "vitest";
import { render, fireEvent } from "@testing-library/react";
import MetroMap from "../components/MetroMap";
import { FLOOR_LIFT } from "../lib/mapDepth";
import type { NetworkPayload, Station, StationConnection } from "../lib/types";

/**
 * Structural tests for the connections view's depth stack.
 *
 * These assert the *shape* of the rendered SVG rather than pixels: which
 * elements landed on the floor plane, that the floor is actually displaced and
 * blurred, and that the lifted layer is painted. A pixel-free test cannot tell
 * whether the view looks good, but it reliably catches the failure mode that
 * matters here - a plane silently reverting to flat, or an "active" link
 * leaking onto the focus plane.
 */

const station = (id: string, code: string, line: string): Station => ({
  id,
  code,
  name: `${id} Station`,
  line,
  zone: "1",
  lat: 40.7,
  lng: -74,
  capacity_per_hour: 1000,
});

const A = station("A", "AAA", "1");
const B = station("B", "BBB", "1");
const C = station("C", "CCC", "2");

/** A -> B is the pair the selection owns; B -> C is genuine but unrelated. */
const CONNECTIONS: StationConnection[] = [
  { from_code: "AAA", to_code: "BBB", vias: "1", kind: "along_line" },
  { from_code: "BBB", to_code: "CCC", vias: "2", kind: "along_line" },
];

const NETWORK: NetworkPayload = {
  stations: [
    { c: "AAA", n: "A", lat: 40.7, lng: -74 },
    { c: "BBB", n: "B", lat: 40.75, lng: -73.98 },
    { c: "CCC", n: "C", lat: 40.8, lng: -73.95 },
    { c: "DDD", n: "D", lat: 40.85, lng: -73.9 },
  ],
  segments: [
    { a: "AAA", b: "BBB", r: "1" },
    { a: "BBB", b: "CCC", r: "2" },
  ],
  monitored: ["AAA", "BBB", "CCC"],
};

/** The view toggle is internal state, so the harness clicks it first. */
function renderConnections(selected?: string): string {
  const result = render(
    <MetroMap
      stations={[A, B, C]}
      live={[]}
      connections={CONNECTIONS}
      network={NETWORK}
      selected={selected}
      onSelect={() => {}}
    />
  );
  fireEvent.click(result.getByRole("button", { name: /connections/i }));
  const html = result.container.innerHTML;
  result.unmount();
  return html;
}

describe("connections view depth stack", () => {
  it("displaces and blurs the floor plane", () => {
    const html = renderConnections("A");
    expect(html).toContain(`translate(0 ${FLOOR_LIFT})`);
    expect(html).toContain("url(#depth-floor)");
  });

  it("draws a cast shadow for the raised plane", () => {
    expect(renderConnections("A")).toContain("url(#depth-lift)");
  });

  it("renders risers tying the lifted stations to their floor twins", () => {
    const html = renderConnections("A");
    // A (the selection) and B (its direct neighbour) each get a riser.
    expect(html).toContain(`data-riser="${A.code}"`);
    expect(html).toContain(`data-riser="${B.code}"`);
    expect(html).not.toContain(`data-riser="${C.code}"`);
    expect(html).toContain("depth-spotlight");
  });

  it("animates only the link the selection owns", () => {
    // A->B is incident to A. B->C is not, so it must not animate.
    expect(renderConnections("A").match(/map-flow/g) ?? []).toHaveLength(1);
  });

  it("keeps unrelated stations and links off the raised plane", () => {
    const html = renderConnections("A");
    // C is neither the selection nor a neighbour of A, so it sits on the floor.
    expect(html).toContain(`data-station="${C.code}" data-plane="floor"`);
    expect(html).toContain(`data-station="${A.code}" data-plane="focus"`);
    expect(html).toContain(`data-station="${B.code}" data-plane="focus"`);
    // ...and so does the B->C link it belongs to.
    expect(html).toMatch(
      /data-plane="floor" data-link="BBB-CCC"/
    );
    expect(html).toMatch(/data-plane="focus" data-link="AAA-BBB"/);
  });

  it("flattens into a single plane when nothing is selected", () => {
    const html = renderConnections(undefined);
    expect(html).not.toContain("url(#depth-lift)");
    expect(html).not.toContain("data-riser=");
    expect(html).not.toContain("map-flow");
    expect(html).not.toContain("translate(0 ");
    // Every station is on the single plane and still labelled.
    expect(html).not.toContain(`data-plane="floor" data-station`);
    expect(html).toContain(`data-station="${C.code}" data-plane="focus"`);
  });

  it("keeps the geographic view free of the depth stack", () => {
    const result = render(
      <MetroMap
        stations={[A, B, C]}
        live={[]}
        connections={CONNECTIONS}
        network={NETWORK}
        selected="A"
        onSelect={() => {}}
      />
    );
    fireEvent.click(result.getByRole("button", { name: /geographic/i }));
    const html = result.container.innerHTML;
    result.unmount();
    expect(html).toContain("url(#grid)");
    expect(html).not.toContain("url(#depth-floor)");
    expect(html).not.toContain("url(#depth-lift)");
  });
});