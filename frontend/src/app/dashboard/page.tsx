"use client";

import { useEffect, useState } from "react";
import { Train, Users, AlertTriangle, Clock, RefreshCw, Zap } from "lucide-react";
import { api } from "@/lib/api";
import { StationDensity, CrowdSummary } from "@/types";
import { MetroMap } from "@/components/maps/MetroMap";
import { DensityChart } from "@/components/charts/DensityChart";
import { socketClient } from "@/lib/socket";

export default function DashboardPage() {
  const [summary, setSummary] = useState<CrowdSummary | null>(null);
  const [selectedStation, setSelectedStation] = useState<StationDensity | null>(null);
  const [loading, setLoading] = useState(true);

  const loadData = async () => {
    try {
      const data = await api.getCrowdSummary();
      setSummary(data);
      if (data.stations.length > 0 && !selectedStation) {
        setSelectedStation(data.stations[0]);
      }
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
    const unsubscribe = socketClient.subscribe((msg) => {
      if (msg.event === "TELEMETRY_UPDATE" && msg.summary) {
        setSummary(msg.summary);
      }
    });
    return () => unsubscribe();
  }, []);

  if (loading || !summary) {
    return (
      <div className="h-[75vh] flex flex-col items-center justify-center space-y-3">
        <RefreshCw className="w-8 h-8 text-blue-500 animate-spin" />
        <div className="text-sm font-semibold text-slate-400">Loading MetroFlow Executive Telemetry...</div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Executive Page Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800 pb-4">
        <div>
          <h1 className="text-2xl font-black text-white flex items-center gap-2">
            Executive Operations Overview
            <span className="text-xs px-2.5 py-0.5 rounded-full bg-blue-500/20 text-blue-400 border border-blue-500/30 uppercase font-mono">
              Live Feed
            </span>
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Real-time station crowd density monitoring, line telemetry, and automated system performance metrics
          </p>
        </div>

        <button
          onClick={loadData}
          className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-xs font-semibold text-slate-200 transition"
        >
          <RefreshCw className="w-3.5 h-3.5" />
          Refresh Stream
        </button>
      </div>

      {/* Top 4 KPI Metrics Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-[#0d1424] border border-slate-800 p-4 rounded-xl space-y-2">
          <div className="flex items-center justify-between text-xs text-slate-400 uppercase tracking-wider font-semibold">
            <span>System Passengers</span>
            <Users className="w-4 h-4 text-blue-400" />
          </div>
          <div className="text-2xl font-black text-white font-mono">
            {summary.total_system_occupancy.toLocaleString()}
          </div>
          <div className="text-[11px] text-emerald-400 font-medium">
            Avg Network Load: {summary.average_density_percentage}%
          </div>
        </div>

        <div className="bg-[#0d1424] border border-slate-800 p-4 rounded-xl space-y-2">
          <div className="flex items-center justify-between text-xs text-slate-400 uppercase tracking-wider font-semibold">
            <span>Active Trains</span>
            <Train className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="text-2xl font-black text-white font-mono">26</div>
          <div className="text-[11px] text-slate-400">
            Red Line: <span className="text-emerald-400 font-bold">14</span> | Blue Line: <span className="text-blue-400 font-bold">12</span>
          </div>
        </div>

        <div className="bg-[#0d1424] border border-slate-800 p-4 rounded-xl space-y-2">
          <div className="flex items-center justify-between text-xs text-slate-400 uppercase tracking-wider font-semibold">
            <span>Critical Stations</span>
            <AlertTriangle className="w-4 h-4 text-rose-400" />
          </div>
          <div className="text-2xl font-black text-rose-400 font-mono">
            {summary.critical_stations_count}
          </div>
          <div className="text-[11px] text-slate-400">
            Moderate: {summary.moderate_stations_count} | Normal: {summary.normal_stations_count}
          </div>
        </div>

        <div className="bg-[#0d1424] border border-slate-800 p-4 rounded-xl space-y-2">
          <div className="flex items-center justify-between text-xs text-slate-400 uppercase tracking-wider font-semibold">
            <span>On-Time Rate (OTP)</span>
            <Clock className="w-4 h-4 text-amber-400" />
          </div>
          <div className="text-2xl font-black text-white font-mono">95.1%</div>
          <div className="text-[11px] text-emerald-400 font-medium">
            +0.4% vs Daily Benchmark
          </div>
        </div>
      </div>

      {/* Main Interactive Map & Analytics Section */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-6">
          <MetroMap
            stations={summary.stations}
            onSelectStation={(st) => setSelectedStation(st)}
            selectedStationId={selectedStation?.station_id}
          />
          <DensityChart stations={summary.stations} />
        </div>

        {/* Selected Station Telemetry Panel */}
        <div className="space-y-4">
          <div className="bg-[#0d1424] border border-slate-800 p-5 rounded-xl space-y-4">
            <h3 className="text-sm font-bold text-white flex items-center justify-between border-b border-slate-800 pb-3">
              <span>Station Telemetry Panel</span>
              {selectedStation && (
                <span className={`text-[10px] px-2 py-0.5 rounded font-bold uppercase ${
                  selectedStation.status === "CRITICAL"
                    ? "bg-rose-500/20 text-rose-400 border border-rose-500/30"
                    : "bg-emerald-500/20 text-emerald-400 border border-emerald-500/30"
                }`}>
                  {selectedStation.status}
                </span>
              )}
            </h3>

            {selectedStation ? (
              <div className="space-y-4 text-xs">
                <div>
                  <div className="text-base font-extrabold text-white">{selectedStation.station_name}</div>
                  <div className="text-slate-400 font-mono">Code: {selectedStation.station_code} | {selectedStation.line_name}</div>
                </div>

                {/* Density Bar */}
                <div className="space-y-1.5">
                  <div className="flex justify-between text-slate-300">
                    <span>Platform Occupancy</span>
                    <span className="font-bold text-amber-400">{selectedStation.density_percentage}%</span>
                  </div>
                  <div className="w-full h-2 bg-slate-800 rounded-full overflow-hidden">
                    <div
                      className={`h-full transition-all duration-500 ${
                        selectedStation.density_percentage > 80
                          ? "bg-rose-500"
                          : selectedStation.density_percentage > 60
                          ? "bg-amber-500"
                          : "bg-emerald-500"
                      }`}
                      style={{ width: `${selectedStation.density_percentage}%` }}
                    ></div>
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-3 pt-2">
                  <div className="p-3 bg-slate-900/80 border border-slate-800 rounded-lg">
                    <div className="text-[10px] text-slate-400 uppercase">Inflow Rate</div>
                    <div className="text-base font-bold text-emerald-400 font-mono">
                      {selectedStation.inflow_rate_ppm} <span className="text-[10px] font-normal text-slate-400">ppm</span>
                    </div>
                  </div>
                  <div className="p-3 bg-slate-900/80 border border-slate-800 rounded-lg">
                    <div className="text-[10px] text-slate-400 uppercase">Outflow Rate</div>
                    <div className="text-base font-bold text-rose-400 font-mono">
                      {selectedStation.outflow_rate_ppm} <span className="text-[10px] font-normal text-slate-400">ppm</span>
                    </div>
                  </div>
                </div>

                <div className="p-3 bg-slate-900/80 border border-slate-800 rounded-lg space-y-1">
                  <div className="text-[10px] text-slate-400 uppercase">Platform Capacity Limit</div>
                  <div className="text-sm font-bold text-white font-mono">
                    {selectedStation.current_occupancy.toLocaleString()} / {selectedStation.platform_capacity.toLocaleString()} Max
                  </div>
                </div>
              </div>
            ) : (
              <div className="text-slate-500 text-center py-6 text-xs">
                Click a station node on the map to inspect live metrics.
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
