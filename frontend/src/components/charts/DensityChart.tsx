"use client";

import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, Legend, Cell
} from "recharts";
import { StationDensity } from "@/types";

interface DensityChartProps {
  stations: StationDensity[];
}

export function DensityChart({ stations }: DensityChartProps) {
  const chartData = stations.slice(0, 10).map((s) => ({
    name: s.station_name.split(" ")[0],
    inflow: s.inflow_rate_ppm,
    outflow: s.outflow_rate_ppm,
    density: s.density_percentage,
    status: s.status,
  }));

  return (
    <div className="w-full h-[320px] bg-[#0d1424] border border-slate-800 rounded-xl p-4 flex flex-col justify-between">
      <div className="flex items-center justify-between mb-2">
        <h4 className="text-sm font-bold text-white">Live Station Inflow vs. Outflow (Passengers / Min)</h4>
        <span className="text-xs text-slate-400 font-mono">Top 10 High-Traffic Nodes</span>
      </div>

      <div className="flex-1 w-full min-h-[220px]">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={chartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
            <XAxis dataKey="name" stroke="#94a3b8" fontSize={11} />
            <YAxis stroke="#94a3b8" fontSize={11} />
            <Tooltip
              contentStyle={{ backgroundColor: "#0f172a", borderColor: "#334155", borderRadius: "8px", color: "#fff", fontSize: "12px" }}
            />
            <Legend wrapperStyle={{ fontSize: "12px", color: "#cbd5e1" }} />
            <Bar dataKey="inflow" name="Inflow Rate (ppm)" fill="#3b82f6" radius={[4, 4, 0, 0]} />
            <Bar dataKey="outflow" name="Outflow Rate (ppm)" fill="#10b981" radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
