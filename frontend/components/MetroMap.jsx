import { useState } from "react";
import { congestionColor } from "./StatusBadge";
import { TrainFront } from "lucide-react";

const LINE_COLORS = {
  Red: "#ef4444",
  Blue: "#3b82f6",
  Green: "#10b981",
};

const LINE_ROUTES = {
  Red: "Central Junction · Riverside Park · Tech District · South Commons",
  Blue: "Old Town Market · Stadium Plaza · University Gate",
  Green: "Airport Terminal · Harbor Front · North Industrial",
};

export default function MetroMap({ stations = [], live = [], selected, onSelect }) {
  const [filterLine, setFilterLine] = useState("all");

  const liveById = Object.fromEntries((live || []).map((s) => [s.station_id, s]));
  
  // Group stations by line preserving order
  const lines = {};
  stations.forEach((s) => {
    (lines[s.line] = lines[s.line] || []).push(s);
  });
  const lineNames = Object.keys(lines).sort();
  const W = 760;
  const H = 280;

  // Layout: track Y coordinates
  const trackY = {};
  lineNames.forEach((ln, i) => {
    trackY[ln] = 70 + i * 80;
  });

  function xFor(line, idx, total) {
    const pad = 80;
    if (total <= 1) return W / 2;
    return pad + (idx * (W - pad * 2)) / (total - 1);
  }

  const activeLineNames = filterLine === "all" ? lineNames : lineNames.filter((l) => l.toLowerCase() === filterLine.toLowerCase());

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
          {lineNames.map((ln) => (
            <button
              key={ln}
              onClick={() => setFilterLine(ln)}
              title={
                LINE_ROUTES[ln]
                  ? `${ln} Line — a color-coded rail corridor serving: ${LINE_ROUTES[ln]}. Click to show only its stations.`
                  : `${ln} Line corridor`
              }
              className={`rounded-lg px-2.5 py-1 text-xs font-bold transition ${filterLine === ln ? "bg-white text-slate-900 shadow" : "bg-slate-800 text-slate-400 hover:text-white"}`}
            >
              <span className="inline-block h-2 w-2 rounded-full mr-1.5" style={{ backgroundColor: LINE_COLORS[ln] }} />
              {ln} Line
            </button>
          ))}
        </div>
        <span className="text-[11px] font-mono text-slate-400 hidden sm:inline">Hover a line chip to see its corridor route</span>
      </div>

      {/* SVG Canvas Map */}
      <div className="relative overflow-x-auto rounded-2xl bg-slate-950 p-4 border border-slate-800/80 shadow-inner">
        <svg viewBox={`0 0 ${W} ${H}`} className="min-w-[680px] w-full" role="img" aria-label="Interactive Metro Network Schematic">
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
            <path d="M 40 0 L 0 0 0 40" fill="none" stroke="rgba(255, 255, 255, 0.03)" strokeWidth="1" />
          </pattern>
          <rect width={W} height={H} fill="url(#grid)" />

          {/* Render Metro Track Polylines */}
          {activeLineNames.map((ln) => {
            const stops = lines[ln];
            const y = trackY[ln];
            const pts = stops.map((s, i) => `${xFor(ln, i, stops.length)},${y}`).join(" ");
            return (
              <g key={ln}>
                {/* Outer Track Glow */}
                <polyline
                  points={pts}
                  fill="none"
                  stroke={LINE_COLORS[ln] || "#64748b"}
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
                  stroke={LINE_COLORS[ln] || "#64748b"}
                  strokeWidth={5}
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  opacity={0.9}
                />
                {/* Line Name Label */}
                <text x={16} y={y + 4} fontSize={11} fontWeight={800} fill={LINE_COLORS[ln] || "#64748b"}>
                  {ln} LINE
                </text>
              </g>
            );
          })}

          {/* Render Station Nodes */}
          {activeLineNames.flatMap((ln) => {
            const stops = lines[ln];
            const y = trackY[ln];
            return stops.map((s, i) => {
              const x = xFor(ln, i, stops.length);
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
                      stroke="#ffffff"
                      strokeWidth={2}
                      strokeDasharray="4 3"
                      className="animate-spin"
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
                    stroke="#0f172a"
                    strokeWidth={2.5}
                    className="transition-transform group-hover:scale-125"
                  />
                  {/* Station Label Above */}
                  <text
                    x={x}
                    y={y - 16}
                    textAnchor="middle"
                    fontSize={10}
                    fontWeight={700}
                    fill="#e2e8f0"
                    className="select-none transition-colors group-hover:fill-brand-400"
                  >
                    {s.name.length > 13 ? s.name.slice(0, 12) + "…" : s.name}
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
        <p className="font-extrabold uppercase tracking-wider text-slate-500 mb-2">What is a “Line”?</p>
        <div className="flex flex-wrap gap-x-6 gap-y-2">
          {Object.entries(LINE_ROUTES).map(([ln, route]) => (
            <span key={ln} className="inline-flex items-start gap-2 max-w-md" title={`${ln} Line — color-coded rail corridor`}>
              <span className="mt-1 h-2.5 w-2.5 shrink-0 rounded-full" style={{ backgroundColor: LINE_COLORS[ln] }} />
              <span>
                <b className="text-white">{ln} Line</b> — <span className="text-slate-400">{route}</span>
              </span>
            </span>
          ))}
        </div>
      </div>
    </div>
  );
}
