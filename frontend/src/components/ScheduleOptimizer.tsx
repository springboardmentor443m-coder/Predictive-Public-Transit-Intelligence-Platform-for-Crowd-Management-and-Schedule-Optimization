import React, { useEffect, useState } from 'react';
import { 
  Zap, 
  Clock, 
  TrendingUp, 
  CheckCircle, 
  AlertTriangle,
  Play,
  RotateCcw
} from 'lucide-react';

interface ForecastTrend {
  time: string;
  predicted_passengers: number;
}

interface CorridorForecast {
  id: string;
  name: string;
  current_headway_min: number;
  recommended_headway_min: number;
  predicted_peak_inflow: number;
  surge_risk_score: number;
  status: 'ACTION_REQUIRED' | 'OPTIMAL';
  trend: ForecastTrend[];
}

export const ScheduleOptimizer: React.FC = () => {
  const [corridors, setCorridors] = useState<CorridorForecast[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeDispatching, setActiveDispatching] = useState<string | null>(null);
  const [notification, setNotification] = useState<string | null>(null);

  const fetchForecasts = async () => {
    try {
      const res = await fetch('http://localhost:8000/api/schedule/forecasts');
      if (res.ok) {
        const json = await res.json();
        setCorridors(json.corridors || []);
      }
    } catch (err) {
      console.error('Forecast fetch error:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchForecasts();
  }, []);

  const handleDispatch = async (corridor: CorridorForecast) => {
    setActiveDispatching(corridor.id);
    try {
      const res = await fetch('http://localhost:8000/api/schedule/dispatch', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          corridor_id: corridor.id,
          action_type: 'HEADWAY_ADJUSTMENT',
          target_headway_min: corridor.recommended_headway_min
        })
      });

      if (res.ok) {
        const data = await res.json();
        setNotification(`Dispatched schedule update for ${corridor.name}`);
        setCorridors(prev =>
          prev.map(c =>
            c.id === corridor.id
              ? { ...c, current_headway_min: c.recommended_headway_min, status: 'OPTIMAL', surge_risk_score: Math.max(20, c.surge_risk_score - 40) }
              : c
          )
        );
        setTimeout(() => setNotification(null), 4000);
      }
    } catch (err) {
      console.error('Dispatch error:', err);
    } finally {
      setActiveDispatching(null);
    }
  };

  if (loading) {
    return null;
  }

  return (
    <div className="w-full bg-slate-900/40 border border-slate-800/80 rounded-2xl p-6 backdrop-blur-md">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-5 border-b border-slate-800/80 mb-6">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <Zap className="w-4 h-4 text-amber-400" />
            <h2 className="text-sm font-bold tracking-wider uppercase text-slate-100">
              Predictive Scheduling & Fleet Dispatch
            </h2>
          </div>
          <p className="text-xs text-slate-400">
            60-minute passenger surge forecasting and automated headway recommendations
          </p>
        </div>

        {notification && (
          <div className="px-3.5 py-1.5 bg-emerald-500/20 border border-emerald-500/40 rounded-xl text-emerald-400 text-xs font-mono flex items-center gap-2">
            <CheckCircle className="w-4 h-4" />
            {notification}
          </div>
        )}
      </div>

      {/* Corridors Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
        {corridors.map((c) => (
          <div
            key={c.id}
            className={`p-5 rounded-2xl border bg-slate-950/80 backdrop-blur-md flex flex-col justify-between ${
              c.status === 'ACTION_REQUIRED'
                ? 'border-amber-500/40 shadow-[0_0_20px_rgba(245,158,11,0.08)]'
                : 'border-slate-800/80'
            }`}
          >
            <div>
              <div className="flex items-center justify-between mb-3">
                <span className="text-xs font-bold text-slate-200">{c.name}</span>
                <span className={`text-[10px] font-mono px-2 py-0.5 rounded-full font-bold ${
                  c.status === 'ACTION_REQUIRED'
                    ? 'bg-amber-500/20 text-amber-400 border border-amber-500/30'
                    : 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                }`}>
                  {c.status === 'ACTION_REQUIRED' ? 'ACTION NEEDED' : 'BALANCED'}
                </span>
              </div>

              {/* Headway Comparison */}
              <div className="grid grid-cols-2 gap-2 text-xs font-mono p-3 bg-slate-900/50 rounded-xl border border-slate-800/60 mb-4">
                <div>
                  <span className="text-[10px] text-slate-500 block">CURRENT HEADWAY</span>
                  <span className="text-slate-200 font-bold text-sm mt-0.5 flex items-center gap-1">
                    <Clock className="w-3.5 h-3.5 text-slate-400" />
                    {c.current_headway_min}m
                  </span>
                </div>
                <div>
                  <span className="text-[10px] text-slate-500 block">RECOMMENDED</span>
                  <span className={`font-bold text-sm mt-0.5 flex items-center gap-1 ${
                    c.current_headway_min !== c.recommended_headway_min ? 'text-amber-400' : 'text-emerald-400'
                  }`}>
                    <Zap className="w-3.5 h-3.5" />
                    {c.recommended_headway_min}m
                  </span>
                </div>
              </div>

              {/* Forecast Sparkline Trend */}
              <div className="mb-4">
                <div className="flex justify-between text-[11px] font-mono text-slate-400 mb-1.5">
                  <span className="flex items-center gap-1">
                    <TrendingUp className="w-3 h-3 text-cyan-400" /> +60m Surge Trend
                  </span>
                  <span className="text-slate-300 font-bold">Peak: {c.predicted_peak_inflow}/m</span>
                </div>
                <div className="grid grid-cols-4 gap-1.5 h-10 items-end bg-slate-900/40 p-1.5 rounded-lg border border-slate-800/40">
                  {c.trend.map((pt, idx) => {
                    const heightPct = Math.min(100, Math.round((pt.predicted_passengers / 450) * 100));
                    return (
                      <div key={idx} className="flex flex-col items-center h-full justify-end">
                        <div
                          className={`w-full rounded-sm transition-all ${
                            c.status === 'ACTION_REQUIRED' ? 'bg-amber-500/80' : 'bg-cyan-500/60'
                          }`}
                          style={{ height: `${heightPct}%` }}
                        />
                        <span className="text-[9px] font-mono text-slate-500 mt-1">{pt.time}</span>
                      </div>
                    );
                  })}
                </div>
              </div>
            </div>

            {/* Action Dispatch Button */}
            <button
              onClick={() => handleDispatch(c)}
              disabled={activeDispatching === c.id || c.status === 'OPTIMAL'}
              className={`w-full py-2 px-3 rounded-xl text-xs font-mono font-bold flex items-center justify-center gap-2 transition ${
                c.status === 'ACTION_REQUIRED'
                  ? 'bg-amber-500/20 text-amber-300 border border-amber-500/40 hover:bg-amber-500/30'
                  : 'bg-slate-900 text-slate-500 border border-slate-800 cursor-not-allowed'
              }`}
            >
              <Play className="w-3.5 h-3.5" />
              {activeDispatching === c.id ? 'DISPATCHING...' : c.status === 'ACTION_REQUIRED' ? 'DISPATCH FLEET ADJUSTMENT' : 'HEADWAY BALANCED'}
            </button>
          </div>
        ))}
      </div>
    </div>
  );
};