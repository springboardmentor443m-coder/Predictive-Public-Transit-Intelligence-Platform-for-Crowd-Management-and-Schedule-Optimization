import { useMemo, useState } from "react";
import { congestionColor } from "./StatusBadge";
import { edgeTrunk, lineColor, lineCorridor, lineStyle, orderedLines, trunkForServices } from "../lib/lines";
import { linkTouches } from "../lib/connections";
import {
  FLOOR_LIFT,
  FOCUS_SHADOW,
  FLOOR_BLUR,
  linkDepth,
  needsRiser,
  nodeDepth,
  planeFilter,
  planeTransform,
  type DepthPlane,
} from "../lib/mapDepth";
import ConnectionList from "./ConnectionList";
import type { Station, LiveCrowdSnapshot, StationConnection, NetworkPayload } from "../lib/types";

/**
 * Three views share this component:
 *
 * 1. `schematic` (default) — the original one-track-per-trunk diagram. Stations
 *    are laid out in the data's stored order and every trunk is drawn as a
 *    continuous line so no route disappears. This view does NOT depend on the
 *    connection graph.
 *
 * 2. `geographic` — a real-world "connection map". The COMPLETE NYC rail network
 *    (every GTFS station and rail segment, ~496 stops / 578 segments) is drawn
 *    as the faint base layer so every route is present, and the monitored
 *    stations are overlaid with live congestion. Selecting a station brightens
 *    exactly its one-hop real connections.
 *
 * 3. `connections` — a dedicated *focus* layer on top of the same true
 *    lat/long projection. It strips the map back to the monitored graph only,
 *    so the one-to-one link structure is unmistakable: with nothing selected
 *    the whole graph is drawn bright, and clicking a station keeps its true
 *    position while everything unrelated drops away and each direct link is
 *    lit, ringed and labelled with the routes that serve it. A side panel
 *    repeats the same links as a list.
 *
 * Views 2 and 3 are alternatives layered on the geographic projection; neither
 * mutates the schematic or the existing geographic rendering.
 */
const TRACK_BAND = 80;
const TRACK_TOP = 70;
const TRACK_BOTTOM = 64;
const LABEL_GUTTER = 84;
const MIN_STATION_GAP = 76;
const MIN_W = 760;
const LABEL_CHAR_W = 5.6;

// Geographic projection target (viewBox units, before padding).
const GEO_W = 1280;
const GEO_PAD = 64;

interface MetroMapProps {
  stations?: Station[];
  live?: LiveCrowdSnapshot[];
  connections?: StationConnection[];
  network?: NetworkPayload | null;
  selected?: string | null;
  onSelect?: (stationId: string) => void;
}

interface Projection {
  byCode: Record<string, { x: number; y: number }>;
  w: number;
  h: number;
}

const nodeKey = (s: Station) => s.id;

