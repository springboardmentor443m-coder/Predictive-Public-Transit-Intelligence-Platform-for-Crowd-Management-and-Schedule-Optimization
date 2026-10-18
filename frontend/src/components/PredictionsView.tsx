import React, { useEffect, useState } from 'react';
import { Cpu, Clock, TrendingUp, AlertCircle, ArrowUpRight, CheckCircle2, ShieldCheck, Zap } from 'lucide-react';
import { ResponsiveContainer, LineChart, Line, XAxis, YAxis, Tooltip, Legend } from 'recharts';
import { api } from '../services/api';
import { HorizonPrediction } from '../types';

interface PredictionsViewProps {
  onSelectStation: (stationId: string) => void;
  activeHorizon: number;
  setActiveHorizon: (h: number) => void;
}

export const PredictionsView: React.FC<PredictionsViewProps> = ({
  onSelectStation,
  activeHorizon,
  setActiveHorizon
}) => {
  const [horizonData, setHorizonData] = useState<any>(null);
  const [recommendations, setRecommendations] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [multiStationCurves, setMultiStationCurves] = useState<any[]>([]);

  // Default to 15m if at 0m when entering prediction tab
  const currentHorizon = activeHorizon === 0 ? 15 : activeHorizon;

  useEffect(() => {
    setLoading(true);
    Promise.all([
      api.getNetworkHorizonPredictions(currentHorizon),
      api.getSmartRecommendations(),
      // Sample multi-horizon curves for key major interchange hubs
      api.getStationMultiHorizon('NYC-TSQ42'),
      api.getStationMultiHorizon('NYC-GCT42'),
      api.getStationMultiHorizon('NYC-PENN34'),
      api.getStationMultiHorizon('NYC-UNSQ14')
    ])
      .then(([hData, recs, tsq, gct, penn, unsq]) => {
        setHorizonData(hData);
        setRecommendations(recs);

        // Build comparison curve over horizons
        const curvePoints = [0, 15, 30, 60, 120].map((mins, idx) => ({
          horizon: mins === 0 ? 'Live' : `+${mins}m`,
          'Times Sq (1/2/3/7/N)': tsq.horizons[idx]?.predicted_density_percent || 0,
          'Grand Central (4/5/6/7)': gct.horizons[idx]?.predicted_density_percent || 0,
          'Penn Station (1/2/3/A)': penn.horizons[idx]?.predicted_density_percent || 0,
          'Union Square (4/5/6/L/N)': unsq.horizons[idx]?.predicted_density_percent || 0
        }));
        setMultiStationCurves(curvePoints);
        setLoading(false);
      })
      .catch(err => {
        console.error('Failed to load predictions', err);
        setLoading(false);
      });
  }, [currentHorizon]);

  return (
    <div className="space-y-6">
      {/* Header Banner */}
      <div className="bg-gradient-to-r from-slate-900 via-blue-950/40 to-slate-900 border border-blue-900/40 p-6 rounded-2xl flex flex-col md:flex-row items-start md:items-center justify-between gap-4 shadow-xl">
        <div className="flex items-center space-x-3.5">
          <div className="p-3 bg-blue-600/20 text-blue-400 rounded-2xl border border-blue-500/30">
            <Cpu className="w-7 h-7" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <h2 className="text-xl font-black text-white">AI Passenger Demand & Crowd Prediction</h2>
              <span className="text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded bg-blue-500/20 text-cyan-300 border border-blue-500/30">
                Multi-Horizon Forecasting
              </span>
            </div>
            <p className="text-xs text-slate-400 mt-1">
              Anticipate station congestion, passenger surges, and headway adjustments across +15m, +30m, +1h, and +2h horizons.
            </p>
          </div>
        </div>

        {/* Horizon Picker */}
        <div className="flex items-center bg-slate-950 p-1.5 rounded-xl border border-slate-800 shadow-inner">
          {[15, 30, 60, 120].map(h => (
            <button
              key={h}
              onClick={() => setActiveHorizon(h)}
              className={`px-3.5 py-1.5 rounded-lg text-xs font-bold transition cursor-pointer ${
                currentHorizon === h
                  ? 'bg-blue-600 text-white shadow-md shadow-blue-600/30'
                  : 'text-slate-400 hover:text-white hover:bg-slate-900'
              }`}
            >
              +{h >= 60 ? `${h / 60} Hour` : `${h} Min`}
            </button>
          ))}
        </div>
      </div>

      {loading ? (
        <div className="p-16 text-center text-slate-400 animate-pulse">
          Generating multi-horizon predictions and calculating headway recommendations...
        </div>
      ) : (
        <>
          {/* Top Predictive Risk Directives */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {recommendations?.recommendations?.map((item: any, idx: number) => (
              <div
                key={idx}
                className="bg-slate-900 border border-slate-800 hover:border-blue-500/40 p-4 rounded-2xl transition space-y-3 shadow-md flex flex-col justify-between"
              >
                <div>
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-sm text-white">{item.station_name}</span>
                    <span className="text-[10px] font-bold uppercase px-2 py-0.5 rounded bg-orange-500/20 text-orange-400 border border-orange-500/30">
                      {item.risk_level}
                    </span>
                  </div>
                  <div className="text-[11px] text-slate-400 mt-0.5">{item.borough} Corridor</div>

                  <div className="mt-3 p-2.5 bg-slate-950 rounded-xl border border-slate-800 flex items-center justify-between">
                    <div>
                      <div className="text-[10px] text-slate-400">Live Density</div>
                      <div className="text-sm font-bold text-slate-300">{item.current_density}%</div>
                    </div>
                    <div className="text-center font-bold text-blue-400">&rarr;</div>
                    <div className="text-right">
                      <div className="text-[10px] text-cyan-400 font-semibold">+15m Projected</div>
                      <div className="text-sm font-black text-cyan-400">{item.projected_density_15m}%</div>
                    </div>
                  </div>

                  <div className="mt-3 text-xs space-y-1">
                    <div className="text-[10px] font-bold uppercase text-slate-400 tracking-wider">
                      Recommended Headway
                    </div>
                    <div className="text-sm font-black text-emerald-400 flex items-center space-x-1">
                      <Zap className="w-3.5 h-3.5" />
                      <span>{item.recommended_headway} minutes / train</span>
                    </div>
                  </div>
                </div>

                <div className="pt-2 border-t border-slate-800 text-[11px] text-slate-300">
                  <div className="text-slate-400 mb-1">Directives:</div>
                  <div className="line-clamp-2 text-slate-300">{item.recommended_actions[0]}</div>
                  <button
                    onClick={() => onSelectStation(item.station_id)}
                    className="w-full mt-2.5 py-1.5 bg-slate-800 hover:bg-slate-700 text-blue-400 rounded-lg text-xs font-semibold transition cursor-pointer text-center"
                  >
                    Examine Station AI Profile &rarr;
                  </button>
                </div>
              </div>
            ))}
          </div>

          {/* Multi-Horizon Density Forecast Curves Chart */}
          <div className="bg-slate-900 border border-slate-800 p-6 rounded-2xl shadow-xl">
            <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between mb-6 gap-2">
              <div>
                <h3 className="text-base font-bold text-white flex items-center space-x-2">
                  <TrendingUp className="w-5 h-5 text-blue-400" />
                  <span>Key Transit Interchanges: Multi-Horizon Progression</span>
                </h3>
                <p className="text-xs text-slate-400 mt-0.5">
                  Simulated passenger load trajectories across Live, +15m, +30m, +1h, and +2h horizons
                </p>
              </div>
              <span className="text-xs px-2.5 py-1 rounded-lg bg-blue-500/10 text-blue-400 border border-blue-500/20 font-mono">
                Multi-Horizon Gradient Boost
              </span>
            </div>

            <div className="h-72 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={multiStationCurves}>
                  <XAxis dataKey="horizon" stroke="#64748b" fontSize={12} tickLine={false} />
                  <YAxis domain={[0, 100]} stroke="#64748b" fontSize={12} tickLine={false} unit="%" />
                  <Tooltip
                    contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '12px' }}
                    labelStyle={{ color: '#cbd5e1', fontWeight: 'bold' }}
                  />
                  <Legend wrapperStyle={{ paddingTop: '10px' }} />
                  <Line type="monotone" dataKey="Times Sq (1/2/3/7/N)" stroke="#EE352E" strokeWidth={3} dot={{ r: 4 }} activeDot={{ r: 6 }} />
                  <Line type="monotone" dataKey="Grand Central (4/5/6/7)" stroke="#00933C" strokeWidth={3} dot={{ r: 4 }} activeDot={{ r: 6 }} />
                  <Line type="monotone" dataKey="Penn Station (1/2/3/A)" stroke="#0039A6" strokeWidth={3} dot={{ r: 4 }} activeDot={{ r: 6 }} />
                  <Line type="monotone" dataKey="Union Square (4/5/6/L/N)" stroke="#FCCC0A" strokeWidth={3} dot={{ r: 4 }} activeDot={{ r: 6 }} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Full Network Predicted Stations Table for target horizon */}
          <div className="bg-slate-900 border border-slate-800 rounded-2xl overflow-hidden shadow-xl">
            <div className="p-5 border-b border-slate-800 flex items-center justify-between">
              <div>
                <h3 className="text-sm font-bold text-white">
                  Network Forecast at Horizon: +{currentHorizon >= 60 ? `${currentHorizon / 60} Hour` : `${currentHorizon} Minutes`}
                </h3>
                <p className="text-xs text-slate-400 mt-0.5">
                  Station-by-station predicted density and automated train headway assignments
                </p>
              </div>
              <div className="text-xs text-slate-300">
                Avg Density: <strong className="text-cyan-400">{horizonData?.average_network_density}%</strong>
              </div>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs text-slate-300">
                <thead className="bg-slate-950/70 text-slate-400 uppercase font-bold text-[10px] tracking-wider border-b border-slate-800">
                  <tr>
                    <th className="py-3 px-4">Station</th>
                    <th className="py-3 px-4">Borough</th>
                    <th className="py-3 px-4">Connecting Lines</th>
                    <th className="py-3 px-4 text-center">Predicted Density</th>
                    <th className="py-3 px-4 text-center">Estimated Volume</th>
                    <th className="py-3 px-4 text-center">Congestion Class</th>
                    <th className="py-3 px-4 text-center">Rec. Headway</th>
                    <th className="py-3 px-4 text-right">Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60 font-medium">
                  {horizonData?.stations?.map((s: HorizonPrediction) => (
                    <tr key={s.station_id} className="hover:bg-slate-800/40 transition">
                      <td className="py-3 px-4 font-bold text-white">{s.station_name}</td>
                      <td className="py-3 px-4 text-slate-400">{s.borough}</td>
                      <td className="py-3 px-4 font-mono text-slate-200">{s.lines?.join(', ')}</td>
                      <td className="py-3 px-4 text-center">
                        <span className="font-black text-sm" style={{ color: s.risk_color }}>
                          {s.predicted_density_percent}%
                        </span>
                      </td>
                      <td className="py-3 px-4 text-center">
                        {s.estimated_passenger_count.toLocaleString()} pass.
                      </td>
                      <td className="py-3 px-4 text-center">
                        <span
                          className="px-2 py-0.5 rounded text-[10px] font-bold uppercase"
                          style={{ backgroundColor: `${s.risk_color}25`, color: s.risk_color }}
                        >
                          {s.congestion_level}
                        </span>
                      </td>
                      <td className="py-3 px-4 text-center font-bold text-emerald-400">
                        {s.recommended_headway_mins} min
                      </td>
                      <td className="py-3 px-4 text-right">
                        <button
                          onClick={() => onSelectStation(s.station_id)}
                          className="px-3 py-1 bg-blue-600/20 hover:bg-blue-600/30 text-blue-400 hover:text-blue-300 rounded-lg text-xs font-semibold transition cursor-pointer"
                        >
                          Deep Dive
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </>
      )}
    </div>
  );
};
