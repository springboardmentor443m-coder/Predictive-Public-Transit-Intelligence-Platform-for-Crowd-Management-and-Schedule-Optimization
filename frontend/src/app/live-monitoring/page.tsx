"use client";

import { useEffect, useState } from "react";
import { Activity, Search, Filter, ArrowUpRight, ArrowDownRight, Layers } from "lucide-react";
import { api } from "@/lib/api";
import { StationDensity } from "@/types";
import { socketClient } from "@/lib/socket";

export default function LiveMonitoringPage() {
  const [stations, setStations] = useState<StationDensity[]>([]);
  const [filterLine, setFilterLine] = useState<string>("ALL");
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
    const matchesLine = filterLine === "ALL" || s.line_name === filterLine;
    const matchesSearch = s.station_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
                          s.station_code.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesLine && matchesSearch;
  });

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800 pb-4">
        <div>
          <h1 className="text-2xl font-black text-white flex items-center gap-2">
            <Activity className="w-6 h-6 text-emerald-400" />
            Live Crowd Density & Platform Gauges
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Real-time footfall inflow/outflow, capacity gauges, and congestion risk classification across all stations
          </p>
        </div>

        {/* Filter Controls */}
        <div className="flex flex-wrap items-center gap-3">
          <div className="relative">
            <Search className="w-4 h-4 text-slate-500 absolute left-3 top-2.5" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search station name..."
              className="bg-[#0d1424] border border-slate-800 rounded-lg pl-9 pr-4 py-1.5 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-blue-500"
            />
          </div>

          <div className="flex items-center gap-1.5 bg-[#0d1424] border border-slate-800 p-1 rounded-lg text-xs">
            <button
              onClick={() => setFilterLine("ALL")}
              className={`px-2.5 py-1 rounded font-medium ${filterLine === "ALL" ? "bg-blue-600 text-white" : "text-slate-400 hover:text-white"}`}
            >
              All Lines
            </button>
            <button
              onClick={() => setFilterLine("Red Line")}
              className={`px-2.5 py-1 rounded font-medium ${filterLine === "Red Line" ? "bg-rose-600 text-white" : "text-slate-400 hover:text-white"}`}
            >
              Red Line
            </button>
            <button
              onClick={() => setFilterLine("Blue Line")}
              className={`px-2.5 py-1 rounded font-medium ${filterLine === "Blue Line" ? "bg-blue-600 text-white" : "text-slate-400 hover:text-white"}`}
            >
              Blue Line
            </button>
          </div>
        </div>
      </div>

      {/* Station Density Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {filteredStations.map((s) => {
          const isCritical = s.status === "CRITICAL";
          const isModerate = s.status === "MODERATE";

          return (
            <div
              key={s.station_id}
              className={`bg-[#0d1424] border rounded-xl p-4 space-y-3 transition-all hover:border-slate-600 ${
                isCritical
                  ? "border-rose-500/50 shadow-lg shadow-rose-500/10"
                  : isModerate
                  ? "border-amber-500/40"
                  : "border-slate-800"
              }`}
            >
              {/* Card Header */}
              <div className="flex items-start justify-between">
                <div>
                  <div className="font-extrabold text-sm text-white">{s.station_name}</div>
                  <div className="text-[11px] text-slate-400 font-mono">
                    {s.station_code} • {s.line_name}
                  </div>
                </div>

                <span
                  className={`text-[10px] px-2.5 py-1 rounded font-bold uppercase ${
                    isCritical
                      ? "bg-rose-500/20 text-rose-400 border border-rose-500/30 animate-pulse"
                      : isModerate
                      ? "bg-amber-500/20 text-amber-400 border border-amber-500/30"
                      : "bg-emerald-500/20 text-emerald-400 border border-emerald-500/30"
                  }`}
                >
                  {s.status}
                </span>
              </div>

              {/* Progress Bar Gauge */}
              <div className="space-y-1">
                <div className="flex justify-between text-xs">
                  <span className="text-slate-400">Platform Density</span>
                  <span className="font-mono font-bold text-white">{s.density_percentage}%</span>
                </div>
                <div className="w-full h-2 bg-slate-900 rounded-full overflow-hidden">
                  <div
                    className={`h-full transition-all duration-500 ${
                      isCritical ? "bg-rose-500" : isModerate ? "bg-amber-500" : "bg-emerald-500"
                    }`}
                    style={{ width: `${s.density_percentage}%` }}
                  ></div>
                </div>
              </div>

              {/* Inflow vs Outflow Rates */}
              <div className="grid grid-cols-2 gap-2 text-xs pt-1">
                <div className="flex items-center gap-1.5 p-2 bg-slate-900/60 rounded-lg">
                  <ArrowUpRight className="w-3.5 h-3.5 text-emerald-400" />
                  <div>
                    <div className="text-[10px] text-slate-400">Inflow</div>
                    <div className="font-bold text-white font-mono">{s.inflow_rate_ppm} ppm</div>
                  </div>
                </div>

                <div className="flex items-center gap-1.5 p-2 bg-slate-900/60 rounded-lg">
                  <ArrowDownRight className="w-3.5 h-3.5 text-rose-400" />
                  <div>
                    <div className="text-[10px] text-slate-400">Outflow</div>
                    <div className="font-bold text-white font-mono">{s.outflow_rate_ppm} ppm</div>
                  </div>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