export default function MetroMap({
  stations = [],
  live = [],
  connections = [],
  network = null,
  selected,
  onSelect,
}: MetroMapProps) {
  const [filterLine, setFilterLine] = useState("all");
  const [view, setView] = useState<"schematic" | "geographic" | "connections">("schematic");

  const liveById: Record<string, LiveCrowdSnapshot> = Object.fromEntries(
    (live || []).map((s) => [s.station_id, s])
  );

  const byCode = useMemo(
    () => Object.fromEntries(stations.map((s) => [s.code, s])),
    [stations]
  );

  // Group stations by trunk route for filtering/legend purposes.
  const lines: Record<string, Station[]> = {};
  stations.forEach((s) => {
    (lines[s.line] = lines[s.line] || []).push(s);
  });
  const lineNames = orderedLines(Object.keys(lines));
  const activeLineNames =
    view === "schematic" && filterLine === "all"
      ? lineNames
      : view === "schematic"
        ? lineNames.filter((l) => l === filterLine)
        : lineNames;

  // --- Schematic geometry -------------------------------------------------
  const maxStops = Math.max(1, ...activeLineNames.map((ln) => lines[ln].length));
  const W = Math.max(MIN_W, LABEL_GUTTER * 2 + (maxStops - 1) * MIN_STATION_GAP);
  const H = TRACK_TOP + Math.max(1, activeLineNames.length) * TRACK_BAND + TRACK_BOTTOM;

  const trackY: Record<string, number> = {};
  activeLineNames.forEach((ln, i) => {
    trackY[ln] = TRACK_TOP + i * TRACK_BAND + TRACK_BAND / 2;
  });

  const innerW = W - LABEL_GUTTER * 2;

  function xFor(idx: number, total: number): number {
    if (total <= 1) return LABEL_GUTTER + innerW / 2;
    return LABEL_GUTTER + (idx * innerW) / (total - 1);
  }

  /** Longest label that fits the gap between neighbouring stations. */
  function fitLabel(name: string, total: number): string {
    const gap = total <= 1 ? innerW : innerW / (total - 1);
    const maxChars = Math.max(6, Math.floor(gap / LABEL_CHAR_W));
    return name.length > maxChars ? name.slice(0, maxChars - 1).trimEnd() + "…" : name;
  }

  // --- Geographic geometry ------------------------------------------------
  // Project against the FULL network (496 stations) so the base map covers the
  // whole subway; monitored dots fall inside that frame. Falls back to the
  // monitored stations if /crowd/network hasn't loaded yet.
  const geoPoints = useMemo(() => {
    if (network?.stations?.length) {
      return network.stations.map((s) => ({ code: s.c, lat: s.lat, lng: s.lng }));
    }
    return stations
      .filter((s) => typeof s.lat === "number" && typeof s.lng === "number")
      .map((s) => ({ code: s.code, lat: s.lat as number, lng: s.lng as number }));
  }, [network, stations]);

  const geo = useMemo<Projection>(() => {
    if (geoPoints.length === 0) return { byCode: {}, w: MIN_W, h: 400 };
    const lats = geoPoints.map((s) => s.lat);
    const lngs = geoPoints.map((s) => s.lng);
    const minLat = Math.min(...lats);
    const maxLat = Math.max(...lats);
    const minLng = Math.min(...lngs);
    const maxLng = Math.max(...lngs);
    const aspect = Math.cos(((minLat + maxLat) / 2) * (Math.PI / 180));
    const spanX = (maxLng - minLng) * aspect;
    const spanY = maxLat - minLat;
    const pad = GEO_PAD;
    const scale = Math.min((GEO_W - pad * 2) / spanX, (GEO_W * 0.72 - pad * 2) / spanY);
    const w = pad * 2 + spanX * scale;
    const h = pad * 2 + spanY * scale;
    const byCode: Projection["byCode"] = {};
    for (const s of geoPoints) {
      byCode[s.code] = {
        x: pad + (s.lng - minLng) * aspect * scale,
        y: pad + (maxLat - s.lat) * scale,
      };
    }
    return { byCode, w, h };
  }, [geoPoints]);

  // Connection graph facts only needed by the geographic view.
  const selectedStation = selected ? stations.find((s) => s.id === selected) : undefined;
  const selectedCode = selectedStation && connections.length ? selectedStation.code : "";
  const neighborsOfSelected = useMemo(() => {
    if (!selectedCode) return new Set<string>();
    const n = new Set<string>();
    for (const c of connections) {
      if (c.from_code === selectedCode) n.add(c.to_code);
      if (c.to_code === selectedCode) n.add(c.from_code);
    }
    return n;
  }, [selectedCode, connections]);

  const graphCodes = useMemo(() => {
    const n = new Set<string>();
    for (const c of connections) {
      n.add(c.from_code);
      n.add(c.to_code);
    }
    return n;
  }, [connections]);

  const monitoredCodes = useMemo(
    () => new Set(network?.monitored ?? []),
    [network?.monitored]
  );

  function viaLabel(vias: string): string {
    return vias.replace(/;/g, "/");
  }

  const isSchematic = view === "schematic";
  const isConnections = view === "connections";
  const isGeoLike = view === "geographic" || isConnections;

  const viewW = isGeoLike ? geo.w : W;
  const viewH = isGeoLike ? geo.h : H;

  // Paint order for the map views: dimmed stations first so a selected station
  // and its lit neighbours are never hidden underneath an overlapping ghost.
  const geoNodeOrder = useMemo(() => {
    if (isSchematic) return stations;
    const rank = (s: Station): number => {
      if (selected === s.id) return 2;
      if (selectedCode !== "" && neighborsOfSelected.has(s.code)) return 1;
      return 0;
    };
    return [...stations].sort((a, b) => rank(a) - rank(b));
  }, [stations, isSchematic, selected, selectedCode, neighborsOfSelected]);

  const nodeList = isSchematic ? activeLineNames.flatMap((ln) => lines[ln]) : geoNodeOrder;

  // A link counts as "lit" only when the selected station is one of its two
  // endpoints. See `linkTouches` — testing `neighborsOfSelected.has(...)` would
  // also light up every edge that merely *touches* a neighbour, pulling
  // unrelated paths into the highlight.
  const linksSelected = useMemo(
    () => (a: string, b: string): boolean => linkTouches(selectedCode, a, b),
    [selectedCode]
  );

  /**
   * Draws one station. The caller supplies the depth plane, so the focus view
   * can paint its floor nodes and its lifted nodes in the correct z order while
   * sharing one definition of what a station looks like.
   */
  const renderNode = (s: Station, plane: DepthPlane) => {
    const snap = liveById[s.id];
    const pct = snap?.occupancy_pct ?? 0;
    const col = congestionColor(pct);
    const isSel = selected === s.id;
    let x: number;
    let y: number;
    if (!isSchematic) {
      const p = geo.byCode[s.code];
      if (!p) return null;
      x = p.x;
      y = p.y;
    } else {
      const stops = lines[s.line];
      const idx = stops.findIndex((st) => st.id === s.id);
      x = xFor(idx, stops.length);
      y = trackY[s.line];
    }

    const inGraph = graphCodes.has(s.code);
    const onSelectedPath = selectedCode !== "" && neighborsOfSelected.has(s.code);
    const showLabel = isSchematic || isConnections || isSel || inGraph;
    const isDirect = isConnections && onSelectedPath;
    const tip = `${s.name} (${s.id}) · Line: ${s.line} · Occupancy: ${pct}% · Congestion: ${
      snap?.congestion_level || "low"
    }`;

    /* ---- Connections view: depth-plane aware node ---- */
    if (isConnections) {
      const d = nodeDepth(isSel, onSelectedPath, selectedCode !== "");
      const onFloor = d.plane === "floor";

      return (
        <g
          key={nodeKey(s)}
          onClick={() => onSelect && onSelect(s.id)}
          opacity={d.opacity}
          data-station={s.code}
          data-plane={d.plane}
          className="cursor-pointer group"
        >
          <title>{tip}</title>
          <circle cx={x} cy={y} r={10} fill="transparent" />

          {onFloor ? (
            /* Floor station: a small solid pip. Deliberately label-free — the
               floor is context, and 59 names would bury the lifted layer. */
            <>
              <circle
                cx={x}
                cy={y}
                r={d.core + 2.5}
                fill={col}
                opacity={0.12}
                pointerEvents="none"
              />
              <circle cx={x} cy={y} r={d.core} fill={col} pointerEvents="none" />
              <circle
                cx={x}
                cy={y}
                r={d.core}
                fill="none"
                stroke="#0f172a"
                strokeWidth={1.5}
                pointerEvents="none"
              />
            </>
          ) : (
            <>
              {/* Dashed riser collar: catches the eye where the node meets
                  the shadow it casts on the floor. */}
              <circle
                cx={x}
                cy={y}
                r={d.halo + 3}
                fill="none"
                stroke="#f8fafc"
                strokeWidth={0.75}
                strokeDasharray="2 5"
                opacity={0.3}
                pointerEvents="none"
              />
              {/* Selection ring. */}
              {isSel && (
                <circle
                  cx={x}
                  cy={y}
                  r={d.halo + 5}
                  fill="none"
                  className="map-select-ring"
                  strokeWidth={2}
                  strokeDasharray="4 3"
                  pointerEvents="none"
                />
              )}
              {/* Direct-neighbour ring. */}
              {onSelectedPath && (
                <circle
                  cx={x}
                  cy={y}
                  r={d.halo}
                  fill="none"
                  stroke={isDirect ? "#ffffff" : col}
                  strokeWidth={isDirect ? 2 : 1.5}
                  opacity={0.95}
                  pointerEvents="none"
                />
              )}
              {isDirect && (
                <circle
                  cx={x}
                  cy={y}
                  r={d.halo - 1}
                  fill="none"
                  stroke={col}
                  strokeWidth={1}
                  className="map-select-ring"
                  opacity={0.6}
                  pointerEvents="none"
                />
              )}
              {/* Congestion halo. */}
              <circle
                cx={x}
                cy={y}
                r={d.halo}
                fill={col}
                opacity={isSel ? 0.5 : 0.4}
                filter="url(#glow-node)"
                pointerEvents="none"
              />
              {/* Core dot. */}
              <circle
                cx={x}
                cy={y}
                r={d.core}
                fill={col}
                className="map-node-ring transition-transform group-hover:scale-125"
                strokeWidth={isSel ? 3 : 2.5}
                stroke={isSel ? "#ffffff" : undefined}
              />
              {/* Name + live occupancy, on the raised layer only. */}
              {d.labelled && (
                <>
                  <text
                    x={x}
                    y={y - d.core - 8}
                    textAnchor="middle"
                    fontSize={isSel ? 11 : 9.5}
                    fontWeight={isSel ? 800 : 700}
                    fill={isSel ? "#ffffff" : "#e2e8f0"}
                    className="map-label select-none"
                    stroke="#020617"
                    strokeWidth={2.5}
                    paintOrder="stroke"
                    pointerEvents="none"
                  >
                    {s.name.length > 20 ? s.name.slice(0, 19) + "…" : s.name}
                  </text>
                  <text
                    x={x}
                    y={y + d.core + 14}
                    textAnchor="middle"
                    fontSize={9.5}
                    fontWeight={800}
                    fill={col}
                    className="font-mono select-none"
                    stroke="#020617"
                    strokeWidth={2.5}
                    paintOrder="stroke"
                    pointerEvents="none"
                  >
                    {pct}%
                  </text>
                </>
              )}
            </>
          )}
        </g>
      );
    }

    /* ---- Schematic / geographic view: unchanged flat rendering ---- */
    const dimmed = isGeoLike && selectedCode !== "" && !isSel && !onSelectedPath;
    const coreR = isSel ? 9 : 7;
    const haloR = isSel ? 15 : 11;

    return (
      <g
        key={nodeKey(s)}
        onClick={() => onSelect && onSelect(s.id)}
        opacity={dimmed ? 0.45 : 1}
        className="cursor-pointer group"
      >
        <title>{tip}</title>
        <circle cx={x} cy={y} r={10} fill="transparent" />
        {isSel && (
          <circle
            cx={x}
            cy={y}
            r={16}
            fill="none"
            className="map-select-ring"
            strokeWidth={2}
            strokeDasharray="4 3"
            pointerEvents="none"
          />
        )}
        {isGeoLike && onSelectedPath && (
          <circle
            cx={x}
            cy={y}
            r={12}
            fill="none"
            stroke={col}
            strokeWidth={1.5}
            opacity={0.8}
            pointerEvents="none"
          />
        )}
        <circle
          cx={x}
          cy={y}
          r={haloR}
          fill={col}
          opacity={isSel ? 0.45 : 0.35}
          filter="url(#glow-node)"
          pointerEvents="none"
        />
        <circle
          cx={x}
          cy={y}
          r={coreR}
          fill={col}
          className="map-node-ring transition-transform group-hover:scale-125"
          strokeWidth={isSel ? 3 : 2.5}
          stroke={isSel ? "#ffffff" : undefined}
        />
        {isSchematic ? (
          <>
            <text
              x={x}
              y={y - 16}
              textAnchor="middle"
              fontSize={10}
              fontWeight={700}
              className="map-label select-none"
            >
              {fitLabel(s.name, lines[s.line].length)}
            </text>
            <text
              x={x}
              y={y + 24}
              textAnchor="middle"
              fontSize={9.5}
              fontWeight={800}
              fill={col}
              className="font-mono select-none"
            >
              {pct}%
            </text>
          </>
        ) : showLabel ? (
          <text
            x={x}
            y={y - 12}
            textAnchor="middle"
            fontSize={isSel ? 10.5 : 9}
            fontWeight={isSel ? 800 : 600}
            fill={isSel ? "#fff" : undefined}
            className="map-label select-none"
            pointerEvents="none"
          >
            {s.name.length > 18 ? s.name.slice(0, 17) + "…" : s.name}
          </text>
        ) : null}
      </g>
    );
  };

  // The depth stack only exists while a junction is being examined. With
  // nothing selected the whole graph is one flat plane - exploding an unselected
  // map would imply a focus that does not exist.
  const exploded = isConnections && selectedCode !== "";

  // The focus view splits its nodes across the two planes so the lifted layer
  // can be painted in front of the floor rather than interleaved with it.
  const onFocusPlane = (s: Station) => s.id === selected || neighborsOfSelected.has(s.code);
  const focusNodes = isConnections
    ? nodeList.filter((s) => !exploded || onFocusPlane(s))
    : [];
  const floorNodes = isConnections
    ? nodeList.filter((s) => exploded && !onFocusPlane(s))
    : [];

  return (
    <div className="space-y-3">
      {/* Line Filters & Controls */}
      <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-800 pb-3">
        <div className="flex items-center gap-1.5 text-xs">
          <span className="font-extrabold uppercase text-slate-400 mr-2">Filter Track:</span>
          {!isSchematic ? (
            <span className="rounded-lg px-2.5 py-1 text-xs font-bold bg-slate-800 text-slate-400">All Lines</span>
          ) : (
            <>
              <button
                onClick={() => setFilterLine("all")}
                className={`rounded-lg px-2.5 py-1 text-xs font-bold transition ${filterLine === "all" ? "bg-brand-600 text-white shadow" : "bg-slate-800 text-slate-400 hover:text-white"}`}
              >
                All Lines
              </button>
              {lineNames.map((ln) => {
                const style = lineStyle(ln);
                const corridor = lineCorridor(ln);
                return (
                  <button
                    key={ln}
                    onClick={() => setFilterLine(filterLine === ln ? "all" : ln)}
                    title={
                      corridor
                        ? `${style.services || ln} — ${corridor}. Showing ${lines[ln].length} station(s).`
                        : `${ln} — ${lines[ln].length} station(s)`
                    }
                    className={`rounded-lg px-2.5 py-1 text-xs font-bold transition ${filterLine === ln ? "bg-brand-600 text-white shadow" : "bg-slate-800 text-slate-400 hover:text-white"}`}
                  >
                    <span
                      className="inline-block h-2 w-2 rounded-full mr-1.5 align-middle"
                      style={{ backgroundColor: style.color }}
                    />
                    {style.services || ln}
                  </button>
                );
              })}
            </>
          )}
        </div>
        <div className="flex items-center gap-1.5">
          <div className="flex rounded-lg bg-slate-900 p-0.5 border border-slate-800">
            {(
              [
                ["schematic", "Original line diagram"],
                ["geographic", "Real-world connection map (GTFS)"],
                ["connections", "Direct-connection focus — click any station to light up everything it links to"],
              ] as const
            ).map(([v, tip]) => (
              <button
                key={v}
                onClick={() => setView(v)}
                title={tip}
                className={`rounded-md px-2.5 py-1 text-[11px] font-bold capitalize transition ${
                  view === v ? "bg-brand-600 text-white shadow" : "text-slate-400 hover:text-white"
                }`}
              >
                {v}
              </button>
            ))}
          </div>
          <span className="text-[11px] font-mono text-slate-400 hidden sm:inline">
            {isSchematic
              ? "Hover a track chip for its routes"
              : isConnections
                ? "Click a station to raise its direct links above the network"
                : "Click a station to trace its real connections"}
          </span>
        </div>
      </div>

      {/* SVG Canvas Map */}
      <div
        className={`rounded-2xl bg-slate-950 p-4 border border-slate-800/80 shadow-inner ${
          isConnections ? "flex flex-col gap-4 xl:flex-row" : "overflow-x-auto"
        }`}
      >
        <div className={isConnections ? "min-w-0 flex-1 overflow-x-auto" : ""}>
        <svg
          viewBox={`0 0 ${viewW} ${viewH}`}
          className={isConnections ? "min-w-[560px] w-full h-auto" : "min-w-[680px] w-full h-auto"}
          role="img"
          aria-label={
            isSchematic
              ? "Interactive Metro Network Schematic"
              : isConnections
                ? "Metro Direct-Connection Focus Map"
                : "Real-world Geolocated Metro Connection Map"
          }
        >
          <defs>
            <filter id="glow-node" x="-50%" y="-50%" width="200%" height="200%">
              <feGaussianBlur stdDeviation="3" result="coloredBlur" />
              <feMerge>
                <feMergeNode in="coloredBlur" />
                <feMergeNode in="SourceGraphic" />
              </feMerge>
            </filter>
            <filter id="glow-track" x="-20%" y="-20%" width="140%" height="140%">
              <feGaussianBlur stdDeviation="2" result="blur" />
              <feMerge>
                <feMergeNode in="blur" />
                <feMergeNode in="SourceGraphic" />
              </feMerge>
            </filter>

            {/* Depth-of-field for the floor plane: the rest of the network sits
                below the focus plane, so it is rendered slightly soft. */}
            <filter id="depth-floor" x="-5%" y="-5%" width="110%" height="110%">
              <feGaussianBlur stdDeviation={FLOOR_BLUR} />
            </filter>

            {/* Cast shadow so the focus plane visibly floats above the floor. */}
            <filter id="depth-lift" x="-25%" y="-25%" width="150%" height="150%">
              <feDropShadow
                dx="0"
                dy={FOCUS_SHADOW.dy}
                stdDeviation={FOCUS_SHADOW.blur}
                floodColor="#020617"
                floodOpacity={FOCUS_SHADOW.opacity}
              />
            </filter>

            {/* Atmospheric pool of light under the raised focus layer. */}
            <radialGradient id="depth-spotlight" cx="50%" cy="50%" r="50%">
              <stop offset="0%" stopColor="#38bdf8" stopOpacity="0.16" />
              <stop offset="55%" stopColor="#6366f1" stopOpacity="0.07" />
              <stop offset="100%" stopColor="#0f172a" stopOpacity="0" />
            </radialGradient>
          </defs>

          {/* Grid Background Lines */}
          <pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse">
            <path d="M 40 0 L 0 0 0 40" fill="none" className="map-grid-pattern" strokeWidth="1" />
          </pattern>
          <rect width={viewW} height={viewH} fill="url(#grid)" />

          {isSchematic ? (
            <>
              {/* Render Metro Track Polylines — every trunk as one continuous line. */}
              {activeLineNames.map((ln) => {
                const stops = lines[ln];
                const y = trackY[ln];
                const color = lineColor(ln);
                const pts = stops.map((_, i) => `${xFor(i, stops.length)},${y}`).join(" ");
                return (
                  <g key={ln}>
                    {/* Outer Track Glow */}
                    <polyline
                      points={pts}
                      fill="none"
                      stroke={color}
                      strokeWidth={8}
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      opacity={0.3}
                      filter="url(#glow-track)"
                    />
                    {/* Core Track Line */}
                    <polyline
                      points={pts}
                      fill="none"
                      stroke={color}
                      strokeWidth={5}
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      opacity={0.9}
                    />
                    {/* Line Name Label */}
                    <text
                      x={10}
                      y={y + 4}
                      fontSize={11}
                      fontWeight={800}
                      fill={color}
                      className="map-label select-none"
                    >
                      {(lineStyle(ln).services || ln).replace(/ /g, "")}
                    </text>
                  </g>
                );
              })}
            </>
          ) : isConnections ? (
            <>
              {/* ============================================================
                  CONNECTIONS VIEW - a two-plane depth stack.

                  Everything is sorted onto one of two Z planes (see
                  lib/mapDepth.ts): the selected station and its genuine
                  one-hop links sit on the raised FOCUS plane at true
                  coordinates; every other station and every other
                  connection path sits on the FLOOR plane, pushed down,
                  blurred and thinned. The floor is drawn first, so the
                  focus layer is unambiguously in front of it.
                  ============================================================ */}

              {/* ---------- FLOOR PLANE (z = 0) ---------- */}
              <g
                transform={exploded ? planeTransform("floor") : undefined}
                filter={exploded ? planeFilter("floor") : undefined}
                data-plane="floor"
              >
                {/* Real-network backdrop, for orientation only. */}
                {network?.segments.map((seg) => {
                  const a = geo.byCode[seg.a];
                  const b = geo.byCode[seg.b];
                  if (!a || !b) return null;
                  return (
                    <line
                      key={`${seg.a}-${seg.b}`}
                      x1={a.x}
                      y1={a.y}
                      x2={b.x}
                      y2={b.y}
                      stroke={lineColor(trunkForServices(seg.r) ?? "")}
                      strokeWidth={1.1}
                      strokeLinecap="round"
                      opacity={selectedCode ? 0.1 : 0.2}
                    />
                  );
                })}

                {/* Unmonitored real stops, as dim context dots. */}
                {network &&
                  network.stations.map((ns) => {
                    if (monitoredCodes.has(ns.c)) return null;
                    const p = geo.byCode[ns.c];
                    if (!p) return null;
                    return (
                      <circle
                        key={ns.c}
                        cx={p.x}
                        cy={p.y}
                        r={1.8}
                        fill="#475569"
                        opacity={selectedCode ? 0.22 : 0.4}
                      />
                    );
                  })}

                {/* Every connection path that is NOT part of the selection:
                    the "rest of the network", in light view, below. */}
                {connections.map((e) => {
                  const a = geo.byCode[e.from_code];
                  const b = geo.byCode[e.to_code];
                  const aSt = byCode[e.from_code];
                  const bSt = byCode[e.to_code];
                  if (!a || !b || !aSt || !bSt) return null;
                  const active = linksSelected(e.from_code, e.to_code);
                  const style = linkDepth(active, selectedCode !== "", {
                    kind: e.kind === "transfer" ? "transfer" : "along_line",
                  });
                  if (style.plane !== "floor") return null;
                  const color =
                    e.kind === "transfer"
                      ? "#94a3b8"
                      : lineColor(edgeTrunk(e.vias, aSt.line) ?? "1/2/3");
                  return (
                    <line
                      key={`floor-${e.from_code}-${e.to_code}`}
                      data-plane="floor"
                      data-link={`${e.from_code}-${e.to_code}`}
                      x1={a.x}
                      y1={a.y}
                      x2={b.x}
                      y2={b.y}
                      stroke={color}
                      strokeWidth={style.width}
                      strokeDasharray={e.kind === "transfer" ? "5 6" : undefined}
                      strokeLinecap="round"
                      opacity={style.opacity}
                    />
                  );
                })}

                {/* Floor stations, drawn in the same plane as the paths they
                    sit on so the two read as one recessed layer. */}
                {floorNodes.map((s) => renderNode(s, "floor"))}
              </g>

              {/* ---------- RISERS + SPOTLIGHT ---------- */}
              {exploded && (
                <>
                  {/* A pool of light on the floor directly beneath the lift. */}
                  {(() => {
                    const sel = geo.byCode[selectedCode];
                    if (!sel) return null;
                    return (
                      <ellipse
                        cx={sel.x}
                        cy={sel.y + FLOOR_LIFT * 2.4}
                        rx={150}
                        ry={110}
                        fill="url(#depth-spotlight)"
                        pointerEvents="none"
                      />
                    );
                  })()}

                  {/* Each lifted node is tied to its own twin on the floor, so
                      the eye reads "this rose out of that" instead of seeing two
                      unrelated copies. */}
                  {stations.map((s) => {
                    const p = geo.byCode[s.code];
                    if (!p) return null;
                    const isSel = s.id === selected;
                    if (!needsRiser(isSel, neighborsOfSelected.has(s.code), true)) return null;
                    const d = nodeDepth(isSel, !isSel, true);
                    return (
                      <g key={`riser-${s.code}`} data-riser={s.code} pointerEvents="none">
                        <line
                          x1={p.x}
                          y1={p.y + FLOOR_LIFT}
                          x2={p.x}
                          y2={p.y}
                          stroke={congestionColor(liveById[s.id]?.occupancy_pct ?? 0)}
                          strokeWidth={1}
                          strokeDasharray="2 3"
                          opacity={isSel ? 0.5 : 0.28}
                        />
                        {/* Footprint where the node meets the floor. */}
                        <ellipse
                          cx={p.x}
                          cy={p.y + FLOOR_LIFT}
                          rx={d.core}
                          ry={d.core * 0.42}
                          fill="none"
                          stroke={congestionColor(liveById[s.id]?.occupancy_pct ?? 0)}
                          strokeWidth={1}
                          opacity={isSel ? 0.45 : 0.2}
                        />
                      </g>
                    );
                  })}
                </>
              )}

              {/* ---------- FOCUS PLANE (z = +1) ---------- */}
              <g
                filter={exploded ? "url(#depth-lift)" : undefined}
                data-plane="focus"
              >
                {connections.map((e) => {
                  const a = geo.byCode[e.from_code];
                  const b = geo.byCode[e.to_code];
                  const aSt = byCode[e.from_code];
                  const bSt = byCode[e.to_code];
                  if (!a || !b || !aSt || !bSt) return null;
                  const active = linksSelected(e.from_code, e.to_code);
                  const style = linkDepth(active, selectedCode !== "", {
                    kind: e.kind === "transfer" ? "transfer" : "along_line",
                  });
                  if (style.plane !== "focus") return null;
                  const color =
                    e.kind === "transfer"
                      ? "#cbd5e1"
                      : lineColor(edgeTrunk(e.vias, aSt.line) ?? "1/2/3");
                  return (
                    <g key={`focus-${e.from_code}-${e.to_code}`} data-plane="focus" data-link={`${e.from_code}-${e.to_code}`}>
                      <title>{`${aSt.name} ↔ ${bSt.name} · ${
                        e.kind === "transfer" ? "walking interchange" : `via ${viaLabel(e.vias)}`
                      }`}</title>

                      {/* Soft skirt: the glow bed the core line sits on. */}
                      {style.skirt > 0 && (
                        <line
                          x1={a.x}
                          y1={a.y}
                          x2={b.x}
                          y2={b.y}
                          stroke={color}
                          strokeWidth={style.skirt}
                          strokeLinecap="round"
                          opacity={0.22}
                        />
                      )}

                      {/* Core line. */}
                      <line
                        x1={a.x}
                        y1={a.y}
                        x2={b.x}
                        y2={b.y}
                        stroke={color}
                        strokeWidth={style.width}
                        strokeDasharray={e.kind === "transfer" ? "7 5" : undefined}
                        strokeLinecap="round"
                        opacity={style.opacity}
                        filter={style.filter}
                      />

                      {/* Animated flow, only on links that belong to the
                          selection, to read as a live path. */}
                      {style.flow && (
                        <line
                          className="map-flow"
                          x1={a.x}
                          y1={a.y}
                          x2={b.x}
                          y2={b.y}
                          stroke="#ffffff"
                          strokeWidth={Math.max(1, style.width * 0.28)}
                          strokeDasharray="3 14"
                          strokeLinecap="round"
                          opacity={0.85}
                        />
                      )}

                      {/* Route chip naming the services. */}
                      {active && e.kind !== "transfer" && (
                        <g className="select-none">
                          <rect
                            x={(a.x + b.x) / 2 - viaLabel(e.vias).length * 2.9 - 5}
                            y={(a.y + b.y) / 2 - 9}
                            width={viaLabel(e.vias).length * 5.8 + 10}
                            height={18}
                            rx={9}
                            fill="#020617"
                            stroke={color}
                            strokeWidth={1.2}
                          />
                          <text
                            x={(a.x + b.x) / 2}
                            y={(a.y + b.y) / 2 + 4}
                            textAnchor="middle"
                            fontSize={10}
                            fontWeight={800}
                            fill={color}
                            className="font-mono"
                          >
                            {viaLabel(e.vias)}
                          </text>
                        </g>
                      )}
                    </g>
                  );
                })}
              </g>

              {/* Lifted stations, painted last so the whole focus plane - nodes,
                  links, chips - sits in front of the floor and its shadow. */}
              <g
        filter={exploded ? "url(#depth-lift)" : undefined}
        data-plane="focus"
      >
                {focusNodes.map((s) => renderNode(s, "focus"))}
              </g>
            </>
          ) : (
            <>
              {/* Full real-network base layer: every GTFS rail segment, faint. */}
              {network?.segments.map((seg) => {
                const a = geo.byCode[seg.a];
                const b = geo.byCode[seg.b];
                if (!a || !b) return null;
                const color = lineColor(trunkForServices(seg.r) ?? "");
                const bothMonitored = monitoredCodes.has(seg.a) && monitoredCodes.has(seg.b);
                const active = linksSelected(seg.a, seg.b);
                return (
                  <line
                    key={`${seg.a}-${seg.b}`}
                    x1={a.x}
                    y1={a.y}
                    x2={b.x}
                    y2={b.y}
                    stroke={color}
                    strokeWidth={bothMonitored ? 2.5 : 1.4}
                    strokeLinecap="round"
                    opacity={active ? 0.9 : bothMonitored ? 0.55 : 0.3}
                  />
                );
              })}

              {/* Every other station on the real network — tiny, unlabelled dots. */}
              {network &&
                network.stations.map((ns) => {
                  if (monitoredCodes.has(ns.c)) return null;
                  const p = geo.byCode[ns.c];
                  if (!p) return null;
                  return (
                    <circle key={ns.c} cx={p.x} cy={p.y} r={2.2} fill="#334155" opacity={0.5}>
                      <title>{`${ns.n} — not monitored (all lines shown for context)`}</title>
                    </circle>
                  );
                })}

              {/* Monitored along-line edges, bright on top of the base layer. */}
              {connections
                .filter((c) => c.kind === "along_line")
                .map((e) => {
                  const a = geo.byCode[e.from_code];
                  const b = geo.byCode[e.to_code];
                  const aSt = byCode[e.from_code];
                  const bSt = byCode[e.to_code];
                  if (!a || !b || !aSt || !bSt) return null;
                  const color = lineColor(edgeTrunk(e.vias, aSt.line) ?? "1/2/3");
                  const active = linksSelected(e.from_code, e.to_code);
                  const opacity = selectedCode && !active ? 0.45 : 1;
                  return (
                    <g key={`${e.from_code}-${e.to_code}`}>
                      <title>{`${aSt.name} ↔ ${bSt.name} · via ${viaLabel(e.vias)}`}</title>
                      <line
                        x1={a.x}
                        y1={a.y}
                        x2={b.x}
                        y2={b.y}
                        stroke={color}
                        strokeWidth={active ? 9 : 5}
                        strokeLinecap="round"
                        opacity={opacity * 0.28}
                        filter={active ? "url(#glow-track)" : undefined}
                      />
                      <line
                        x1={a.x}
                        y1={a.y}
                        x2={b.x}
                        y2={b.y}
                        stroke={color}
                        strokeWidth={active ? 4 : 2.5}
                        strokeLinecap="round"
                        opacity={opacity}
                      />
                    </g>
                  );
                })}

              {/* Walking interchanges (dashed, slate). */}
              {connections
                .filter((c) => c.kind === "transfer")
                .map((e) => {
                  const a = geo.byCode[e.from_code];
                  const b = geo.byCode[e.to_code];
                  const aSt = byCode[e.from_code];
                  const bSt = byCode[e.to_code];
                  if (!a || !b || !aSt || !bSt) return null;
                  const active = linksSelected(e.from_code, e.to_code);
                  const opacity = selectedCode && !active ? 0.45 : 1;
                  return (
                    <g key={`${e.from_code}-${e.to_code}`}>
                      <title>{`${aSt.name} ↔ ${bSt.name} · walking interchange`}</title>
                      <line
                        x1={a.x}
                        y1={a.y}
                        x2={b.x}
                        y2={b.y}
                        className="map-transfer"
                        stroke="#94a3b8"
                        strokeWidth={active ? 3.5 : 2}
                        strokeDasharray="6 5"
                        strokeLinecap="round"
                        opacity={opacity}
                      />
                    </g>
                  );
                })}
            </>
          )}

          {/* Station Nodes - schematic and geographic views render flat;
              the connections view draws its own nodes inside the two depth
              planes above, so the lifted layer is not interleaved with the
              floor. */}
          {!isConnections && nodeList.map((s) => renderNode(s, "focus"))}
        </svg>
        </div>

        {/* Focus-view side panel: the same links as a readable one-to-one list. */}
        {isConnections && (
          <aside className="w-full shrink-0 xl:w-72">
            <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-3.5">
              {selectedStation ? (
                <>
                  <p className="text-[10px] font-extrabold uppercase tracking-wider text-slate-400">
                    Direct Connections
                  </p>
                  <p className="mt-1.5 truncate text-sm font-extrabold text-white" title={selectedStation.name}>
                    {selectedStation.name}
                  </p>
                  <p className="mt-0.5 font-mono text-[10px] text-slate-500">
                    {selectedStation.code} · {selectedStation.line} · live occupancy{" "}
                    <span style={{ color: congestionColor(liveById[selectedStation.id]?.occupancy_pct ?? 0) }}>
                      {Math.round(liveById[selectedStation.id]?.occupancy_pct ?? 0)}%
                    </span>
                  </p>
                  <div className="mt-3 border-t border-slate-800 pt-3">
                    <ConnectionList
                      code={selectedStation.code}
                      connections={connections}
                      stations={stations}
                      onSelect={onSelect}
                    />
                  </div>
                </>
) : isConnections ? (
          <div className="grid gap-2 sm:grid-cols-2">
            <p className="max-w-2xl leading-relaxed">
              This is the <b className="text-white">same real NYC network at true latitude/longitude</b>, stacked as two
              depth layers. <b className="text-slate-200">The raised layer</b> is the selected station plus every station it
              links to, drawn at full brightness with route chips and live occupancy badges.{" "}
              <b className="text-slate-200">The lower layer</b> is the rest of the network — every other station and all
              its remaining connection paths — pushed down, thinner and slightly soft, so the junction is read in
              context instead of on an empty canvas. Vertical stems connect each raised station to its own twin
              on the floor below.{" "}
              <b className="text-slate-300">Dashed lines</b> are walking interchanges within a complex.
            </p>
            <p className="max-w-2xl leading-relaxed">
              <b className="text-slate-300">How to read it:</b> a thick glowing link with flowing dashes is a
              connection the selection genuinely owns. The faded links below are context, not part of this junction.
              Only links incident to the selected station are lifted, so a path that merely passes through a
              neighbour stays on the floor. Straight lines between stops are a simplification of real track geometry.
            </p>
          </div>
        ) : (
                <div className="py-2">
                  <p className="text-[10px] font-extrabold uppercase tracking-wider text-slate-400">
                    Direct Connections
                  </p>
                  <p className="mt-2 text-xs leading-relaxed text-slate-500">
                    Click any station node on the map. Everything unrelated drops away and every station it links
                    to is lit, ringed and labelled with the routes that serve it.
                  </p>
                  <dl className="mt-3 space-y-1.5 border-t border-slate-800 pt-3 font-mono text-[11px] text-slate-500">
                    <div className="flex justify-between">
                      <dt>Monitored stops</dt>
                      <dd className="text-slate-300">{stations.length}</dd>
                    </div>
                    <div className="flex justify-between">
                      <dt>Train links</dt>
                      <dd className="text-slate-300">{connections.filter((c) => c.kind === "along_line").length}</dd>
                    </div>
                    <div className="flex justify-between">
                      <dt>Walking links</dt>
                      <dd className="text-slate-300">{connections.filter((c) => c.kind === "transfer").length}</dd>
                    </div>
                  </dl>
                </div>
              )}
            </div>
          </aside>
        )}
      </div>

      {/* Map Legend */}
      <div className="flex flex-wrap items-center justify-between gap-4 text-xs text-slate-400 pt-1">
        <div className="flex items-center gap-3">
          <span className="font-extrabold uppercase text-slate-400">Live Congestion Legend:</span>
          {[
            ["Low <55%", "#10b981"],
            ["Medium 55-75%", "#eab308"],
            ["High 75-90%", "#f97316"],
            ["Critical ≥90%", "#f43f5e"],
          ].map(([l, c]) => (
            <span key={l} className="inline-flex items-center gap-1.5 font-medium">
              <span className="h-2.5 w-2.5 rounded-full" style={{ backgroundColor: c }} />
              {l}
            </span>
          ))}
          {!isSchematic && (
            <span className="inline-flex items-center gap-1.5 font-medium">
              <svg width="16" height="6" className="h-2">
                <line x1="0" y1="3" x2="16" y2="3" stroke="#94a3b8" strokeWidth="2" strokeDasharray="4 3" />
              </svg>
              Walking interchange
            </span>
          )}
          {isConnections && (
            <>
              <span className="inline-flex items-center gap-1.5 font-medium">
                <svg width="22" height="8" className="h-2">
                  <line x1="0" y1="4" x2="22" y2="4" stroke="#22d3ee" strokeWidth="3" strokeLinecap="round" />
                </svg>
                Raised layer: the selection&apos;s own links
              </span>
              <span className="inline-flex items-center gap-1.5 font-medium">
                {/* Miniature of the map's own stacking: a riser rising off a
                    shadowed, thinner base line. */}
                <svg width="22" height="12" className="h-3">
                  <line x1="1" y1="10" x2="21" y2="10" stroke="#64748b" strokeWidth="1.5" opacity="0.45" />
                  <line x1="11" y1="10" x2="11" y2="4" stroke="#94a3b8" strokeWidth="1" strokeDasharray="2 2" opacity="0.5" />
                  <line x1="4" y1="4" x2="18" y2="4" stroke="#22d3ee" strokeWidth="3" strokeLinecap="round" />
                  <circle cx="4" cy="4" r="2.4" fill="#22d3ee" />
                </svg>
                Floor layer: the rest of the network
              </span>
            </>
          )}
        </div>
        <span className="text-[11px] text-slate-400">
          {isSchematic
            ? "Click any station node to open real-time telemetry"
            : isConnections
              ? "Click a station: it and its direct connections lift onto a raised layer, with the rest of the network left in view below"
              : "Selecting a station highlights its one-hop real-world connections"}
        </span>
      </div>

      {/* Metro Line Corridor Legend */}
      <div className="rounded-2xl border border-slate-800 bg-slate-950/60 px-4 py-3 text-[11px] text-slate-400">
        <p className="font-extrabold uppercase tracking-wider text-slate-500 mb-2">
          {isSchematic ? "What is a “Trunk Route”?" : isConnections ? "How to read the connection focus view" : "How to read the connection map"}
        </p>
        {isSchematic ? (
          <div className="flex flex-wrap gap-x-6 gap-y-2">
            {lineNames.map((ln) => {
              const style = lineStyle(ln);
              return (
                <span
                  key={ln}
                  className="inline-flex items-start gap-2 max-w-md"
                  title={`${style.services || ln} — ${lines[ln].length} station(s) monitored`}
                >
                  <span
                    className="mt-1 h-2.5 w-2.5 shrink-0 rounded-full"
                    style={{ backgroundColor: style.color }}
                  />
                  <span>
                    <b className="text-white" style={{ color: style.ink }}>
                      {style.services || ln}
                    </b>{" "}
                    —{" "}
                    <span className="text-slate-400">
                      {style.corridor || `${lines[ln].length} stations`}
                    </span>
                  </span>
                </span>
              );
            })}
          </div>
        ) : (
          <div className="grid gap-2 sm:grid-cols-2">
            <p className="max-w-2xl leading-relaxed">
              This is the <b className="text-white">real NYC subway network</b> (496 stations / 578 segments
              from the official MTA GTFS feed) drawn at true latitude/longitude. Every station sits at its
              real MTA coordinate and every segment joins stops that are genuinely consecutive on the same
              trip, tagged with the routes that serve it. Faint coloured segments are the existing rails;
              the big dots are our processed stations. Click any processed node to brighten exactly which
              stations it connects to and trace the real-world junction.
            </p>
            <p className="max-w-2xl leading-relaxed">
              <b className="text-slate-300">Straight lines are a simplification:</b> the connection between
              two stops is drawn as a straight segment, so curves and track-level detail are not surveyed
              geometry. <b className="text-slate-300">Dashed grey</b> lines are walking interchanges added
              by hand from the GTFS data (42 St Shuttle, Queensboro Plaza same-concourse, Union Sq, etc.).
              Tiny slate dots are other rail stations shown purely for orientation — they carry no live
              telemetry.
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
