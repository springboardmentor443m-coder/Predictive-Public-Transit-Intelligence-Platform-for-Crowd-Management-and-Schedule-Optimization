"use client";

import {
  AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, Legend
} from "recharts";
import { StationForecast } from "@/types";

interface ForecastChartProps {
  forecast: StationForecast;
}

export function ForecastChart({ forecast }: ForecastChartProps) {
  const chartData = forecast.forecast_points.map((pt) => ({
    time: pt.timestamp,
    predicted_inflow: pt.predicted_inflow,
    lower_bound: pt.confidence_interval_lower,
    upper_bound: pt.confidence_interval_upper,
    surge_prob: Math.round(pt.surge_probability * 100),
  }));

  return (
    <div className="w-full h-[340px] bg-[#0d1424] border border-slate-800 rounded-xl p-4 flex flex-col justify-between">
      <div className="flex items-center justify-between mb-2">
        <div>
          <h4 className="text-sm font-bold text-white flex items-center gap-2">
            AI Demand Forecast Curve: <span className="text-blue-400 font-mono">{forecast.station_name}</span>
          </h4>
          <p className="text-xs text-slate-400">
            {forecast.forecast_horizon_minutes}-min Horizon Prediction with 95% Confidence Interval Bounds
          </p>
        </div>

        <div className="flex items-center gap-3 text-xs">
          <div className="px-2.5 py-1 rounded bg-slate-800 border border-slate-700 text-slate-300 font-mono">
            Surge Risk: <span className="text-amber-400 font-bold">{Math.round(forecast.surge_probability * 100)}%</span>
          </div>
          <div className={`px-2.5 py-1 rounded font-bold text-xs ${
            forecast.risk_level === "CRITICAL" || forecast.risk_level === "SEVERE"
              ? "bg-rose-500/20 text-rose-400 border border-rose-500/30"
              : "bg-emerald-500/20 text-emerald-400 border border-emerald-500/30"
          }`}>
            Risk: {forecast.risk_level}
          </div>
        </div>
      </div>

      <div className="flex-1 w-full min-h-[220px]">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={chartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
            <defs>
              <linearGradient id="colorPredicted" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.8} />
                <stop offset="95%" stopColor="#3b82f6" stopOpacity={0.0} />
              </linearGradient>
              <linearGradient id="colorUpper" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#6366f1" stopOpacity={0.3} />
                <stop offset="95%" stopColor="#6366f1" stopOpacity={0.0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
            <XAxis dataKey="time" stroke="#94a3b8" fontSize={11} />
            <YAxis stroke="#94a3b8" fontSize={11} />
            <Tooltip
              contentStyle={{ backgroundColor: "#0f172a", borderColor: "#334155", borderRadius: "8px", color: "#fff", fontSize: "12px" }}
            />
            <Legend wrapperStyle={{ fontSize: "12px", color: "#cbd5e1" }} />
            <Area type="monotone" dataKey="upper_bound" name="Upper Confidence Bound" stroke="#818cf8" fillOpacity={1} fill="url(#colorUpper)" />
            <Area type="monotone" dataKey="predicted_inflow" name="Predicted Inflow (ppm)" stroke="#3b82f6" strokeWidth={3} fillOpacity={1} fill="url(#colorPredicted)" />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
