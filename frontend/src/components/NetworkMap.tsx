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

  const fetchMapData = () => {
    fetch('http://localhost:8000/api/network/map')
      .then((res) => res.json())
      .then((data) => {
        setLines(data.lines || []);
        setStations(data.stations || []);
      })
      .catch((err) => console.error('Map fetch error:', err))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    fetchMapData();
    const interval = setInterval(fetchMapData, 5000); // 5 sec live telemetry poll
    return () => clearInterval(interval);
  }, []);

  const getNodeColor = (status: string) => {
    switch (status) {
      case 'CRITICAL':
        return { fill: '#ef4444', glow: 'rgba(239,68,68,0.7)', text: 'text-rose-400' };
      case 'ELEVATED':
        return { fill: '#f59e0b', glow: 'rgba(245,158,11,0.7)', text: 'text-amber-400' };
      default:
        return { fill: '#10b981', glow: 'rgba(16,185,129,0.7)', text: 'text-emerald-400' };
    }
  };

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center h-96 text-cyan-400 gap-3 font-mono text-xs bg-slate-900/40 rounded-2xl border border-slate-800">
        <Activity className="w-6 h-6 animate-pulse" />
        LOADING METRO NETWORK TELEMETRY...
      </div>
    );
  }

  return (
    <div className="w-full bg-slate-900/40 border border-slate-800/80 rounded-2xl p-6 shadow-2xl backdrop-blur-md">
      {/* Header and Legend */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 mb-4 border-b border-slate-800/80">
        <div>
          <div className="flex items-center gap-2">
            <span className="h-2 w-2 rounded-full bg-cyan-400 animate-ping" />
            <h2 className="text-sm font-bold tracking-wider uppercase text-slate-100">
              Live Metro Network Topology
            </h2>
          </div>
          <p className="text-xs text-slate-400 mt-0.5">Click any station node to view real-time station metrics</p>
        </div>

        <div className="flex items-center gap-4 bg-slate-950/70 border border-slate-800 px-4 py-2 rounded-xl text-xs font-mono">
          <span className="flex items-center gap-1.5 text-slate-300">
            <span className="w-2.5 h-2.5 rounded-full bg-emerald-500 shadow-[0_0_8px_#10b981]" />
            &lt;60% Normal
          </span>
          <span className="flex items-center gap-1.5 text-slate-300">
            <span className="w-2.5 h-2.5 rounded-full bg-amber-500 shadow-[0_0_8px_#f59e0b]" />
            60-80% Elevated
          </span>
          <span className="flex items-center gap-1.5 text-slate-300">
            <span className="w-2.5 h-2.5 rounded-full bg-rose-500 shadow-[0_0_8px_#ef4444]" />
            &gt;80% Congested
          </span>
        </div>
      </div>

      {/* Responsive SVG Map Canvas */}
      <div className="relative w-full h-[520px] bg-[#030712] rounded-xl border border-slate-800/80 overflow-hidden flex items-center justify-center">
        <svg
          viewBox="0 0 1100 600"
          className="w-full h-full"
          preserveAspectRatio="xMidYMid meet"
          xmlns="http://www.w3.org/2000/svg"
        >
          {/* Background Grid Pattern */}
          <defs>
            <pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse">
              <path d="M 40 0 L 0 0 0 40" fill="none" stroke="#1e293b" strokeWidth="0.6" opacity="0.3" />
            </pattern>
          </defs>
          <rect width="100%" height="100%" fill="url(#grid)" />

          {/* Metro Lines */}
          {lines.map((line) => (
            <g key={line.id}>
              {/* Outer soft glow line */}
              <path
                d={line.path}
                stroke={line.color}
                strokeWidth="10"
                strokeLinecap="round"
                strokeLinejoin="round"
                fill="none"
                opacity="0.2"
              />
              {/* Core metro track line */}
              <path
                d={line.path}
                stroke={line.color}
                strokeWidth="4"
                strokeLinecap="round"
                strokeLinejoin="round"
                fill="none"
              />
            </g>
          ))}

          {/* Station Nodes */}
          {stations.map((st) => {
            const color = getNodeColor(st.status);
            const isSelected = selectedStation?.id === st.id;

            return (
              <g
                key={st.id}
                className="cursor-pointer group"
                onClick={() => setSelectedStation(st)}
              >
                {/* Ping ring if status is critical */}
                {st.status === 'CRITICAL' && (
                  <circle
                    cx={st.x}
                    cy={st.y}
                    r="20"
                    fill="none"
                    stroke={color.fill}
                    strokeWidth="1.5"
                    className="animate-ping"
                    opacity="0.3"
                  />
                )}

                {/* Selected Ring */}
                {isSelected && (
                  <circle
                    cx={st.x}
                    cy={st.y}
                    r="18"
                    fill="none"
                    stroke="#38bdf8"
                    strokeWidth="2.5"
                    strokeDasharray="4 2"
                  />
                )}

                {/* Outer Node Circle */}
                <circle
                  cx={st.x}
                  cy={st.y}
                  r="12"
                  fill="#030712"
                  stroke={color.fill}
                  strokeWidth="3.5"
                  style={{ filter: `drop-shadow(0 0 8px ${color.glow})` }}
                />

                {/* Inner Center Dot */}
                <circle cx={st.x} cy={st.y} r="4.5" fill={color.fill} />

                {/* Station Label */}
                <text
                  x={st.x}
                  y={st.y - 18}
                  fill="#f8fafc"
                  fontSize="11"
                  fontFamily="monospace"
                  fontWeight="bold"
                  textAnchor="middle"
                  className="select-none pointer-events-none drop-shadow-[0_2px_4px_rgba(0,0,0,0.9)]"
                >
                  {st.name}
                </text>
              </g>
            );
          })}
        </svg>

        {/* Selected Station Telemetry Popup / Drawer */}
        {selectedStation && (
          <div className="absolute top-4 right-4 w-72 bg-slate-950/95 border border-slate-700/80 rounded-xl p-4 shadow-2xl backdrop-blur-md z-20">
            <div className="flex items-center justify-between pb-2 border-b border-slate-800">
              <div>
                <span className="text-[10px] font-mono text-cyan-400 font-bold uppercase block">
                  {selectedStation.id} • {selectedStation.line}
                </span>
                <h3 className="text-sm font-bold text-slate-100">{selectedStation.name}</h3>
              </div>
              <button
                onClick={() => setSelectedStation(null)}
                className="p-1 text-slate-400 hover:text-slate-100 rounded-lg hover:bg-slate-800 transition"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <div className="mt-3 space-y-3">
              <div>
                <div className="flex justify-between text-xs font-mono mb-1">
                  <span className="text-slate-400">Current Occupancy</span>
                  <span className={`font-bold ${getNodeColor(selectedStation.status).text}`}>
                    {selectedStation.occupancy_pct}%
                  </span>
                </div>
                <div className="w-full bg-slate-900 h-2 rounded-full overflow-hidden border border-slate-800">
                  <div
                    className={`h-full rounded-full transition-all duration-500 ${
                      selectedStation.status === 'CRITICAL' ? 'bg-rose-500' :
                      selectedStation.status === 'ELEVATED' ? 'bg-amber-500' : 'bg-emerald-500'
                    }`}
                    style={{ width: `${selectedStation.occupancy_pct}%` }}
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-2 text-xs font-mono">
                <div className="p-2 bg-slate-900/60 border border-slate-800 rounded-lg">
                  <span className="text-[10px] text-slate-500 uppercase block">Inflow</span>
                  <span className="text-slate-200 font-bold flex items-center gap-1 mt-0.5">
                    <Users className="w-3.5 h-3.5 text-cyan-400" />
                    {selectedStation.inflow_rate} /m
                  </span>
                </div>
                <div className="p-2 bg-slate-900/60 border border-slate-800 rounded-lg">
                  <span className="text-[10px] text-slate-500 uppercase block">Platforms</span>
                  <span className="text-slate-200 font-bold flex items-center gap-1 mt-0.5">
                    <Train className="w-3.5 h-3.5 text-blue-400" />
                    {selectedStation.platform_count} Active
                  </span>
                </div>
              </div>

              {selectedStation.status === 'CRITICAL' && (
                <div className="p-2.5 bg-rose-500/10 border border-rose-500/30 rounded-lg flex items-center gap-2 text-rose-300 text-xs">
                  <AlertTriangle className="w-4 h-4 text-rose-400 shrink-0" />
                  <span>Threshold Exceeded. Surge diversion required.</span>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};