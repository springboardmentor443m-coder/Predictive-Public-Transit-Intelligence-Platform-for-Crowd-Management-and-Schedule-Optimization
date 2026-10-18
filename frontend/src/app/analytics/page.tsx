"use client";

import { useEffect, useState } from "react";
import { BarChart3, Download, Clock, TrendingUp, Users, ShieldCheck, RefreshCw } from "lucide-react";
import {
  AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, Legend
} from "recharts";
import { api } from "@/lib/api";
import { AnalyticsSummary } from "@/types";

export default function AnalyticsPage() {
  const [summary, setSummary] = useState<AnalyticsSummary | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        const data = await api.getAnalyticsSummary();
        setSummary(data);
      } catch (e) {
        console.error(e);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  if (loading || !summary) {
    return (
      <div className="h-[75vh] flex flex-col items-center justify-center space-y-3">
        <RefreshCw className="w-8 h-8 text-blue-500 animate-spin" />
        <div className="text-sm font-semibold text-slate-400">Compiling Analytics & OTP Reports...</div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800 pb-4">
        <div>
          <h1 className="text-2xl font-black text-white flex items-center gap-2">
            <BarChart3 className="w-6 h-6 text-blue-400" />
            Analytics & Operations Performance Reports
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Historical passenger throughput trends, peak-hour bottleneck identification, and OTP audit reports
          </p>
        </div>

        <a
          href={api.getExportCsvUrl()}
          download="metroflow_performance_report.csv"
          className="flex items-center gap-2 px-4 py-2.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-xs transition shadow-lg shadow-emerald-600/25"
        >
          <Download className="w-4 h-4" />
          Export Operations CSV Report
        </a>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-[#0d1424] border border-slate-800 p-4 rounded-xl space-y-1">
          <div className="text-xs text-slate-400 font-semibold uppercase">Total Daily Ridership</div>
          <div className="text-2xl font-black text-white font-mono">
            {summary.total_daily_passengers.toLocaleString()}
          </div>
          <div className="text-[11px] text-emerald-400">+12.4% vs last week</div>
        </div>

        <div className="bg-[#0d1424] border border-slate-800 p-4 rounded-xl space-y-1">
          <div className="text-xs text-slate-400 font-semibold uppercase">On-Time Performance (OTP)</div>
          <div className="text-2xl font-black text-emerald-400 font-mono">
            {summary.overall_otp_percentage}%
          </div>
          <div className="text-[11px] text-slate-400">Target: &gt;95.0%</div>
        </div>

        <div className="bg-[#0d1424] border border-slate-800 p-4 rounded-xl space-y-1">
          <div className="text-xs text-slate-400 font-semibold uppercase">Peak Rush Hour</div>
          <div className="text-xl font-black text-amber-400 font-mono">
            {summary.peak_rush_hour}
          </div>
          <div className="text-[11px] text-slate-400">Highest Inflow Window</div>
        </div>

        <div className="bg-[#0d1424] border border-slate-800 p-4 rounded-xl space-y-1">
          <div className="text-xs text-slate-400 font-semibold uppercase">Incidents Logged Today</div>
          <div className="text-2xl font-black text-rose-400 font-mono">
            {summary.critical_incidents_today}
          </div>
          <div className="text-[11px] text-slate-400">All Resolved</div>
        </div>
      </div>

      {/* Historical Throughput Chart */}
      <div className="bg-[#0d1424] border border-slate-800 rounded-xl p-5 space-y-4">
        <h3 className="text-sm font-bold text-white flex items-center justify-between border-b border-slate-800 pb-3">
          <span>Hourly Passenger Footfall Throughput Curve</span>
          <span className="text-xs text-slate-400 font-mono">24-Hour Operations Cycle</span>
        </h3>

        <div className="w-full h-[320px]">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={summary.ridership_trends} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
              <defs>
                <linearGradient id="colorInflow" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.8} />
                  <stop offset="95%" stopColor="#3b82f6" stopOpacity={0.0} />
                </linearGradient>
                <linearGradient id="colorOutflow" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#10b981" stopOpacity={0.8} />
                  <stop offset="95%" stopColor="#10b981" stopOpacity={0.0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
              <XAxis dataKey="time_label" stroke="#94a3b8" fontSize={11} />
              <YAxis stroke="#94a3b8" fontSize={11} />
              <Tooltip
                contentStyle={{ backgroundColor: "#0f172a", borderColor: "#334155", borderRadius: "8px", color: "#fff", fontSize: "12px" }}
              />
              <Legend wrapperStyle={{ fontSize: "12px", color: "#cbd5e1" }} />
              <Area type="monotone" dataKey="total_inflow" name="Total Inflow Passengers" stroke="#3b82f6" fillOpacity={1} fill="url(#colorInflow)" />
              <Area type="monotone" dataKey="total_outflow" name="Total Outflow Passengers" stroke="#10b981" fillOpacity={1} fill="url(#colorOutflow)" />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Line Performance Audit Table */}
      <div className="bg-[#0d1424] border border-slate-800 rounded-xl p-5 space-y-4">
        <h3 className="text-sm font-bold text-white border-b border-slate-800 pb-3">
          Transit Corridor Performance Breakdown
        </h3>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="text-slate-400 uppercase bg-slate-900/80 border-b border-slate-800">
              <tr>
                <th className="p-3">Transit Line</th>
                <th className="p-3">Active Fleet</th>
                <th className="p-3">OTP (%)</th>
                <th className="p-3">Avg Delay (min)</th>
                <th className="p-3">Daily Ridership</th>
                <th className="p-3">Peak Bottleneck Node</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 font-mono">
              {summary.line_performances.map((line, idx) => (
                <tr key={idx} className="hover:bg-slate-900/40">
                  <td className="p-3 font-bold text-white font-sans">{line.line_name}</td>
                  <td className="p-3 text-blue-400">{line.active_trains} trains</td>
                  <td className="p-3 text-emerald-400 font-bold">{line.on_time_performance_pct}%</td>
                  <td className="p-3 text-slate-300">{line.avg_delay_minutes}m</td>
                  <td className="p-3 text-white">{line.total_daily_ridership.toLocaleString()}</td>
                  <td className="p-3 text-amber-400 font-sans">{line.peak_crowd_station}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
