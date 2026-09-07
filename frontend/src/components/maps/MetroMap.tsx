"use client";

import { StationDensity } from "@/types";
import { Train, Info, MapPin } from "lucide-react";
import { useState } from "react";

interface MetroMapProps {
  stations: StationDensity[];
  onSelectStation?: (station: StationDensity) => void;
  selectedStationId?: number | null;
}

export function MetroMap({ stations, onSelectStation, selectedStationId }: MetroMapProps) {
  const [hoveredStation, setHoveredStation] = useState<StationDensity | null>(null);

  // Filter stations by line
  const redLineStations = stations.filter((s) => s.line_name === "Red Line").sort((a, b) => a.station_id - b.station_id);
  const blueLineStations = stations.filter((s) => s.line_name === "Blue Line").sort((a, b) => a.station_id - b.station_id);

  const getStatusColor = (status: string) => {
    if (status === "CRITICAL") return "#ef4444"; // Red
    if (status === "MODERATE") return "#f59e0b"; // Amber
    return "#10b981"; // Green
  };

  return (
    <div className="relative w-full h-[450px] bg-[#090d18] border border-slate-800 rounded-xl p-4 overflow-hidden flex flex-col justify-between">
      {/* Map Header */}
      <div className="flex items-center justify-between z-10">
        <div>
          <h3 className="text-sm font-bold text-white flex items-center gap-2">
            <MapPin className="w-4 h-4 text-blue-400" />
            Interactive Metro Network Telemetry Map
          </h3>
          <p className="text-xs text-slate-400">
            Real-time platform density heatmap & transit line node graph
          </p>
        </div>

        {/* Legend */}
        <div className="flex items-center gap-4 text-xs">
          <div className="flex items-center gap-1.5">
            <span className="w-3 h-3 rounded-full bg-emerald-500 inline-block"></span>
            <span className="text-slate-300">Normal (&lt;60%)</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="w-3 h-3 rounded-full bg-amber-500 inline-block"></span>
            <span className="text-slate-300">Moderate (60-80%)</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="w-3 h-3 rounded-full bg-rose-500 inline-block"></span>
            <span className="text-slate-300 font-semibold text-rose-400">Critical (&gt;80%)</span>
          </div>
        </div>
      </div>

      {/* SVG Transit Line Graph */}
      <div className="relative flex-1 flex items-center justify-center my-2">
        <svg className="w-full h-full" viewBox="0 0 900 320">
          {/* Background Grid Lines */}
          <pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse">
            <path d="M 40 0 L 0 0 0 40" fill="none" stroke="#1e293b" strokeWidth="0.5" opacity="0.4" />
          </pattern>
          <rect width="100%" height="100%" fill="url(#grid)" />

          {/* Line Path - Red Line */}
          <path
            d="M 80 100 L 200 100 L 320 100 L 440 100 L 560 100 L 680 100 L 800 100"
            fill="none"
            stroke="#dc2626"
            strokeWidth="6"
            strokeLinecap="round"
            opacity="0.8"
          />

          {/* Line Path - Blue Line */}
          <path
            d="M 80 220 L 200 220 L 440 100 L 560 220 L 680 220 L 800 220"
            fill="none"
            stroke="#2563eb"
            strokeWidth="6"
            strokeLinecap="round"
            opacity="0.8"
          />

          {/* Red Line Station Nodes */}
          {redLineStations.map((st, idx) => {
            const cx = 80 + idx * 102;
            const cy = 100;
            const color = getStatusColor(st.status);
            const isSelected = selectedStationId === st.station_id;

            return (
              <g
                key={`red-${st.station_id}`}
                className="cursor-pointer transition-transform hover:scale-125"
                onClick={() => onSelectStation && onSelectStation(st)}
                onMouseEnter={() => setHoveredStation(st)}
                onMouseLeave={() => setHoveredStation(null)}
              >
                {/* Glowing Outer Ring if Critical */}
                {st.status === "CRITICAL" && (
                  <circle cx={cx} cy={cy} r="18" fill="none" stroke="#ef4444" strokeWidth="3" className="animate-ping" opacity="0.6" />
                )}
                {/* Outer Selection Highlight */}
                <circle
                  cx={cx}
                  cy={cy}
                  r={isSelected ? "14" : "11"}
                  fill="#0b0f17"
                  stroke={isSelected ? "#60a5fa" : color}
                  strokeWidth="3"
                />
                {/* Inner Node */}
                <circle cx={cx} cy={cy} r="6" fill={color} />
                {/* Station Label */}
                <text
                  x={cx}
                  y={cy - 20}
                  textAnchor="middle"
                  fill={st.status === "CRITICAL" ? "#fca5a5" : "#cbd5e1"}
                  fontSize="11"
                  fontWeight={st.status === "CRITICAL" ? "bold" : "normal"}
                >
                  {st.station_name.split(" ")[0]}
                </text>
                <text x={cx} y={cy + 24} textAnchor="middle" fill="#94a3b8" fontSize="10">
                  {st.density_percentage}%
                </text>
              </g>
            );
          })}

          {/* Blue Line Station Nodes */}
          {blueLineStations.map((st, idx) => {
            const cx = 80 + idx * 102;
            const cy = st.is_interchange ? 100 : 220;
            const color = getStatusColor(st.status);
            const isSelected = selectedStationId === st.station_id;

            if (st.is_interchange) return null; // Skip duplicate rendering for interchange

            return (
              <g
                key={`blue-${st.station_id}`}
                className="cursor-pointer transition-transform hover:scale-125"
                onClick={() => onSelectStation && onSelectStation(st)}
                onMouseEnter={() => setHoveredStation(st)}
                onMouseLeave={() => setHoveredStation(null)}
              >
                {st.status === "CRITICAL" && (
                  <circle cx={cx} cy={cy} r="18" fill="none" stroke="#ef4444" strokeWidth="3" className="animate-ping" opacity="0.6" />
                )}
                <circle
                  cx={cx}
                  cy={cy}
                  r={isSelected ? "14" : "11"}
                  fill="#0b0f17"
                  stroke={isSelected ? "#60a5fa" : color}
                  strokeWidth="3"
                />
                <circle cx={cx} cy={cy} r="6" fill={color} />
                <text x={cx} y={cy + 22} textAnchor="middle" fill="#cbd5e1" fontSize="11">
                  {st.station_name.split(" ")[0]}
                </text>
                <text x={cx} y={cy + 36} textAnchor="middle" fill="#94a3b8" fontSize="10">
                  {st.density_percentage}%
                </text>
              </g>
            );
          })}
        </svg>
      </div>

      {/* Hovered Station Tooltip Box */}
      {hoveredStation && (
        <div className="absolute bottom-4 left-4 z-20 bg-slate-900/95 border border-slate-700 p-3 rounded-lg shadow-xl text-xs backdrop-blur space-y-1">
          <div className="font-bold text-white flex items-center justify-between gap-3">
            <span>{hoveredStation.station_name}</span>
            <span className="text-[10px] px-2 py-0.5 rounded bg-slate-800 text-blue-400 font-mono">
              {hoveredStation.line_name}
            </span>
          </div>
          <div className="flex items-center gap-4 text-slate-300">
            <div>Inflow: <span className="font-semibold text-emerald-400">{hoveredStation.inflow_rate_ppm} ppm</span></div>
            <div>Outflow: <span className="font-semibold text-rose-400">{hoveredStation.outflow_rate_ppm} ppm</span></div>
            <div>Density: <span className="font-semibold text-amber-400">{hoveredStation.density_percentage}%</span></div>
          </div>
        </div>
      )}
    </div>
  );
}
