"use client";

import { useEffect, useState } from "react";
import { BrainCircuit, Sparkles, CheckCircle, AlertTriangle, ArrowRight, RefreshCw } from "lucide-react";
import { api } from "@/lib/api";
import { StationForecast, FrequencyRecommendation } from "@/types";
import { ForecastChart } from "@/components/charts/ForecastChart";

export default function PredictionsPage() {
  const [forecasts, setForecasts] = useState<StationForecast[]>([]);
  const [optimizations, setOptimizations] = useState<FrequencyRecommendation[]>([]);
  const [selectedStationId, setSelectedStationId] = useState<number>(1);
  const [horizon, setHorizon] = useState<number>(30);
  const [appliedRecommendations, setAppliedRecommendations] = useState<Record<string, boolean>>({});
  const [loading, setLoading] = useState(true);

  const loadData = async () => {
    try {
      const fcData = await api.getAllForecasts(horizon);
      const optData = await api.getOptimizations();
      setForecasts(fcData);
      setOptimizations(optData);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [horizon]);

  const activeForecast = forecasts.find((f) => f.station_id === selectedStationId) || forecasts[0];

  const handleApplyOptimization = (rec: FrequencyRecommendation) => {
    setAppliedRecommendations((prev) => ({ ...prev, [rec.segment_name]: true }));
  };

  if (loading || !activeForecast) {
    return (
      <div className="h-[75vh] flex flex-col items-center justify-center space-y-3">
        <RefreshCw className="w-8 h-8 text-blue-500 animate-spin" />
        <div className="text-sm font-semibold text-slate-400">Executing XGBoost AI Demand Inferences...</div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800 pb-4">
        <div>
          <h1 className="text-2xl font-black text-white flex items-center gap-2">
            <BrainCircuit className="w-6 h-6 text-blue-400" />
            AI Demand Forecasting & Predictive Insights
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Short-term station passenger forecaster & automated train frequency tuning engine
          </p>
        </div>

        {/* Horizon selector */}
        <div className="flex items-center gap-2 bg-[#0d1424] border border-slate-800 p-1.5 rounded-lg text-xs font-semibold">
          <span className="text-slate-400 px-2 uppercase text-[10px]">Forecast Horizon:</span>
          {[15, 30, 60].map((h) => (
            <button
              key={h}
              onClick={() => setHorizon(h)}
              className={`px-3 py-1 rounded transition ${
                horizon === h
                  ? "bg-blue-600 text-white shadow"
                  : "text-slate-400 hover:text-white"
              }`}
            >
              {h} mins
            </button>
          ))}
        </div>
      </div>

      {/* Main Content Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Forecast Chart & Station Selector */}
        <div className="lg:col-span-2 space-y-4">
          {/* Station selector dropdown */}
          <div className="flex items-center justify-between bg-[#0d1424] border border-slate-800 p-3 rounded-xl">
            <label className="text-xs font-bold text-slate-300 uppercase">
              Select Target Station:
            </label>
            <select
              value={selectedStationId}
              onChange={(e) => setSelectedStationId(Number(e.target.value))}
              className="bg-slate-900 border border-slate-700 text-white text-xs rounded-lg px-3 py-1.5 focus:outline-none focus:border-blue-500 font-semibold"
            >
              {forecasts.map((f) => (
                <option key={f.station_id} value={f.station_id}>
                  {f.station_name} ({f.line_name})
                </option>
              ))}
            </select>
          </div>

          <ForecastChart forecast={activeForecast} />
        </div>

        {/* AI Recommendations Sidebar Panel */}
        <div className="space-y-4">
          <div className="bg-[#0d1424] border border-slate-800 p-5 rounded-xl space-y-4">
            <h3 className="text-sm font-bold text-white flex items-center gap-2 border-b border-slate-800 pb-3">
              <Sparkles className="w-4 h-4 text-amber-400" />
              Automated Frequency Tuning
            </h3>

            <div className="space-y-3">
              {optimizations.map((rec, idx) => {
                const isApplied = appliedRecommendations[rec.segment_name];

                return (
                  <div
                    key={idx}
                    className="p-3.5 bg-slate-900/80 border border-slate-800 rounded-xl space-y-2.5 text-xs"
                  >
                    <div className="flex items-start justify-between">
                      <div>
                        <div className="font-bold text-white">{rec.line_name}</div>
                        <div className="text-[11px] text-slate-400">{rec.segment_name}</div>
                      </div>
                      <span className="px-2 py-0.5 rounded bg-blue-500/20 text-blue-400 border border-blue-500/30 text-[10px] font-mono">
                        +{rec.additional_trains_needed} trains/hr
                      </span>
                    </div>

                    <p className="text-slate-300 leading-relaxed text-[11px]">
                      {rec.reason}
                    </p>

                    <div className="flex items-center justify-between text-[11px] pt-1">
                      <div className="text-slate-400">
                        Headway: <span className="text-white font-mono">{rec.current_headway_minutes}m</span> → <span className="text-emerald-400 font-bold font-mono">{rec.recommended_headway_minutes}m</span>
                      </div>

                      <button
                        onClick={() => handleApplyOptimization(rec)}
                        disabled={isApplied}
                        className={`px-3 py-1.5 rounded-lg text-xs font-bold transition flex items-center gap-1.5 ${
                          isApplied
                            ? "bg-emerald-500/20 text-emerald-400 border border-emerald-500/30"
                            : "bg-blue-600 hover:bg-blue-500 text-white shadow-lg shadow-blue-600/20"
                        }`}
                      >
                        {isApplied ? (
                          <>
                            <CheckCircle className="w-3.5 h-3.5" />
                            Applied
                          </>
                        ) : (
                          <>
                            Apply Optimization
                            <ArrowRight className="w-3.5 h-3.5" />
                          </>
                        )}
                      </button>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
