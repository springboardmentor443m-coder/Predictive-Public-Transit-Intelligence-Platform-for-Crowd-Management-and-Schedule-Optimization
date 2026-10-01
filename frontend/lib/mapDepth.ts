/**
 * Depth model for the connections ("focus") map.
 *
 * The focus view has one job: make a single junction's one-hop connections
 * unmistakable *without* destroying the context that tells you where that
 * junction sits. Fading the rest of the graph flat was not enough — a lower
 * opacity still reads as "same plane, unimportant", which made the view
 * functionally identical to the geographic map.
 *
 * Instead the map is built as two physically distinct planes stacked in Z:
 *
 *   FOCUS plane (z = +1, drawn last, at true coordinates)
 *       The selected station and its direct neighbours, plus the links that
 *       are genuinely incident to the selection.
 *
 *   FLOOR plane (z =  0, drawn first, pushed DOWN by `FLOOR_LIFT`)
 *       Everything else: the remaining stations and every remaining connection
 *       path, plus the real-network backdrop for orientation.
 *
 * The visual language that sells the depth is a combination of four cues,
 * because any single one alone is ambiguous:
 *
 *   1. Vertical separation — the floor is translated down `FLOOR_LIFT` px.
 *   2. Cast shadow    — the focus plane drops a shadow onto the floor below.
 *   3. Depth of field — the floor is blurred slightly (far = soft).
 *   4. Risers         — a vertical stem ties each lifted focus node to its own
 *      twin on the floor, so the eye reads "this came up out of that".
 *
 * These constants are exported (and unit-tested) because the legend, the
 * filters and the rendering all have to agree on them; a mismatch between the
 * stated lift and the drawn lift is exactly the kind of thing that silently
 * looks wrong.
 */

/** Pixels the floor plane is pushed below the focus plane. */
export const FLOOR_LIFT = 16;

/** Blur radius applied to the floor plane (depth-of-field cue). */
export const FLOOR_BLUR = 0.7;

/** Cast-shadow offset + blur for the lifted focus plane. */
export const FOCUS_SHADOW = { dy: FLOOR_LIFT, blur: 5, opacity: 0.55 } as const;

/** Which plane an element belongs to. */
export type DepthPlane = "focus" | "floor";

export interface DepthStyle {
  plane: DepthPlane;
  /** Stroke width for links. */
  width: number;
  /** Stroke width for the soft "skirt" line drawn under a focus link. */
  skirt: number;
  /** Overall opacity. */
  opacity: number;
  /** Gaussian glow/blur filter, or undefined for a flat element. */
  filter?: string;
  /** True when the element should carry the animated "flow" dash. */
  flow: boolean;
}

/**
 * Style for a connection link in the focus view.
 *
 * `active` means the link is genuinely incident to the selected station (see
 * `linkTouches`) — those are the only links that may be drawn on the focus
 * plane. Everything else is context and belongs to the floor.
 */
export function linkDepth(
  active: boolean,
  hasSelection: boolean,
  opts: { kind: "along_line" | "transfer" }
): DepthStyle {
  if (opts.kind === "transfer") {
    // Walking interchanges are secondary evidence: bright when they belong to
    // the selection, thin and quiet on the floor.
    return active
      ? { plane: "focus", width: 3.5, skirt: 6, opacity: 1, filter: "url(#glow-track)", flow: false }
      : { plane: "floor", width: 1.2, skirt: 0, opacity: 0.3, flow: false };
  }

  if (!hasSelection) {
    // Nothing selected: every link is the subject, all on one plane.
    return { plane: "focus", width: 3.5, skirt: 6, opacity: 1, flow: false };
  }

  return active
    ? { plane: "focus", width: 5.5, skirt: 12, opacity: 1, filter: "url(#glow-track)", flow: true }
    : { plane: "floor", width: 1.6, skirt: 0, opacity: 0.34, flow: false };
}

/**
 * Style for a station node in the focus view.
 *
 * `isSel` / `isNeighbour` decide the plane; `hasSelection` decides whether the
 * view is in focused mode at all (when idle, every station shares the plane so
 * the graph reads as one flat object).
 */
export function nodeDepth(
  isSel: boolean,
  isNeighbour: boolean,
  hasSelection: boolean
): { plane: DepthPlane; core: number; halo: number; opacity: number; labelled: boolean } {
  if (!hasSelection) {
    return { plane: "focus", core: 7, halo: 11, opacity: 1, labelled: true };
  }
  if (isSel) {
    return { plane: "focus", core: 9.5, halo: 20, opacity: 1, labelled: true };
  }
  if (isNeighbour) {
    return { plane: "focus", core: 8.5, halo: 15, opacity: 1, labelled: true };
  }
  return { plane: "floor", core: 4, halo: 7, opacity: 0.5, labelled: false };
}

/** Does a riser need to be drawn between this node's focus and floor twin? */
export function needsRiser(isSel: boolean, isNeighbour: boolean, hasSelection: boolean): boolean {
  return hasSelection && (isSel || isNeighbour);
}

/** SVG transform for a plane. */
export function planeTransform(plane: DepthPlane): string | undefined {
  return plane === "floor" ? `translate(0 ${FLOOR_LIFT})` : undefined;
}

/** Filter applied to a whole plane. */
export function planeFilter(plane: DepthPlane): string | undefined {
  return plane === "floor" ? "url(#depth-floor)" : undefined;
}