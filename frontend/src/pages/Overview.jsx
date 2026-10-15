import React from 'react';
import {
  MapPin,
  AlertTriangle,
  Train,
  Clock,
  TrendingUp,
  ShieldCheck,
  Zap,
  Activity,
  ArrowRight,
  Send,
} from 'lucide-react';
import MetricCard from '../components/MetricCard';
import StatusBadge from '../components/StatusBadge';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts';

export default function Overview({
  stationsData,
  trainsData,
  alerts,
  onNavigate,
  onInspectStation,
}) {
  const stations = stationsData?.stations || [];
  const highCongestionCount = stationsData?.counts_by_tier?.High || stations.filter((s) => s.congestion_level === 'High').length;
  const medCongestionCount = stationsData?.counts_by_tier?.Medium || stations.filter((s) => s.congestion_level === 'Medium').length;
  const lowCongestionCount = stationsData?.counts_by_tier?.Low || stations.filter((s) => s.congestion_level === 'Low').length;

  const fleetKpis = trainsData?.kpis || {
    active_trains: 29,
    delayed_trains: 6,
    ontime_trains: 23,
    avg_speed: 27.1,
    on_time_pct: 79.3,
  };

  // Hourly preview curve
  const sampleHourlyData = [
    { hour: '06:00', traffic: 650 },
    { hour: '07:00', traffic: 1480 },
    { hour: '08:00', traffic: 2350 },
    { hour: '09:00', traffic: 1980 },
    { hour: '12:00', traffic: 1460 },
    { hour: '16:00', traffic: 2450 },
    { hour: '17:00', traffic: 2680 },
    { hour: '18:00', traffic: 2390 },
    { hour: '20:00', traffic: 1320 },
  ];

  const highStations = stations.filter((s) => s.congestion_level === 'High').slice(0, 5);

  return (
    <div className="space-y-6">
      {/* Top Welcome / Status Directive */}
      <div className="ops-panel p-5 bg-gradient-to-r from-[#111827] via-slate-900 to-[#162032] border border-slate-800 flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="text-xs font-mono font-bold px-2 py-0.5 rounded bg-teal-500/10 text-[#00D4AA] border border-teal-500/20">
              MTA DISPATCH TELEMETRY
            </span>
            <span className="text-xs text-slate-400 font-mono">
              NYC SUBWAY NETWORK OCC
            </span>
          </div>
          <h2 className="text-xl font-bold text-white tracking-wide">
            Transit Operations Command Center
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Predictive crowd intelligence, automated headway regulation, and kinematic train tracking.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={() => onNavigate('crowd-monitoring')}
            className="btn-primary"
          >
            <MapPin size={14} />
            <span>Open Live Heatmap</span>
          </button>
          <button
            onClick={() => onNavigate('train-tracking')}
            className="btn-secondary"
          >
            <Train size={14} />
            <span>Track Fleet</span>
          </button>
        </div>
      </div>

      {/* Primary KPI Metric Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard
          title="Monitored Stations"
          value={stations.length || '361'}
          delta="100% Coverage"
          deltaType="positive"
          subtext="across 4 NYC Boroughs"
          icon={MapPin}
          accentColor="#38BDF8"
        />

        <MetricCard
          title="High Congestion Hotspots"
          value={highCongestionCount}
          delta={highCongestionCount > 100 ? 'Surge Peak' : 'Nominal'}
          deltaType={highCongestionCount > 100 ? 'warning' : 'positive'}
          subtext={`Med: ${medCongestionCount} | Low: ${lowCongestionCount}`}
          icon={AlertTriangle}
          accentColor="#EF4444"
        />

        <MetricCard
          title="Active Simulated Fleet"
          value={`${fleetKpis.active_trains || 29} Trains`}
          delta={`${fleetKpis.on_time_pct || 79}% On-Time`}
          deltaType="positive"
          subtext={`${fleetKpis.delayed_trains || 6} Delayed`}
          icon={Train}
          accentColor="#00D4AA"
        />

        <MetricCard
          title="Average Fleet Velocity"
          value={`${fleetKpis.avg_speed || 27.1} mph`}
          delta="Normal Flow"
          deltaType="neutral"
          subtext="Tunnel & Elevated tracks"
          icon={Clock}
          accentColor="#818CF8"
        />
      </div>

      {/* Middle Grid: Congestion Hotspots & Diurnal Curve */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left 2 Cols: High Congestion Stations Alert List */}
        <div className="lg:col-span-2 ops-panel p-5">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="text-sm font-bold text-white flex items-center gap-2">
                <AlertTriangle size={16} className="text-[#EF4444]" />
                <span>Critical Congestion Watchlist (Active Peak Hour)</span>
              </h3>
              <p className="text-xs text-slate-400 mt-0.5">
                Subway stations flagged for immediate dispatch action or platform monitoring.
              </p>
            </div>
            <button
              onClick={() => onNavigate('crowd-monitoring')}
              className="text-xs text-[#00D4AA] hover:underline flex items-center gap-1 font-semibold"
            >
              <span>View All 361 Stations</span>
              <ArrowRight size={12} />
            </button>
          </div>

          <div className="overflow-x-auto">
            <table className="ops-table">
              <thead>
                <tr>
                  <th>Station Name</th>
                  <th>Borough</th>
                  <th>Structure</th>
                  <th>Congestion</th>
                  <th>Confidence</th>
                  <th>Operational Directive</th>
                  <th>Action</th>
                </tr>
              </thead>
              <tbody>
                {highStations.length > 0 ? (
                  highStations.map((st, i) => (
                    <tr key={st.id || i} className="hover:bg-slate-800/40">
                      <td className="font-semibold text-white">{st.name}</td>
                      <td>{st.borough}</td>
                      <td className="text-slate-400">{st.structure}</td>
                      <td>
                        <StatusBadge status={st.congestion_level} />
                      </td>
                      <td className="font-mono text-xs text-slate-300">
                        {Math.round((st.confidence || 0.9) * 100)}%
                      </td>
                      <td className="text-slate-300 max-w-xs truncate">
                        {st.recommendation}
                      </td>
                      <td>
                        <button
                          onClick={() => onInspectStation(st)}
                          className="px-2.5 py-1 text-xs rounded bg-slate-800 hover:bg-slate-700 text-sky-400 font-medium transition"
                        >
                          Inspect
                        </button>
                      </td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan={7} className="text-center py-6 text-slate-500">
                      No high congestion alerts active.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>

        {/* Right Col: Diurnal Profile & Quick Jump */}
        <div className="ops-panel p-5 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-sm font-bold text-white flex items-center gap-2">
                <TrendingUp size={16} className="text-[#38BDF8]" />
                <span>Diurnal Peak Traffic Curve</span>
              </h3>
              <span className="text-[10px] font-mono text-slate-500">
                4.58M Turnstile Basis
              </span>
            </div>
            <p className="text-xs text-slate-400 mb-4">
              Typical passenger volume trends illustrating morning (8 AM) and evening (5 PM) peak rushes.
            </p>

            <div className="h-44 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={sampleHourlyData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1E293B" />
                  <XAxis
                    dataKey="hour"
                    stroke="#64748B"
                    tick={{ fontSize: 10 }}
                  />
                  <YAxis
                    stroke="#64748B"
                    tick={{ fontSize: 10 }}
                    width={35}
                  />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: '#111827',
                      borderColor: '#374151',
                      fontSize: '11px',
                      color: '#F8FAFC',
                    }}
                  />
                  <Line
                    type="monotone"
                    dataKey="traffic"
                    stroke="#00D4AA"
                    strokeWidth={2}
                    dot={{ fill: '#00D4AA', r: 3 }}
                    name="Passengers/hr"
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>

          <div className="mt-4 pt-4 border-t border-slate-800 space-y-2">
            <div className="text-xs font-semibold text-slate-300">
              Quick Operations Actions:
            </div>
            <div className="grid grid-cols-2 gap-2 text-xs">
              <button
                onClick={() => onNavigate('schedule-management')}
                className="p-2 rounded bg-slate-800/80 hover:bg-slate-700 text-slate-200 border border-slate-700 flex items-center gap-2 justify-center transition"
              >
                <Clock size={13} className="text-[#00D4AA]" />
                <span>Adjust Headway</span>
              </button>
              <button
                onClick={() => onNavigate('real-time-prediction')}
                className="p-2 rounded bg-slate-800/80 hover:bg-slate-700 text-slate-200 border border-slate-700 flex items-center gap-2 justify-center transition"
              >
                <Zap size={13} className="text-sky-400" />
                <span>Run Prediction</span>
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Bottom Row: Recent Alert History & Operational Guidelines */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Recent Alerts Feed */}
        <div className="ops-panel p-5">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-sm font-bold text-white flex items-center gap-2">
              <AlertTriangle size={15} className="text-[#F59E0B]" />
              <span>Incident & Alert Logbook (Active Session)</span>
            </h3>
            <button
              onClick={() => onNavigate('alerts-center')}
              className="text-xs text-[#00D4AA] hover:underline font-semibold"
            >
              Open Alert Center
            </button>
          </div>

          <div className="space-y-2.5">
            {alerts && alerts.length > 0 ? (
              alerts.slice(0, 4).map((alert, idx) => (
                <div
                  key={alert.id || idx}
                  className="p-3 rounded-lg bg-slate-900 border border-slate-800/80 flex items-start justify-between gap-3 text-xs"
                >
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <StatusBadge status={alert.severity || alert.level} size="sm" />
                      <span className="font-semibold text-slate-200">
                        {alert.station}
                      </span>
                      <span className="text-[10px] text-slate-500 font-mono">
                        ({alert.borough})
                      </span>
                    </div>
                    <p className="text-slate-400 text-[11px] leading-relaxed">
                      {alert.message}
                    </p>
                  </div>
                  <div className="text-[10px] font-mono text-slate-500 shrink-0">
                    {alert.timestamp || 'Just now'}
                  </div>
                </div>
              ))
            ) : (
              <div className="p-4 text-center text-slate-500 text-xs">
                No incident alerts recorded yet.
              </div>
            )}
          </div>
        </div>

        {/* Model Architecture & Operational Disclaimer */}
        <div className="ops-panel p-5 flex flex-col justify-between">
          <div>
            <h3 className="text-sm font-bold text-white flex items-center gap-2 mb-2">
              <ShieldCheck size={16} className="text-[#00D4AA]" />
              <span>Transit Intelligence Pipeline Specifications</span>
            </h3>
            <p className="text-xs text-slate-400 leading-relaxed mb-4">
              MetroFlow employs a non-leaked machine learning architecture evaluated across 4.58M turnstile records:
            </p>

            <ul className="space-y-2 text-xs text-slate-300">
              <li className="flex items-start gap-2">
                <span className="text-[#00D4AA] font-bold">1.</span>
                <span>
                  <strong>Congestion Classifier:</strong> Random Forest Classifier (Champion: 87.1% accuracy, 0.8703 F1) trained without target leakage.
                </span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-[#38BDF8] font-bold">2.</span>
                <span>
                  <strong>Demand Regressor:</strong> Random Forest Regressor predicting continuous turnstile volumes for 1h, 3h, and 24h horizons.
                </span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-[#818CF8] font-bold">3.</span>
                <span>
                  <strong>Kinematics Simulator:</strong> Realistic NYC subway train progression along verified corridor station sequences (SIMULATED).
                </span>
              </li>
            </ul>
          </div>

          <div className="mt-4 p-3 rounded bg-slate-900/80 border border-slate-800 text-[11px] text-slate-400">
            <strong>Mentor & Presentation Notice:</strong> Train positions and throughput numbers are simulated for demonstration. Station locations and turnstile profiles reflect audited NYC Transit data.
          </div>
        </div>
      </div>
    </div>
  );
}
