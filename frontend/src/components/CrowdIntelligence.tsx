import React, { useEffect, useState } from 'react';
import { 
  Users, 
  ArrowUpRight, 
  ArrowDownRight, 
  TrendingUp, 
  Activity, 
  AlertCircle,
  Radio,
  Sliders
} from 'lucide-react';

interface CrowdStation {
  station_id: string;
  name: string;
  line: string;
  entry_turnstiles_active: number;
  exit_turnstiles_active: number;
  inflow_per_min: number;
  outflow_per_min: number;
  current_platform_load_pct: number;
  trend: 'SURGE' | 'INCREASING' | 'STABLE' | 'DECREASING';
  crowd_status: 'NORMAL' | 'ELEVATED' | 'CRITICAL';
}

interface CrowdPayload {
  timestamp: string;
  total_active_turnstiles: number;
  network_net_inflow_per_min: number;
  crowd_telemetry: CrowdStation[];
}

export const CrowdIntelligence: React.FC = () => {
  const [data, setData] = useState<CrowdPayload | null>(null);
  const [filter, setFilter] = useState<'ALL' | 'CRITICAL' | 'ELEVATED'>('ALL');
  const [loading, setLoading] = useState(true);

  const fetchCrowd = async () => {
    try {
      const res = await fetch('http://localhost:8000/api/crowd/live-telemetry');
      if (res.ok) {
        const json = await res.json();
        setData(json);
      }
    } catch (err) {
      console.error('Crowd telemetry error:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCrowd();
    const interval = setInterval(fetchCrowd, 5000);
    return () => clearInterval(interval);
  }, []);

  const filteredStations = data?.crowd_telemetry.filter(s => {
    if (filter === 'ALL') return true;
    return s.crowd_status === filter;
  }) || [];

  if (loading) {
    return (
      <div className="flex items-center justify-center p-8 text-cyan-400 font-mono text-xs">
        <Activity className="w-5 h-5 animate-pulse mr-2" />
        AGGREGATING TURNSTILE SENSOR TELEMETRY...
      </div>
    );
  }

  return (
    <div className="w-full bg-slate-900/40 border border-slate-800/80 rounded-2xl p-6 backdrop-blur-md">
      {/* Module Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-5 border-b border-slate-800/80 mb-6">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <Users className="w-4 h-4 text-cyan-400" />
            <h2 className="text-sm font-bold tracking-wider uppercase text-slate-100">
              Live Crowd Intelligence & Turnstile Telemetry
            </h2>
          </div>
          <p className="text-xs text-slate-400">
            Real-time platform density and gate throughput metrics (Non-CV sensor data)
          </p>
        </div>

        {/* Filters and Meta */}
        <div className="flex items-center gap-2">
          <button
            onClick={() => setFilter('ALL')}
            className={`px-3 py-1.5 rounded-lg text-xs font-mono font-bold transition ${
              filter === 'ALL'
                ? 'bg-cyan-500/20 text-cyan-400 border border-cyan-500/40'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            ALL STATIONS
          </button>
          <button
            onClick={() => setFilter('CRITICAL')}
            className={`px-3 py-1.5 rounded-lg text-xs font-mono font-bold transition ${
              filter === 'CRITICAL'
                ? 'bg-rose-500/20 text-rose-400 border border-rose-500/40'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            CRITICAL ONLY
          </button>
        </div>
      </div>

      {/* Grid of Station Crowd Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {filteredStations.map((st) => (
          <div
            key={st.station_id}
            className={`bg-slate-950/80 border rounded-xl p-4 transition-all ${
              st.crowd_status === 'CRITICAL'
                ? 'border-rose-500/50 shadow-[0_0_20px_rgba(244,63,94,0.12)]'
                : st.crowd_status === 'ELEVATED'
                ? 'border-amber-500/40'
                : 'border-slate-800/80'
            }`}
          >
            <div className="flex items-start justify-between mb-3">
              <div>
                <span className="text-[10px] font-mono text-slate-500 uppercase">{st.station_id} • {st.line}</span>
                <h3 className="text-sm font-bold text-slate-200">{st.name}</h3>
              </div>
              <span className={`text-[10px] font-mono font-bold px-2 py-0.5 rounded-full ${
                st.crowd_status === 'CRITICAL'
                  ? 'bg-rose-500/20 text-rose-400 border border-rose-500/30'
                  : st.crowd_status === 'ELEVATED'
                  ? 'bg-amber-500/20 text-amber-400 border border-amber-500/30'
                  : 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
              }`}>
                {st.current_platform_load_pct}% LOAD
              </span>
            </div>

            {/* Density Bar */}
            <div className="w-full bg-slate-900 h-1.5 rounded-full overflow-hidden mb-3.5">
              <div
                className={`h-full transition-all duration-500 ${
                  st.current_platform_load_pct > 80
                    ? 'bg-rose-500'
                    : st.current_platform_load_pct > 60
                    ? 'bg-amber-500'
                    : 'bg-emerald-500'
                }`}
                style={{ width: `${st.current_platform_load_pct}%` }}
              />
            </div>

            {/* Inflow vs Outflow Rate */}
            <div className="grid grid-cols-2 gap-2 text-xs font-mono mb-3">
              <div className="p-2 bg-slate-900/60 rounded-lg border border-slate-800/60">
                <span className="text-[10px] text-slate-500 flex items-center gap-1">
                  <ArrowUpRight className="w-3 h-3 text-cyan-400" /> INFLOW
                </span>
                <span className="text-slate-200 font-bold mt-0.5 block">{st.inflow_per_min} /min</span>
              </div>
              <div className="p-2 bg-slate-900/60 rounded-lg border border-slate-800/60">
                <span className="text-[10px] text-slate-500 flex items-center gap-1">
                  <ArrowDownRight className="w-3 h-3 text-emerald-400" /> OUTFLOW
                </span>
                <span className="text-slate-200 font-bold mt-0.5 block">{st.outflow_per_min} /min</span>
              </div>
            </div>

            {/* Turnstiles & Trend Info */}
            <div className="flex items-center justify-between text-[11px] font-mono text-slate-400 pt-2 border-t border-slate-800/60">
              <span>Gates: {st.entry_turnstiles_active + st.exit_turnstiles_active} Active</span>
              <span className={`font-bold ${
                st.trend === 'SURGE' ? 'text-rose-400' :
                st.trend === 'INCREASING' ? 'text-amber-400' : 'text-slate-400'
              }`}>
                Trend: {st.trend}
              </span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};