"use client";

import { StationDensity } from "@/types";
import { Train, Info, MapPin, Search, Layers, GitFork, Compass } from "lucide-react";
import { useState, useMemo } from "react";

interface MetroMapProps {
  stations: StationDensity[];
  onSelectStation?: (station: StationDensity) => void;
  selectedStationId?: number | null;
}

type CorridorFilter = "ALL" | "Purple Line" | "Green Line";

export function MetroMap({ stations, onSelectStation, selectedStationId }: MetroMapProps) {
  const [hoveredStation, setHoveredStation] = useState<StationDensity | null>(null);
  const [activeCorridor, setActiveCorridor] = useState<CorridorFilter>("ALL");
  const [searchQuery, setSearchQuery] = useState<string>("");

  // Categorize stations by corridor
  const purpleLineStations = useMemo(
    () => stations.filter((s) => s.line_name.includes("Purple")).sort((a, b) => a.station_id - b.station_id),
    [stations]
  );
  const greenLineStations = useMemo(
    () => stations.filter((s) => s.line_name.includes("Green")).sort((a, b) => a.station_id - b.station_id),
    [stations]
  );

  const displayedStations = useMemo(() => {
    let list = stations;
    if (activeCorridor === "Purple Line") {
      list = list.filter((s) => s.line_name.includes("Purple"));
    } else if (activeCorridor === "Green Line") {
      list = list.filter((s) => s.line_name.includes("Green"));
    }
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      list = list.filter(
        (s) =>
          s.station_name.toLowerCase().includes(q) ||
          s.station_code.toLowerCase().includes(q) ||
          s.line_name.toLowerCase().includes(q)
      );
    }
    return list;
  }, [stations, activeCorridor, searchQuery]);

  const getStatusColor = (status: string) => {
    if (status === "CRITICAL") return "#ef4444"; // Red
    if (status === "MODERATE") return "#f59e0b"; // Amber
    return "#10b981"; // Emerald
  };

  const getLineThemeColor = (line: string) => {
    if (line.includes("Purple")) return "#a855f7"; // Purple
    if (line.includes("Green")) return "#10b981"; // Green
    return "#38bdf8"; // Cyan for Interchange
  };

  return (
    <div className="relative w-full bg-[#090d18] border border-slate-800 rounded-2xl p-5 overflow-hidden flex flex-col gap-4 shadow-xl">
      {/* Map Header & Controls */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 z-10 border-b border-slate-800/80 pb-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="p-1.5 rounded-lg bg-purple-500/10 border border-purple-500/20 text-purple-400">
              <Compass className="w-4 h-4" />
            </span>
            <h3 className="text-base font-bold text-white tracking-wide">
              BMRCL Namma Metro Network Map
            </h3>
            <span className="text-[10px] px-2 py-0.5 rounded-full bg-slate-800 text-purple-400 border border-slate-700 font-mono font-bold">
              {stations.length} Stations (GTFS Topology)
            </span>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Bengaluru Metro Rail Corporation Limited • Purple Line (East-West) & Green Line (North-South) • Central Interchange: Majestic
          </p>
        </div>

        {/* Legend */}
        <div className="flex flex-wrap items-center gap-3 text-xs bg-slate-900/80 px-3 py-1.5 rounded-lg border border-slate-800">
          <div className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-emerald-500 inline-block shadow-[0_0_8px_#10b981]" />
            <span className="text-slate-300 text-[11px]">Normal (&lt;50%)</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-amber-500 inline-block shadow-[0_0_8px_#f59e0b]" />
            <span className="text-slate-300 text-[11px]">Moderate (50-80%)</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-rose-500 inline-block shadow-[0_0_8px_#ef4444]" />
            <span className="text-rose-400 font-semibold text-[11px]">Critical (&gt;80%)</span>
          </div>
          <div className="flex items-center gap-1.5 pl-2 border-l border-slate-700">
            <span className="w-3 h-3 rounded-full border-2 border-cyan-400 bg-cyan-950 inline-block" />
            <span className="text-cyan-300 font-medium text-[11px]">Majestic Interchange</span>
          </div>
        </div>
      </div>

      {/* Corridor Filter Tabs & Search */}
      <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3">
        <div className="flex items-center gap-1.5 bg-[#0d1424] border border-slate-800 p-1 rounded-xl text-xs overflow-x-auto">
          <button
            onClick={() => setActiveCorridor("ALL")}
            className={`px-3 py-1.5 rounded-lg font-semibold transition-all whitespace-nowrap ${
              activeCorridor === "ALL"
                ? "bg-gradient-to-r from-purple-600 to-indigo-600 text-white shadow-md shadow-purple-900/40"
                : "text-slate-400 hover:text-white"
            }`}
          >
            All BMRCL Network ({stations.length})
          </button>
          <button
            onClick={() => setActiveCorridor("Purple Line")}
            className={`px-3 py-1.5 rounded-lg font-semibold transition-all flex items-center gap-1.5 whitespace-nowrap ${
              activeCorridor === "Purple Line"
                ? "bg-purple-600 text-white shadow-md shadow-purple-900/40"
                : "text-slate-400 hover:text-purple-300"
            }`}
          >
            <span className="w-2 h-2 rounded-full bg-purple-400" />
            Purple Line ({purpleLineStations.length})
          </button>
          <button
            onClick={() => setActiveCorridor("Green Line")}
            className={`px-3 py-1.5 rounded-lg font-semibold transition-all flex items-center gap-1.5 whitespace-nowrap ${
              activeCorridor === "Green Line"
                ? "bg-emerald-600 text-white shadow-md shadow-emerald-900/40"
                : "text-slate-400 hover:text-emerald-300"
            }`}
          >
            <span className="w-2 h-2 rounded-full bg-emerald-400" />
            Green Line ({greenLineStations.length})
          </button>
        </div>

        {/* Quick Search */}
        <div className="relative min-w-[220px]">
          <Search className="w-3.5 h-3.5 absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search BMRCL station..."
            className="w-full bg-[#0d1424] border border-slate-800 rounded-xl pl-8 pr-3 py-1.5 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-purple-500"
          />
        </div>
      </div>

      {/* Main Map Visualization Area */}
      <div className="relative w-full h-[360px] bg-[#070a12] border border-slate-800/80 rounded-xl overflow-hidden flex flex-col justify-center">
        {/* Background Grid Pattern */}
        <div
          className="absolute inset-0 opacity-15 pointer-events-none"
          style={{
            backgroundImage:
              "radial-gradient(circle at 1px 1px, rgba(148, 163, 184, 0.4) 1px, transparent 0)",
            backgroundSize: "28px 28px",
          }}
        />

        {activeCorridor === "ALL" ? (
          /* BMRCL Network Topological Map (Schematic of intersecting Purple and Green corridors) */
          <div className="relative w-full h-full flex items-center justify-center overflow-x-auto p-4">
            <svg className="w-full h-full min-w-[860px]" viewBox="0 0 960 340">
              <defs>
                <linearGradient id="gradPurple" x1="0%" y1="0%" x2="100%" y2="0%">
                  <stop offset="0%" stopColor="#9333ea" />
                  <stop offset="100%" stopColor="#c084fc" />
                </linearGradient>
                <linearGradient id="gradGreenBmrcl" x1="0%" y1="0%" x2="0%" y2="100%">
                  <stop offset="0%" stopColor="#059669" />
                  <stop offset="100%" stopColor="#34d399" />
                </linearGradient>
              </defs>

              {/* Purple Line Track: Challaghatta (West) -> Mysore Rd -> Majestic (Center) -> MG Road -> Indiranagar -> Whitefield (East) */}
              <path
                d="M 60 170 C 260 170, 360 170, 480 170 C 600 170, 720 170, 900 170"
                fill="none"
                stroke="#9333ea"
                strokeWidth="8"
                strokeLinecap="round"
                opacity="0.9"
              />

              {/* Green Line Track: Madavara / Nagasandra (North) -> Yeshwantpur -> Majestic (intersects Purple) -> Banashankari -> Silk Institute (South) */}
              <path
                d="M 480 30 L 480 310"
                fill="none"
                stroke="#059669"
                strokeWidth="8"
                strokeLinecap="round"
                opacity="0.9"
              />

              {/* Corridor Terminal Labels */}
              <text x="60" y="145" fill="#d8b4fe" fontSize="11" fontWeight="bold">
                Challaghatta (Purple West)
              </text>
              <text x="900" y="145" fill="#d8b4fe" fontSize="11" fontWeight="bold" textAnchor="end">
                Whitefield (Kadugodi) (Purple East)
              </text>
              <text x="500" y="35" fill="#6ee7b7" fontSize="11" fontWeight="bold">
                Madavara / Nagasandra (Green North)
              </text>
              <text x="500" y="315" fill="#6ee7b7" fontSize="11" fontWeight="bold">
                Silk Institute (Green South)
              </text>

              {/* CENTRAL INTERCHANGE: Nadaprabhu Kempegowda Station Majestic (KGWA) */}
              <g
                className="cursor-pointer transition-transform hover:scale-110"
                onClick={() => {
                  const majestic = stations.find((s) => s.station_code === "KGWA" || s.station_name.includes("Majestic"));
                  if (majestic && onSelectStation) onSelectStation(majestic);
                }}
                onMouseEnter={() => {
                  const majestic = stations.find((s) => s.station_code === "KGWA" || s.station_name.includes("Majestic"));
                  if (majestic) setHoveredStation(majestic);
                }}
                onMouseLeave={() => setHoveredStation(null)}
              >
                <circle cx="480" cy="170" r="24" fill="#a855f7" opacity="0.25" className="animate-ping" />
                <circle cx="480" cy="170" r="18" fill="#090d18" stroke="#38bdf8" strokeWidth="4" />
                <circle cx="480" cy="170" r="10" fill="#f59e0b" />
                <text x="480" y="135" fill="#ffffff" fontSize="13" fontWeight="900" textAnchor="middle">
                  Majestic Interchange
                </text>
                <text x="480" y="210" fill="#38bdf8" fontSize="10" fontWeight="bold" textAnchor="middle">
                  Purple ⇄ Green Multi-Level Transfer
                </text>
              </g>

              {/* Key Intermediate Stations on Purple Line */}
              {[
                { name: "Kengeri", code: "KGRI", x: 140, y: 170 },
                { name: "Mysore Road", code: "MYRD", x: 230, y: 170 },
                { name: "Magadi Road", code: "MIRD", x: 330, y: 170 },
                { name: "Sir M. Visvesvaraya", code: "SMV", x: 410, y: 170 },
                { name: "Cubbon Park", code: "CBPK", x: 550, y: 170 },
                { name: "MG Road", code: "MGRD", x: 620, y: 170 },
                { name: "Indiranagar", code: "IDN", x: 690, y: 170 },
                { name: "Baiyappanahalli", code: "BYPH", x: 760, y: 170 },
                { name: "KR Puram", code: "KRP", x: 820, y: 170 },
              ].map((kSt, i) => {
                const found = stations.find((s) => s.station_code === kSt.code || s.station_name.includes(kSt.name));
                const color = found ? getStatusColor(found.status) : "#c084fc";
                const isSelected = found && selectedStationId === found.station_id;

                return (
                  <g
                    key={`purple-node-${i}`}
                    className="cursor-pointer transition-transform hover:scale-125"
                    onClick={() => found && onSelectStation && onSelectStation(found)}
                    onMouseEnter={() => found && setHoveredStation(found)}
                    onMouseLeave={() => setHoveredStation(null)}
                  >
                    <circle
                      cx={kSt.x}
                      cy={kSt.y}
                      r={isSelected ? "11" : "8"}
                      fill="#0b0f17"
                      stroke={isSelected ? "#38bdf8" : color}
                      strokeWidth="2.5"
                    />
                    <circle cx={kSt.x} cy={kSt.y} r="4" fill={color} />
                    <text
                      x={kSt.x}
                      y={i % 2 === 0 ? kSt.y - 13 : kSt.y + 20}
                      textAnchor="middle"
                      fill="#cbd5e1"
                      fontSize="9.5"
                      fontWeight="500"
                    >
                      {kSt.name}
                    </text>
                  </g>
                );
              })}

              {/* Key Intermediate Stations on Green Line */}
              {[
                { name: "Peenya", code: "PENA", x: 480, y: 70 },
                { name: "Yeshwantpur", code: "YPM", x: 480, y: 110 },
                { name: "Krishna Rajendra Market", code: "KRMT", x: 480, y: 220 },
                { name: "Jayanagar", code: "JAYN", x: 480, y: 250 },
                { name: "Banashankari", code: "BSNK", x: 480, y: 280 },
              ].map((kSt, i) => {
                const found = stations.find((s) => s.station_code === kSt.code || s.station_name.includes(kSt.name));
                const color = found ? getStatusColor(found.status) : "#34d399";
                const isSelected = found && selectedStationId === found.station_id;

                return (
                  <g
                    key={`green-node-${i}`}
                    className="cursor-pointer transition-transform hover:scale-125"
                    onClick={() => found && onSelectStation && onSelectStation(found)}
                    onMouseEnter={() => found && setHoveredStation(found)}
                    onMouseLeave={() => setHoveredStation(null)}
                  >
                    <circle
                      cx={kSt.x}
                      cy={kSt.y}
                      r={isSelected ? "11" : "8"}
                      fill="#0b0f17"
                      stroke={isSelected ? "#38bdf8" : color}
                      strokeWidth="2.5"
                    />
                    <circle cx={kSt.x} cy={kSt.y} r="4" fill={color} />
                    <text
                      x={kSt.x + 18}
                      y={kSt.y + 4}
                      textAnchor="start"
                      fill="#cbd5e1"
                      fontSize="9.5"
                      fontWeight="500"
                    >
                      {kSt.name}
                    </text>
                  </g>
                );
              })}
            </svg>
          </div>
        ) : (
          /* Linear Track Progression View for specific corridor */
          <div className="w-full h-full overflow-x-auto p-4 flex items-center">
            <div className="flex items-center min-w-max gap-4 px-6">
              {displayedStations.map((st, idx) => {
                const color = getStatusColor(st.status);
                const isSelected = selectedStationId === st.station_id;
                const isInterchange = st.is_interchange || st.station_code === "KGWA";

                return (
                  <div key={st.station_id} className="flex items-center">
                    {/* Node Card */}
                    <div
                      onClick={() => onSelectStation && onSelectStation(st)}
                      onMouseEnter={() => setHoveredStation(st)}
                      onMouseLeave={() => setHoveredStation(null)}
                      className={`relative flex flex-col items-center cursor-pointer transition-all duration-200 p-2.5 rounded-xl border ${
                        isSelected
                          ? "bg-slate-800/90 border-purple-400 ring-2 ring-purple-500/40 scale-105"
                          : "bg-slate-900/60 border-slate-800 hover:border-slate-600 hover:bg-slate-800/60 hover:scale-105"
                      }`}
                    >
                      {/* Interchange badge */}
                      {isInterchange && (
                        <span className="absolute -top-2.5 px-1.5 py-0.5 rounded bg-cyan-950 border border-cyan-400/80 text-cyan-300 text-[9px] font-mono font-bold flex items-center gap-1">
                          <GitFork className="w-2.5 h-2.5" /> Majestic Transfer
                        </span>
                      )}

                      {/* Station Code */}
                      <span className="text-[10px] font-mono text-slate-400 font-semibold mb-1">
                        {st.station_code}
                      </span>

                      {/* Interactive Density Orb */}
                      <div className="relative my-1">
                        {st.status === "CRITICAL" && (
                          <div
                            className="absolute inset-0 rounded-full animate-ping opacity-60"
                            style={{ backgroundColor: color }}
                          />
                        )}
                        <div
                          className="w-7 h-7 rounded-full border-2 flex items-center justify-center font-bold text-[10px] text-white shadow-lg transition-transform"
                          style={{
                            borderColor: color,
                            backgroundColor: "#070a12",
                            boxShadow: `0 0 10px ${color}40`,
                          }}
                        >
                          <div className="w-3.5 h-3.5 rounded-full" style={{ backgroundColor: color }} />
                        </div>
                      </div>

                      {/* Station Name */}
                      <div className="text-xs font-bold text-white text-center max-w-[110px] truncate mt-1">
                        {st.station_name}
                      </div>

                      {/* Density % */}
                      <div className="text-[10px] font-mono font-semibold mt-0.5" style={{ color }}>
                        {st.density_percentage}%
                      </div>
                    </div>

                    {/* Connecting Track segment to next station */}
                    {idx < displayedStations.length - 1 && (
                      <div
                        className="w-8 h-1.5 rounded-full mx-1 opacity-70"
                        style={{ backgroundColor: getLineThemeColor(st.line_name) }}
                      />
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        )}
      </div>

      {/* Hovered Station Live Telemetry Floating Tooltip */}
      {hoveredStation && (
        <div className="absolute bottom-5 left-5 z-30 bg-[#0b101e]/95 border border-slate-700 p-3.5 rounded-xl shadow-2xl text-xs backdrop-blur-md space-y-1.5 min-w-[260px]">
          <div className="flex items-center justify-between gap-3 border-b border-slate-800 pb-1.5">
            <div className="font-extrabold text-white text-sm">{hoveredStation.station_name}</div>
            <span
              className="text-[10px] px-2 py-0.5 rounded font-mono font-bold"
              style={{
                backgroundColor: `${getLineThemeColor(hoveredStation.line_name)}20`,
                color: getLineThemeColor(hoveredStation.line_name),
              }}
            >
              {hoveredStation.station_code}
            </span>
          </div>

          <div className="text-[11px] text-slate-400 font-semibold">
            {hoveredStation.line_name} • Capacity: {hoveredStation.platform_capacity.toLocaleString()} pax
          </div>

          <div className="grid grid-cols-3 gap-2 pt-1 text-[11px]">
            <div className="bg-slate-900/80 p-1.5 rounded border border-slate-800">
              <div className="text-[10px] text-slate-400">Observed Entries</div>
              <div className="font-bold text-emerald-400">{hoveredStation.inflow_rate_ppm} pax/hr</div>
            </div>
            <div className="bg-slate-900/80 p-1.5 rounded border border-slate-800">
              <div className="text-[10px] text-slate-400">Observed Exits</div>
              <div className="font-bold text-rose-400">{hoveredStation.outflow_rate_ppm} pax/hr</div>
            </div>
            <div className="bg-slate-900/80 p-1.5 rounded border border-slate-800">
              <div className="text-[10px] text-slate-400">Load %</div>
              <div
                className="font-bold"
                style={{ color: getStatusColor(hoveredStation.status) }}
              >
                {hoveredStation.density_percentage}%
              </div>
            </div>
          </div>

          {hoveredStation.is_interchange && (
            <div className="text-[10px] text-cyan-300 bg-cyan-950/60 border border-cyan-800/60 p-1 rounded font-semibold text-center mt-1">
              Multi-Level Transfer Node (Kempegowda Majestic)
            </div>
          )}
        </div>
      )}
    </div>
  );
}
