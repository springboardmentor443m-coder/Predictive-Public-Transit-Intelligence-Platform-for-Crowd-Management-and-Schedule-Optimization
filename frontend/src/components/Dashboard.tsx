import { ScheduleOptimizer } from './ScheduleOptimizer';
import { CrowdIntelligence } from './CrowdIntelligence';
import { IncidentManager } from './IncidentManager';
import React, { useEffect, useState } from 'react';
import { 
  Activity, 
  Users, 
  GitBranch, 
  AlertTriangle, 
  Gauge, 
  RefreshCw,
  LogOut,
  Radio,
  CheckCircle2
} from 'lucide-react';
import { NetworkMap } from './NetworkMap';

interface DashboardData {
  network_status: string;
  metrics: {
    total_passengers_today: number;
    active_stations: number;
    total_stations: number;
    average_congestion_pct: number;
    active_alerts_count: number;
  };
  station_quick_status: Array<{
    id: string;
    name: string;
    line: string;
    congestion: number;
    status: string;
  }>;
  critical_alerts: Array<{
    id: string;
    station: string;
    type: string;
    severity: string;
    time: string;
  }>;
}

interface DashboardProps {
  onLogout: () => void;
}

export const Dashboard: React.FC<DashboardProps> = ({ onLogout }) => {
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);

  const fetchDashboard = async () => {
    try {
      const res = await fetch('http://localhost:8000/api/dashboard/summary');
      if (!res.ok) throw new Error('Failed to fetch data');
      const result = await res.json();
      setData(result);
    } catch (err) {
      console.error('Telemetry fetch error:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDashboard();
    const timer = setInterval(fetchDashboard, 10000);
    return () => clearInterval(timer);
  }, []);

  if (loading) {
    return (
      <div className="min-h-screen bg-[#030712] flex items-center justify-center text-cyan-400 gap-3">
        <Activity className="w-6 h-6 animate-pulse" />
        <span className="font-mono text-xs uppercase tracking-widest">
          Connecting to Metro Operations Telemetry...
        </span>
      </div>
    );
  }

  return (
    <div className="min-h-screen w-full bg-[#030712] text-slate-100 flex flex-col font-sans">
      {/* Top Operations Header */}
      <header className="sticky top-0 z-50 border-b border-slate-800/80 bg-slate-900/80 backdrop-blur-md px-6 py-3.5 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-cyan-500/10 border border-cyan-400/30 rounded-xl text-cyan-400 shadow-[0_0_15px_rgba(6,182,212,0.2)]">
            <Activity className="w-5 h-5 animate-pulse" />
          </div>
          <div>
            <h1 className="text-base font-bold tracking-wider uppercase text-slate-100">
              Metro<span className="text-cyan-400">Flow</span> Command Center
            </h1>
            <div className="flex items-center gap-2 text-[11px] text-slate-400 font-mono">
              <Radio className="w-3 h-3 text-emerald-400 animate-pulse" />
              <span>Telemetry: Active</span>
              <span>•</span>
              <span>System State: {data?.network_status}</span>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={fetchDashboard}
            className="p-2 border border-slate-800 rounded-xl text-slate-400 hover:text-cyan-400 hover:border-slate-700 transition"
            title="Sync Telemetry"
          >
            <RefreshCw className="w-4 h-4" />
          </button>
          <button
            onClick={onLogout}
            className="flex items-center gap-1.5 px-3.5 py-1.5 text-xs font-semibold bg-rose-500/10 border border-rose-500/30 text-rose-400 hover:bg-rose-500/20 rounded-xl transition"
          >
            <LogOut className="w-3.5 h-3.5" />
            Disconnect
          </button>
        </div>
      </header>

      {/* Main Command Center Body */}
      <main className="p-6 space-y-6 flex-1 max-w-7xl w-full mx-auto">
        
        {/* Metric Telemetry Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {/* Total Passengers */}
          <div className="bg-slate-900/60 border border-slate-800/80 rounded-2xl p-4 backdrop-blur-md">
            <div className="flex items-center justify-between text-slate-400 mb-1.5">
              <span className="text-[11px] font-mono tracking-wider uppercase">Network Footfall</span>
              <Users className="w-4 h-4 text-cyan-400" />
            </div>
            <div className="text-2xl font-bold font-mono text-slate-100">
              {data?.metrics.total_passengers_today.toLocaleString()}
            </div>
            <span className="text-[11px] text-emerald-400 font-mono flex items-center gap-1 mt-1">
              <CheckCircle2 className="w-3 h-3" /> Normal Flow Rate
            </span>
          </div>

          {/* Active Stations */}
          <div className="bg-slate-900/60 border border-slate-800/80 rounded-2xl p-4 backdrop-blur-md">
            <div className="flex items-center justify-between text-slate-400 mb-1.5">
              <span className="text-[11px] font-mono tracking-wider uppercase">Active Stations</span>
              <GitBranch className="w-4 h-4 text-blue-400" />
            </div>
            <div className="text-2xl font-bold font-mono text-slate-100">
              {data?.metrics.active_stations} / {data?.metrics.total_stations}
            </div>
            <span className="text-[11px] text-slate-400 font-mono mt-1 block">100% Online</span>
          </div>

          {/* Congestion Avg */}
          <div className="bg-slate-900/60 border border-slate-800/80 rounded-2xl p-4 backdrop-blur-md">
            <div className="flex items-center justify-between text-slate-400 mb-1.5">
              <span className="text-[11px] font-mono tracking-wider uppercase">Avg Congestion</span>
              <Gauge className="w-4 h-4 text-amber-400" />
            </div>
            <div className="text-2xl font-bold font-mono text-slate-100">
              {data?.metrics.average_congestion_pct}%
            </div>
            <span className="text-[11px] text-amber-400 font-mono mt-1 block">Moderate Density</span>
          </div>

          {/* Active Alerts */}
          <div className="bg-slate-900/60 border border-slate-800/80 rounded-2xl p-4 backdrop-blur-md">
            <div className="flex items-center justify-between text-slate-400 mb-1.5">
              <span className="text-[11px] font-mono tracking-wider uppercase">Active Incidents</span>
              <AlertTriangle className="w-4 h-4 text-rose-400" />
            </div>
            <div className="text-2xl font-bold font-mono text-rose-400">
              {data?.metrics.active_alerts_count}
            </div>
            <span className="text-[11px] text-rose-400 font-mono mt-1 block">Surge Action Required</span>
          </div>
        </div>

        {/* Interactive Metro Network Map (Full Width) */}
        <div>
          <NetworkMap />
        </div>
          {/* Step 4: Live Crowd Intelligence */}
           <CrowdIntelligence />
           {/* Step 5: Predictive Scheduling & Fleet Optimization */}
            <ScheduleOptimizer />
           
{/* Step 6: Surge Containment & Emergency Incident Protocols */}
<IncidentManager />
        {/* Detailed Feeds (Congestion & Alerts) */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Station Quick Status */}
          <div className="lg:col-span-2 bg-slate-900/60 border border-slate-800/80 rounded-2xl p-5 backdrop-blur-md">
            <h2 className="text-xs font-mono font-bold tracking-wider uppercase mb-4 text-slate-300">
              Station Quick Capacity Overview
            </h2>
            <div className="space-y-3">
              {data?.station_quick_status.map((st) => (
                <div key={st.id} className="p-3 bg-slate-950/70 border border-slate-800/80 rounded-xl">
                  <div className="flex items-center justify-between mb-2">
                    <div>
                      <span className="font-semibold text-sm text-slate-200">{st.name}</span>
                      <span className="text-xs font-mono text-slate-500 ml-2">({st.line} Line)</span>
                    </div>
                    <span className={`text-xs font-mono font-bold px-2 py-0.5 rounded-md ${
                      st.status === 'CRITICAL' ? 'bg-rose-500/20 text-rose-400 border border-rose-500/30' :
                      st.status === 'ELEVATED' ? 'bg-amber-500/20 text-amber-400 border border-amber-500/30' :
                      'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                    }`}>
                      {st.congestion}% Capacity
                    </span>
                  </div>
                  <div className="w-full bg-slate-800 h-1.5 rounded-full overflow-hidden">
                    <div 
                      className={`h-full rounded-full transition-all duration-500 ${
                        st.congestion > 80 ? 'bg-rose-500' :
                        st.congestion > 60 ? 'bg-amber-500' : 'bg-emerald-500'
                      }`} 
                      style={{ width: `${st.congestion}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Live Incident Alerts */}
          <div className="bg-slate-900/60 border border-slate-800/80 rounded-2xl p-5 backdrop-blur-md flex flex-col">
            <h2 className="text-xs font-mono font-bold tracking-wider uppercase mb-4 text-slate-300">
              Live Operations Feed
            </h2>
            <div className="space-y-3 flex-1">
              {data?.critical_alerts.map((alt) => (
                <div key={alt.id} className="p-3.5 bg-slate-950/80 border border-slate-800/80 rounded-xl border-l-4 border-l-rose-500">
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-xs font-bold text-slate-200">{alt.station}</span>
                    <span className="text-[10px] text-slate-500 font-mono">{alt.time}</span>
                  </div>
                  <p className="text-xs text-slate-400">{alt.type}</p>
                </div>
              ))}
            </div>
          </div>
        </div>

      </main>
    </div>
  );
};