"use client";

import { useEffect, useState } from "react";
import { Activity, Search, ArrowUpRight, ArrowDownRight, ShieldCheck, AlertTriangle, Users, Info } from "lucide-react";
import { api } from "@/lib/api";
import { StationDensity } from "@/types";
import { socketClient } from "@/lib/socket";

export default function LiveMonitoringPage() {
  const [stations, setStations] = useState<StationDensity[]>([]);
  const [filterLine, setFilterLine] = useState<string>("ALL");
  const [filterStatus, setFilterStatus] = useState<string>("ALL");
  const [searchQuery, setSearchQuery] = useState<string>("");
  const [loading, setLoading] = useState(true);

  const loadData = async () => {
    try {
      const data = await api.getDensities();
      setStations(data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
    const unsubscribe = socketClient.subscribe((msg) => {
      if (msg.event === "TELEMETRY_UPDATE" && msg.summary?.stations) {
        setStations(msg.summary.stations);
      }
    });
    return () => unsubscribe();
  }, []);

  const filteredStations = stations.filter((s) => {
    const matchesLine =
      filterLine === "ALL" ||
      s.line_name.toLowerCase().includes(filterLine.toLowerCase());
    const matchesStatus =
      filterStatus === "ALL" || s.status === filterStatus;
    const matchesSearch =
      s.station_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      s.station_code.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesLine && matchesStatus && matchesSearch;
  });

  const criticalCount = stations.filter((s) => s.status === "CRITICAL").length;
  const moderateCount = stations.filter((s) => s.status === "MODERATE").length;
  const normalCount = stations.filter((s) => s.status === "NORMAL").length;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800 pb-4">
        <div>
          <h1 className="text-2xl font-black text-white flex items-center gap-2">
            <Activity className="w-6 h-6 text-emerald-400" />
            BMRCL Station Crowd Density & Capacity Gauges
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Observed passenger demand, platform capacity gauges, and crowd risk classification across BMRCL Purple & Green lines.
          </p>
        </div>

        {/* Status Indicators */}
        <div className="flex items-center gap-2">
          <span className="px-2.5 py-1 rounded-lg bg-slate-900 border border-slate-800 text-[11px] font-mono text-slate-300">
            DATA MODE: <span className="text-purple-400 font-bold">HISTORICAL REPLAY</span>
          </span>
          <span className="px-2.5 py-1 rounded-lg bg-slate-900 border border-slate-800 text-[11px] font-mono text-slate-300">
            LIVE SENSORS: <span className="text-amber-400 font-bold">NOT CONNECTED</span>
          </span>
        </div>
      </div>

      {/* Decision-Support & Classification Standard Banner */}
      <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-4 space-y-3">
        <div className="flex items-start gap-3">
          <Info className="w-5 h-5 text-blue-400 shrink-0 mt-0.5" />
          <div className="space-y-1">
            <div className="text-xs font-bold text-white flex items-center gap-2">
              <span>Decision-Support Crowd Classification Standard</span>
              <span className="text-[10px] text-slate-400 font-normal">
                (Derived from observed BMRCL RTI demand relative to configured platform capacity)
              </span>
            </div>
            <p className="text-[11px] text-slate-400 leading-relaxed">
              Occupancy is a decision-support classification derived from observed station demand relative to the configured station capacity. Not a physical live sensor measurement.
            </p>
          </div>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 pt-1 text-xs">
          <button
            onClick={() => setFilterStatus(filterStatus === "NORMAL" ? "ALL" : "NORMAL")}
            className={`p-2.5 rounded-lg border flex items-center justify-between transition ${
              filterStatus === "NORMAL"
                ? "bg-emerald-500/20 border-emerald-500 text-emerald-300"
                : "bg-slate-900/60 border-emerald-500/30 text-emerald-400 hover:bg-emerald-500/10"
            }`}
          >
            <div className="flex items-center gap-2">
              <span className="w-2.5 h-2.5 rounded-full bg-emerald-400"></span>
              <span className="font-bold">NORMAL (&lt; 60%)</span>
            </div>
            <span className="font-mono font-bold text-white">{normalCount} stations</span>
          </button>

          <button
            onClick={() => setFilterStatus(filterStatus === "MODERATE" ? "ALL" : "MODERATE")}
            className={`p-2.5 rounded-lg border flex items-center justify-between transition ${
              filterStatus === "MODERATE"
                ? "bg-amber-500/20 border-amber-500 text-amber-300"
                : "bg-slate-900/60 border-amber-500/30 text-amber-400 hover:bg-amber-500/10"
            }`}
          >
            <div className="flex items-center gap-2">
              <span className="w-2.5 h-2.5 rounded-full bg-amber-400"></span>
              <span className="font-bold">MODERATE (60% to &lt; 80%)</span>
            </div>
            <span className="font-mono font-bold text-white">{moderateCount} stations</span>
          </button>

          <button
            onClick={() => setFilterStatus(filterStatus === "CRITICAL" ? "ALL" : "CRITICAL")}
            className={`p-2.5 rounded-lg border flex items-center justify-between transition ${
              filterStatus === "CRITICAL"
                ? "bg-rose-500/20 border-rose-500 text-rose-300"
                : "bg-slate-900/60 border-rose-500/30 text-rose-400 hover:bg-rose-500/10"
            }`}
          >
            <div className="flex items-center gap-2">
              <span className="w-2.5 h-2.5 rounded-full bg-rose-400 animate-pulse"></span>
              <span className="font-bold">CRITICAL (≥ 80%)</span>
            </div>
            <span className="font-mono font-bold text-rose-400">{criticalCount} stations</span>
          </button>
        </div>
      </div>

      {/* Filter and Search Controls */}
      <div className="flex flex-wrap items-center justify-between gap-3 bg-[#0d1424] border border-slate-800 p-3 rounded-xl">
        <div className="relative flex-1 min-w-[240px]">
          <Search className="w-4 h-4 text-slate-500 absolute left-3 top-2.5" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search BMRCL station name or code (e.g. Majestic, KGWA)..."
            className="w-full bg-slate-900 border border-slate-700 rounded-lg pl-9 pr-4 py-1.5 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-purple-500"
          />
        </div>

        {/* Line Filter */}
        <div className="flex items-center gap-1.5 text-xs">
          <button
            onClick={() => setFilterLine("ALL")}
            className={`px-3 py-1.5 rounded-lg font-semibold transition ${
              filterLine === "ALL" ? "bg-purple-600 text-white shadow-md shadow-purple-600/20" : "text-slate-400 hover:text-white bg-slate-900 border border-slate-800"
            }`}
          >
            All Corridors (83)
          </button>
          <button
            onClick={() => setFilterLine("Purple")}
            className={`px-3 py-1.5 rounded-lg font-semibold transition ${
              filterLine === "Purple" ? "bg-purple-700 text-white shadow-md shadow-purple-700/20" : "text-slate-400 hover:text-white bg-slate-900 border border-slate-800"
            }`}
          >
            Purple Line
          </button>
          <button
            onClick={() => setFilterLine("Green")}
            className={`px-3 py-1.5 rounded-lg font-semibold transition ${
              filterLine === "Green" ? "bg-emerald-600 text-white shadow-md shadow-emerald-600/20" : "text-slate-400 hover:text-white bg-slate-900 border border-slate-800"
            }`}
          >
            Green Line
          </button>
        </div>
      </div>

      {/* Station Density Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {filteredStations.map((s) => {
          const isCritical = s.status === "CRITICAL" || s.density_percentage >= 80;
          const isModerate = !isCritical && (s.status === "MODERATE" || s.density_percentage >= 60);

          return (
            <div
              key={s.station_id}
              className={`bg-[#0d1424] border rounded-xl p-4 space-y-3 transition-all hover:border-slate-600 ${
                isCritical
                  ? "border-rose-500/60 shadow-lg shadow-rose-500/10 bg-rose-950/10"
                  : isModerate
                  ? "border-amber-500/40 bg-amber-950/10"
                  : "border-slate-800"
              }`}
            >
              {/* Card Header */}
              <div className="flex items-start justify-between">
                <div>
                  <div className="font-extrabold text-sm text-white flex items-center gap-1.5">
                    {s.station_name}
                  </div>
                  <div className="text-[11px] text-slate-400 font-mono mt-0.5">
                    {s.station_code} • {s.line_name}
                  </div>
                </div>

                <span
                  className={`text-[10px] px-2.5 py-1 rounded font-bold uppercase tracking-wider ${
                    isCritical
                      ? "bg-rose-500/20 text-rose-300 border border-rose-500/40 animate-pulse"
                      : isModerate
                      ? "bg-amber-500/20 text-amber-300 border border-amber-500/40"
                      : "bg-emerald-500/20 text-emerald-300 border border-emerald-500/40"
                  }`}
                >
                  {isCritical ? "CRITICAL" : isModerate ? "MODERATE" : "NORMAL"}
                </span>
              </div>

              {/* Progress Bar Gauge */}
              <div className="space-y-1">
                <div className="flex justify-between text-xs">
                  <span className="text-slate-400">Platform Occupancy</span>
                  <span className="font-mono font-bold text-white">{s.density_percentage}%</span>
                </div>
                <div className="w-full h-2.5 bg-slate-900 rounded-full overflow-hidden border border-slate-800">
                  <div
                    className={`h-full transition-all duration-500 ${
                      isCritical ? "bg-rose-500" : isModerate ? "bg-amber-500" : "bg-emerald-500"
                    }`}
                    style={{ width: `${Math.min(100, s.density_percentage)}%` }}
                  ></div>
                </div>
                <div className="flex justify-between text-[10px] text-slate-500 font-mono pt-0.5">
                  <span>Capacity: {s.platform_capacity?.toLocaleString() || "6,000"} pax</span>
                  <span>Target: &lt; 60%</span>
                </div>
              </div>

              {/* Inflow vs Outflow Rates */}
              <div className="grid grid-cols-2 gap-2 text-xs pt-1 border-t border-slate-800/80">
                <div className="flex items-center gap-1.5 p-2 bg-slate-900/60 rounded-lg">
                  <ArrowUpRight className="w-3.5 h-3.5 text-emerald-400" />
                  <div>
                    <div className="text-[10px] text-slate-400 uppercase font-semibold">Observed Inflow</div>
                    <div className="font-bold text-white font-mono">{s.inflow_rate_ppm} pax/hr</div>
                  </div>
                </div>

                <div className="flex items-center gap-1.5 p-2 bg-slate-900/60 rounded-lg">
                  <ArrowDownRight className="w-3.5 h-3.5 text-rose-400" />
                  <div>
                    <div className="text-[10px] text-slate-400 uppercase font-semibold">Observed Outflow</div>
                    <div className="font-bold text-white font-mono">{s.outflow_rate_ppm} pax/hr</div>
                  </div>
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {filteredStations.length === 0 && (
        <div className="p-12 text-center text-slate-400 bg-[#0d1424] border border-slate-800 rounded-xl space-y-2">
          <p className="text-sm font-semibold text-white">No stations match the selected filters.</p>
          <p className="text-xs text-slate-500">Reset your corridor or classification filter to view BMRCL stations.</p>
        </div>
      )}
    </div>
  );
}
