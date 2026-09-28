import { useState } from "react";
import { congestionColor } from "./StatusBadge";
import { lineColor, lineCorridor, lineStyle, orderedLines } from "../lib/lines";
import type { Station, LiveCrowdSnapshot } from "../lib/types";

/**
 * Layout is derived from the data rather than fixed. The tracks are schematic
 * (one horizontal row per trunk, stations spaced along it), so a trunk with 12
 * stops needs more horizontal room than one with 2, and the canvas has to grow
 * as trunks are added instead of clipping them off the bottom.
 */
const TRACK_BAND = 80;
const TRACK_TOP = 70;
const TRACK_BOTTOM = 64;
const LABEL_GUTTER = 84;
const MIN_STATION_GAP = 76;
const MIN_W = 760;
const LABEL_CHAR_W = 5.6;

interface MetroMapProps {
  stations?: Station[];
  live?: LiveCrowdSnapshot[];
  selected?: string | null;
  onSelect?: (stationId: string) => void;
}

export default function MetroMap({ stations = [], live = [], selected, onSelect }: MetroMapProps) {
  const [filterLine, setFilterLine] = useState("all");

  const liveById: Record<string, LiveCrowdSnapshot> = Object.fromEntries(
    (live || []).map((s) => [s.station_id, s])
  );

  // Group stations by trunk route, preserving order within each trunk.
  const lines: Record<string, Station[]> = {};
  stations.forEach((s) => {
    (lines[s.line] = lines[s.line] || []).push(s);
  });
  const lineNames = orderedLines(Object.keys(lines));

  const activeLineNames = filterLine === "all" ? lineNames : lineNames.filter((l) => l === filterLine);

  // Width is driven by the busiest trunk so station labels have room to breathe.
  const maxStops = Math.max(1, ...activeLineNames.map((ln) => lines[ln].length));
  const W = Math.max(MIN_W, LABEL_GUTTER * 2 + (maxStops - 1) * MIN_STATION_GAP);
  // Height follows the number of *visible* trunks, so filtering collapses the map
  // instead of leaving blank bands where the hidden tracks used to be.
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

  return (
    <div className="space-y-3">
      {/* Line Filters & Controls */}
      <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-800 pb-3">
        <div className="flex items-center gap-1.5 text-xs">
          <span className="font-extrabold uppercase text-slate-400 mr-2">Filter Track:</span>
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
        </div>
        <span className="text-[11px] font-mono text-slate-400 hidden sm:inline">
          Hover a track chip for its routes
        </span>
      </div>

      {/* SVG Canvas Map */}
      <div className="relative overflow-x-auto rounded-2xl bg-slate-950 p-4 border border-slate-800/80 shadow-inner">
        <svg
          viewBox={`0 0 ${W} ${H}`}
          className="min-w-[680px] w-full"
          style={{ height: "auto" }}
          role="img"
          aria-label="Interactive Metro Network Schematic"
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
          </defs>

          {/* Grid Background Lines */}
          <pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse">
            <path d="M 40 0 L 0 0 0 40" fill="none" className="map-grid-pattern" strokeWidth="1" />
          </pattern>
          <rect width={W} height={H} fill="url(#grid)" />

          {/* Render Metro Track Polylines */}
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

          {/* Render Station Nodes */}
          {activeLineNames.flatMap((ln) => {
            const stops = lines[ln];
            const y = trackY[ln];
            return stops.map((s, i) => {
              const x = xFor(i, stops.length);
              const snap = liveById[s.id];
              const pct = snap?.occupancy_pct ?? 0;
              const isSel = selected === s.id;
              const col = congestionColor(pct);

              return (
                <g
                  key={s.id}
                  onClick={() => onSelect && onSelect(s.id)}
                  className="cursor-pointer group"
                >
                  <title>{`${s.name} (${s.id}) · Line: ${s.line} · Occupancy: ${pct}% · Congestion: ${snap?.congestion_level || "low"}`}</title>

                  {/* Selection Pulsing Ring */}
                  {isSel && (
                    <circle
                      cx={x}
                      cy={y}
                      r={16}
                      fill="none"
                      className="map-select-ring animate-spin"
                      strokeWidth={2}
                      strokeDasharray="4 3"
                    />
                  )}

                  {/* Congestion Glow Ring */}
                  <circle
                    cx={x}
                    cy={y}
                    r={11}
                    fill={col}
                    opacity={0.35}
                    filter="url(#glow-node)"
                  />
                  {/* Core Station Dot */}
                  <circle
                    cx={x}
                    cy={y}
                    r={7}
                    fill={col}
                    className="map-node-ring transition-transform group-hover:scale-125"
                    strokeWidth={2.5}
                  />
                  {/* Station Label Above */}
                  <text
                    x={x}
                    y={y - 16}
                    textAnchor="middle"
                    fontSize={10}
                    fontWeight={700}
                    className="map-label select-none"
                  >
                    {fitLabel(s.name, stops.length)}
                  </text>
                  {/* Occupancy Pct Below */}
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
                </g>
              );
            });
          })}
        </svg>
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
        </div>
        <span className="text-[11px] text-slate-400">Click any station node to open real-time telemetry</span>
      </div>

      {/* Metro Line Corridor Legend */}
      <div className="rounded-2xl border border-slate-800 bg-slate-950/60 px-4 py-3 text-[11px] text-slate-400">
        <p className="font-extrabold uppercase tracking-wider text-slate-500 mb-2">
          What is a “Trunk Route”?
        </p>
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
      </div>
    </div>
  );
}
