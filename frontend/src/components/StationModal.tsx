import React, { useEffect, useState } from 'react';
import { X, TrendingUp, Users, ArrowUpRight, ArrowDownRight, Clock, ShieldAlert, Cpu } from 'lucide-react';
import { ResponsiveContainer, AreaChart, Area, XAxis, YAxis, Tooltip } from 'recharts';
import { api } from '../services/api';

interface StationModalProps {
  stationId: string | null;
  onClose: () => void;
}

export const StationModal: React.FC<StationModalProps> = ({ stationId, onClose }) => {
  const [details, setDetails] = useState<any>(null);
  const [forecast, setForecast] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!stationId) return;
    setLoading(true);

    Promise.all([
      api.getStationDetails(stationId),
      api.getStationMultiHorizon(stationId)
    ])
      .then(([det, fc]) => {
        setDetails(det);
        setForecast(fc);
        setLoading(false);
      })
      .catch(err => {
        console.error('Failed to load station details', err);
        setLoading(false);
      });
  }, [stationId]);

  if (!stationId) return null;

  return (
    <div className="fixed inset-0 z-[2000] flex items-center justify-center p-4 bg-black/75 backdrop-blur-sm animate-in fade-in duration-200">
      <div className="bg-slate-900 border border-slate-700/80 rounded-2xl w-full max-w-4xl max-h-[92vh] overflow-y-auto shadow-2xl flex flex-col text-slate-100">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-slate-800 bg-slate-900/60 sticky top-0 z-10 backdrop-blur-md">
          {loading ? (
            <div className="animate-pulse h-6 w-48 bg-slate-700 rounded"></div>
          ) : (
            <div>
              <div className="flex items-center space-x-3">
                <h2 className="text-xl font-bold text-white">{details?.station?.name}</h2>
                <span className={`px-2.5 py-0.5 rounded-full text-xs font-bold uppercase tracking-wider ${
                  details?.station?.density_percent >= 85 ? 'bg-red-500/20 text-red-400 border border-red-500/30' :
                  details?.station?.density_percent >= 70 ? 'bg-orange-500/20 text-orange-400 border border-orange-500/30' :
                  details?.station?.density_percent >= 45 ? 'bg-amber-500/20 text-amber-400 border border-amber-500/30' :
                  'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                }`}>
                  {details?.station?.congestion_level} Congestion
                </span>
              </div>
              <p className="text-xs text-slate-400 mt-1">
                {details?.station?.borough} &bull; {details?.station?.zone} &bull; Serving Lines: {details?.station?.lines.join(', ')}
              </p>
            </div>
          )}

          <button
            onClick={onClose}
            className="p-2 rounded-xl text-slate-400 hover:text-white hover:bg-slate-800 transition cursor-pointer"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content Body */}
        {loading ? (
          <div className="p-12 text-center text-slate-400 animate-pulse">
            Loading real-time station telemetry and AI demand forecasting...
          </div>
        ) : (
          <div className="p-6 space-y-6">
            {/* Quick Metrics Bar */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
              <div className="bg-slate-950/70 border border-slate-800 p-4 rounded-xl">
                <div className="flex items-center space-x-2 text-slate-400 text-xs mb-1">
                  <Users className="w-4 h-4 text-blue-400" />
                  <span>Platform Occupancy</span>
                </div>
                <div className="text-2xl font-black text-white">
                  {details.station.current_occupancy.toLocaleString()}
                </div>
                <div className="text-[11px] text-slate-400 mt-1">
                  Cap: {details.station.capacity.toLocaleString()} ({details.station.density_percent}%)
                </div>
                <div className="w-full bg-slate-800 h-1.5 rounded-full mt-2 overflow-hidden">
                  <div
                    className={`h-full rounded-full ${
                      details.station.density_percent >= 85 ? 'bg-red-500' :
                      details.station.density_percent >= 70 ? 'bg-orange-500' :
                      details.station.density_percent >= 45 ? 'bg-amber-500' :
                      'bg-emerald-500'
                    }`}
                    style={{ width: `${Math.min(100, details.station.density_percent)}%` }}
                  ></div>
                </div>
              </div>

              <div className="bg-slate-950/70 border border-slate-800 p-4 rounded-xl">
                <div className="flex items-center space-x-2 text-slate-400 text-xs mb-1">
                  <ArrowDownRight className="w-4 h-4 text-emerald-400" />
                  <span>Turnstile Inflow</span>
                </div>
                <div className="text-2xl font-black text-emerald-400">
                  {details.station.inflow_rate}
                </div>
                <div className="text-[11px] text-slate-400 mt-1">
                  passengers / min entry
                </div>
              </div>

              <div className="bg-slate-950/70 border border-slate-800 p-4 rounded-xl">
                <div className="flex items-center space-x-2 text-slate-400 text-xs mb-1">
                  <ArrowUpRight className="w-4 h-4 text-cyan-400" />
                  <span>Turnstile Outflow</span>
                </div>
                <div className="text-2xl font-black text-cyan-400">
                  {details.station.outflow_rate}
                </div>
                <div className="text-[11px] text-slate-400 mt-1">
                  passengers / min exit
                </div>
              </div>

              <div className="bg-slate-950/70 border border-slate-800 p-4 rounded-xl">
                <div className="flex items-center space-x-2 text-slate-400 text-xs mb-1">
                  <TrendingUp className="w-4 h-4 text-purple-400" />
                  <span>Flow Momentum</span>
                </div>
                <div className="text-2xl font-black text-purple-400 capitalize">
                  {details.station.trend}
                </div>
                <div className="text-[11px] text-slate-400 mt-1">
                  Active turnstiles: {details.station.turnstiles_active}/{details.station.turnstiles}
                </div>
              </div>
            </div>

            {/* 12-Minute Real-Time Flow Chart */}
            <div className="bg-slate-950/80 border border-slate-800 p-5 rounded-2xl">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-sm font-semibold text-slate-200 flex items-center space-x-2">
                  <Clock className="w-4 h-4 text-blue-400" />
                  <span>Recent Platform Density History (Past 12 Mins)</span>
                </h3>
                <span className="text-xs text-slate-400">1-min sensor interval</span>
              </div>
              <div className="h-44 w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={details.history}>
                    <defs>
                      <linearGradient id="densityGradient" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#3B82F6" stopOpacity={0.4}/>
                        <stop offset="95%" stopColor="#3B82F6" stopOpacity={0.0}/>
                      </linearGradient>
                    </defs>
                    <XAxis dataKey="time" stroke="#475569" fontSize={11} tickLine={false} />
                    <YAxis domain={[0, 100]} stroke="#475569" fontSize={11} tickLine={false} unit="%" />
                    <Tooltip
                      contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px' }}
                      labelStyle={{ color: '#94a3b8' }}
                    />
                    <Area type="monotone" dataKey="density" stroke="#3B82F6" strokeWidth={2} fillOpacity={1} fill="url(#densityGradient)" name="Density %" />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            </div>

            {/* Multi-Horizon AI Crowd Prediction (+15m, +30m, +1h, +2h) */}
            <div className="bg-gradient-to-br from-slate-950 to-slate-900 border border-blue-900/40 p-5 rounded-2xl">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center space-x-2.5">
                  <div className="p-2 bg-blue-600/20 text-blue-400 rounded-lg border border-blue-500/30">
                    <Cpu className="w-5 h-5" />
                  </div>
                  <div>
                    <h3 className="text-base font-bold text-white">Multi-Horizon Crowd Density Forecasting</h3>
                    <p className="text-xs text-slate-400">
                      Predictive demand projection for +15m, +30m, +1h, and +2h
                    </p>
                  </div>
                </div>
                <div className="text-right">
                  <span className="text-xs text-slate-400">Overall Trend:</span>
                  <span className="ml-1 text-xs font-bold text-cyan-400">{forecast?.overall_trend}</span>
                </div>
              </div>

              {/* Forecast Cards Grid */}
              <div className="grid grid-cols-2 sm:grid-cols-5 gap-3">
                {forecast?.horizons?.map((h: any, i: number) => (
                  <div
                    key={i}
                    className={`p-3.5 rounded-xl border transition ${
                      h.horizon_minutes === 0 ? 'bg-slate-900/90 border-slate-700' : 'bg-slate-950/80 border-slate-800 hover:border-blue-500/50'
                    }`}
                  >
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-xs font-bold text-white">{h.horizon_label}</span>
                      <span className="text-[10px] text-slate-400 font-mono">{h.predicted_timestamp}</span>
                    </div>

                    <div className="text-xl font-black mb-1" style={{ color: h.risk_color }}>
                      {h.predicted_density_percent}%
                    </div>

                    <div className="text-[11px] text-slate-300 font-medium">
                      {h.estimated_passenger_count.toLocaleString()} pass.
                    </div>

                    <div className="mt-2 pt-2 border-t border-slate-800 text-[10px] space-y-1">
                      <div className="flex justify-between">
                        <span className="text-slate-400">Status:</span>
                        <span className="font-semibold" style={{ color: h.risk_color }}>{h.congestion_level}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-slate-400">Headway:</span>
                        <span className="font-semibold text-cyan-400">{h.recommended_headway_mins}m</span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>

              {/* Station Smart Recommendations */}
              {forecast?.horizons?.[1]?.recommendations?.length > 0 && (
                <div className="mt-4 pt-4 border-t border-slate-800">
                  <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-2 flex items-center space-x-1.5">
                    <ShieldAlert className="w-3.5 h-3.5 text-amber-400" />
                    <span>Actionable Dispatch Directives</span>
                  </h4>
                  <ul className="space-y-1.5">
                    {forecast.horizons[1].recommendations.map((rec: string, idx: number) => (
                      <li key={idx} className="text-xs text-slate-300 flex items-start space-x-2">
                        <span className="text-blue-400 font-bold">&bull;</span>
                        <span>{rec}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
