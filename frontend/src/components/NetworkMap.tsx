import React, { useEffect, useState } from 'react';
import { Activity, X, Users, Train, AlertTriangle } from 'lucide-react';

interface StationNode {
  id: string;
  name: string;
  x: number;
  y: number;
  line: string;
  occupancy_pct: number;
  status: 'NORMAL' | 'ELEVATED' | 'CRITICAL';
  inflow_rate: number;
  platform_count: number;
}

interface MetroLine {
  id: string;
  name: string;
  color: string;
  path: string;
}

export const NetworkMap: React.FC = () => {
  const [stations, setStations] = useState<StationNode[]>([]);
  const [lines, setLines] = useState<MetroLine[]>([]);
  const [selectedStation, setSelectedStation] = useState<StationNode | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch('http://localhost:8000/api/network/map')
      .then((res) => res.json())
      .then((data) => {
        // Broad transformation scale to cover optimal widescreen aspect ratio
        const scaleX = 1.35;
        const scaleY = 1.15;
        const offsetX = 60;
        const offsetY = 40;

        const adjustedStations = (data.stations || []).map((st: StationNode) => ({
          ...st,
          x: Math.round(st.x * scaleX + offsetX),
          y: Math.round(st.y * scaleY + offsetY)
        }));

        const adjustedLines = (data.lines || []).map((line: MetroLine) => {
          let path = line.path;
          if (line.id === 'blue-line') {
            path = "M 168 247 L 411 247 L 654 362 L 924 362 L 1167 500 L 1383 500";
          } else if (line.id === 'emerald-line') {
            path = "M 222 592 L 492 592 L 654 362 L 924 362 L 1086 201 L 1329 201";
          } else if (line.id === 'ruby-line') {
            path = "M 411 247 L 492 592 L 789 661 L 1167 500";
          }
          return { ...line, path };
        });

        setLines(adjustedLines);
        setStations(adjustedStations);
      })
      .catch((err) => console.error('Map fetch error:', err))
      .finally(() => setLoading(false));
  }, []);

  const getNodeColor = (status: string) => {
    switch (status) {
      case 'CRITICAL':
        return { fill: '#ef4444', stroke: '#fee2e2', glow: 'rgba(239,68,68,0.7)' };
      case 'ELEVATED':
        return { fill: '#f59e0b', stroke: '#fef3c7', glow: 'rgba(245,158,11,0.7)' };
      default:
        return { fill: '#10b981', stroke: '#d1fae5', glow: 'rgba(16,185,129,0.6)' };
    }
  };

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center h-[520px] text-cyan-400 gap-3 font-mono text-xs">
        <Activity className="w-6 h-6 animate-pulse" />
        RESOLVING DYNAMIC MAP TOPOLOGY...
      </div>
    );
  }

  return (
    <div className="w-full bg-slate-900/40 border border-slate-800/80 rounded-3xl p-8 shadow-2xl backdrop-blur-md">
      
      {/* Title & Color Legend Banner */}
      <div className="flex flex-col xl:flex-row xl:items-center justify-between gap-5 pb-6 mb-6 border-b border-slate-800/80">
        <div>
          <div className="flex items-center gap-2 mb-1.5">
            <span className="h-2 w-2 rounded-full bg-cyan-400 animate-ping" />
            <h2 className="text-lg font-bold tracking-wider uppercase text-slate-100">
              Live Metro Network Topology
            </h2>
          </div>
          <p className="text-sm text-slate-400">Click any station node to inspect real-time crowd telemetry</p>
        </div>
        
        {/* Widescreen Status Legend */}
        <div className="flex flex-wrap items-center gap-4.5 bg-slate-950/80 border border-slate-800/80 px-5 py-3 rounded-2xl text-xs font-mono">
          <span className="flex items-center gap-2.5 text-slate-300">
            <span className="w-3.5 h-3.5 rounded-full bg-emerald-500 shadow-[0_0_12px_#10b981]" />
            &lt;60% Normal
          </span>
          <span className="flex items-center gap-2.5 text-slate-300">
            <span className="w-3.5 h-3.5 rounded-full bg-amber-500 shadow-[0_0_12px_#f59e0b]" />
            60-80% Elevated
          </span>
          <span className="flex items-center gap-2.5 text-slate-300">
            <span className="w-3.5 h-3.5 rounded-full bg-rose-500 shadow-[0_0_12px_#ef4444] animate-pulse" />
            &gt;80% Congested
          </span>
        </div>
      </div>

      {/* SVG Canvas Widescreen Framing */}
      <div className="w-full bg-[#030712]/95 rounded-2xl border border-slate-800/90 shadow-2xl relative overflow-hidden flex items-center justify-center p-3 h-[580px]">
        
        {/* Dynamic Canvas Area */}
        <svg 
          viewBox="0 0 1550 780" 
          className="w-full h-full object-contain"
          xmlns="http://www.w3.org/2000/svg"
        >
          <defs>
            <filter id="neon-glow" x="-20%" y="-20%" width="140%" height="140%">
              <feGaussianBlur stdDeviation="5" result="blur" />
              <feMerge>
                <feMergeNode in="blur" />
                <feMergeNode in="SourceGraphic" />
              </feMerge>
            </filter>
            
            <pattern id="grid-pattern" width="40" height="40" patternUnits="userSpaceOnUse">
              <path d="M 40 0 L 0 0 0 40" fill="none" stroke="#1e293b" strokeWidth="0.8" opacity="0.15" />
            </pattern>
          </defs>
          <rect width="100%" height="100%" fill="url(#grid-pattern)" />

          {/* Connected Network Tracks */}
          {lines.map((line: MetroLine) => (
            <g key={line.id} className="opacity-90">
              <path
                d={line.path}
                stroke={line.color}
                strokeWidth="14"
                strokeLinecap="round"
                strokeLinejoin="round"
                fill="none"
                opacity="0.12"
                filter="url(#neon-glow)"
              />
              <path
                d={line.path}
                stroke={line.color}
                strokeWidth="5"
                strokeLinecap="round"
                strokeLinejoin="round"
                fill="none"
              />
            </g>
          ))}

          {/* Station Nodes */}
          {stations.map((st: StationNode) => {
            const color = getNodeColor(st.status);
            const isSelected = selectedStation?.id === st.id;

            return (
              <g
                key={st.id}
                className="cursor-pointer group"
                onClick={() => setSelectedStation(st)}
              >
                {/* Critical Glow Ping */}
                {st.status === 'CRITICAL' && (
                  <circle
                    cx={st.x}
                    cy={st.y}
                    r="24"
                    fill="none"
                    stroke={color.fill}
                    strokeWidth="2"
                    className="animate-ping"
                    opacity="0.25"
                  />
                )}

                {/* Selected Ring Outline */}
                {isSelected && (
                  <circle
                    cx={st.x}
                    cy={st.y}
                    r="21"
                    fill="none"
                    stroke="#22d3ee"
                    strokeWidth="3"
                    strokeDasharray="4 2"
                  />
                )}

                {/* Base Node Frame */}
                <circle
                  cx={st.x}
                  cy={st.y}
                  r="14"
                  fill={color.fill}
                  stroke={color.stroke}
                  strokeWidth="2.5"
                  opacity={isSelected ? 1 : 0.9}
                  filter="url(#neon-glow)"
                />

                {/* Inner Node Core */}
                <circle
                  cx={st.x}
                  cy={st.y}
                  r={isSelected ? '9' : '8'}
                  fill={isSelected ? '#e0f2fe' : '#f8fafc'}
                  opacity={0.95}
                />

                {/* Station Label */}
                <text
                  x={st.x + 18}
                  y={st.y - 18}
                  fill="#e2e8f0"
                  fontSize="12"
                  fontWeight="600"
                  fontFamily="monospace"
                  letterSpacing="0.6"
                >
                  {st.name}
                </text>
              </g>
            );
          })}
        </svg>

        {/* Station Details Panel */}
        {selectedStation && (
          <div className="absolute right-5 top-5 w-[320px] rounded-2xl border border-cyan-500/30 bg-slate-950/90 p-4 shadow-2xl backdrop-blur-md">
            <div className="flex items-start justify-between mb-3">
              <div>
                <p className="text-[10px] uppercase tracking-[0.24em] text-cyan-300/80 font-mono">Selected Station</p>
                <h3 className="text-xl font-bold text-white mt-1">{selectedStation.name}</h3>
              </div>
              <button
                onClick={() => setSelectedStation(null)}
                className="rounded-full border border-slate-700 bg-slate-900 p-1.5 text-slate-300 hover:text-white transition-colors"
                aria-label="Close station details"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <div className="space-y-3 text-sm">
              <div className="flex items-center justify-between rounded-xl bg-slate-900/70 px-3 py-2">
                <span className="text-slate-400 flex items-center gap-2"><Users className="w-4 h-4 text-cyan-400" />Occupancy</span>
                <span className="text-white font-semibold">{selectedStation.occupancy_pct}%</span>
              </div>

              <div className="flex items-center justify-between rounded-xl bg-slate-900/70 px-3 py-2">
                <span className="text-slate-400 flex items-center gap-2"><Train className="w-4 h-4 text-violet-400" /> Line</span>
                <span className="text-white font-semibold">{selectedStation.line}</span>
              </div>

              <div className="flex items-center justify-between rounded-xl bg-slate-900/70 px-3 py-2">
                <span className="text-slate-400 flex items-center gap-2"><AlertTriangle className="w-4 h-4 text-amber-400" /> Status</span>
                <span className="text-white font-semibold">{selectedStation.status}</span>
              </div>

              <div className="grid grid-cols-2 gap-3 mt-3">
                <div className="rounded-xl bg-slate-900/70 px-3 py-2">
                  <div className="text-[10px] uppercase tracking-[0.18em] text-slate-500 font-mono">Inflow</div>
                  <div className="text-lg font-bold text-cyan-300 mt-1">{selectedStation.inflow_rate}</div>
                </div>
                <div className="rounded-xl bg-slate-900/70 px-3 py-2">
                  <div className="text-[10px] uppercase tracking-[0.18em] text-slate-500 font-mono">Platforms</div>
                  <div className="text-lg font-bold text-violet-300 mt-1">{selectedStation.platform_count}</div>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
