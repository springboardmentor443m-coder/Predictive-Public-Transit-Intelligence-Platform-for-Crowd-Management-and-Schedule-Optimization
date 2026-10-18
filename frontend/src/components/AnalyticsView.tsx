import React, { useEffect, useState } from 'react';
import { BarChart3, TrendingUp, Users, Shield, Clock, ArrowDownRight, ArrowUpRight, Award, FileText } from 'lucide-react';
import { ResponsiveContainer, AreaChart, Area, BarChart, Bar, XAxis, YAxis, Tooltip, Legend } from 'recharts';
import { api } from '../services/api';

export const AnalyticsView: React.FC = () => {
  const [overview, setOverview] = useState<any>(null);
  const [demandCurve, setDemandCurve] = useState<any[]>([]);
  const [rankings, setRankings] = useState<any[]>([]);
  const [auditLogs, setAuditLogs] = useState<any[]>([]);
  const [flowData, setFlowData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      api.getAnalyticsOverview(),
      api.getHourlyPatterns(),
      api.getStationRankings(),
      api.getAuditLogs(),
      api.getFlowAnalysis()
    ])
      .then(([ov, hr, rk, lg, fl]) => {
        setOverview(ov);
        setDemandCurve(hr.demand_curve);
        setRankings(rk.rankings);
        setAuditLogs(lg.logs);
        setFlowData(fl);
        setLoading(false);
      })
      .catch(err => {
        console.error('Failed to load analytics', err);
        setLoading(false);
      });
  }, []);

  if (loading) {
    return (
      <div className="p-16 text-center text-slate-400 animate-pulse">
        Compiling ridership datasets and generating performance analytics...
      </div>
    );
  }

  // Format top 5 flow for bar chart
  const flowBarData = flowData?.top_inflow_stations?.slice(0, 5).map((s: any, idx: number) => ({
    name: s.name.replace(' - ', ' '),
    Inflow: s.inflow_rate,
    Outflow: flowData.top_outflow_stations[idx]?.outflow_rate || s.inflow_rate * 0.95
  })) || [];

  return (
    <div className="space-y-6">
      {/* Top Analytics Summary Bar */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-slate-900 border border-slate-800 p-4 rounded-2xl shadow-sm">
          <div className="text-slate-400 text-xs mb-1 flex items-center space-x-1.5">
            <Users className="w-3.5 h-3.5 text-blue-400" />
            <span>Estimated Daily Ridership</span>
          </div>
          <div className="text-2xl font-black text-white">
            {overview?.daily_ridership_estimated?.toLocaleString()}
          </div>
          <div className="text-[10px] text-emerald-400 mt-1 font-semibold">&uarr; 4.8% vs Baseline Week</div>
        </div>

        <div className="bg-slate-900 border border-slate-800 p-4 rounded-2xl shadow-sm">
          <div className="text-slate-400 text-xs mb-1 flex items-center space-x-1.5">
            <TrendingUp className="w-3.5 h-3.5 text-emerald-400" />
            <span>On-Time Performance</span>
          </div>
          <div className="text-2xl font-black text-emerald-400">
            {overview?.on_time_performance_percent}%
          </div>
          <div className="text-[10px] text-slate-400 mt-1">Schedule Adherence Rate</div>
        </div>

        <div className="bg-slate-900 border border-slate-800 p-4 rounded-2xl shadow-sm">
          <div className="text-slate-400 text-xs mb-1 flex items-center space-x-1.5">
            <Clock className="w-3.5 h-3.5 text-cyan-400" />
            <span>Average Dwell Clearance</span>
          </div>
          <div className="text-2xl font-black text-cyan-400">
            {overview?.avg_station_dwell_seconds}s
          </div>
          <div className="text-[10px] text-slate-400 mt-1">Station Door Open Duration</div>
        </div>

        <div className="bg-slate-900 border border-slate-800 p-4 rounded-2xl shadow-sm">
          <div className="text-slate-400 text-xs mb-1 flex items-center space-x-1.5">
            <Shield className="w-3.5 h-3.5 text-purple-400" />
            <span>Headway Compliance</span>
          </div>
          <div className="text-2xl font-black text-purple-400">
            {overview?.headway_compliance_percent}%
          </div>
          <div className="text-[10px] text-slate-400 mt-1">Active Peak Regularity</div>
        </div>
      </div>

      {/* 24-Hour Passenger Demand vs Offered Capacity */}
      <div className="bg-slate-900 border border-slate-800 p-6 rounded-2xl shadow-xl">
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between mb-6 gap-2">
          <div>
            <h3 className="text-base font-bold text-white flex items-center space-x-2">
              <BarChart3 className="w-5 h-5 text-blue-400" />
              <span>24-Hour Commuter Demand Profile vs Offered Train Capacity</span>
            </h3>
            <p className="text-xs text-slate-400 mt-0.5">
              Hourly transit ridership curve illustrating Morning Peak (7:30-9:30 AM) and Evening Peak (4:30-7:00 PM)
            </p>
          </div>
          <div className="flex items-center space-x-2 text-xs">
            <span className="flex items-center space-x-1 text-blue-400">
              <span className="w-2.5 h-2.5 bg-blue-500 rounded-sm"></span>
              <span>Actual Ridership</span>
            </span>
            <span className="flex items-center space-x-1 text-emerald-400">
              <span className="w-2.5 h-2.5 bg-emerald-500 rounded-sm"></span>
              <span>Offered Capacity</span>
            </span>
          </div>
        </div>

        <div className="h-72 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={demandCurve}>
              <defs>
                <linearGradient id="ridershipGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#3B82F6" stopOpacity={0.5}/>
                  <stop offset="95%" stopColor="#3B82F6" stopOpacity={0.0}/>
                </linearGradient>
                <linearGradient id="capGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#10B981" stopOpacity={0.3}/>
                  <stop offset="95%" stopColor="#10B981" stopOpacity={0.0}/>
                </linearGradient>
              </defs>
              <XAxis dataKey="hour" stroke="#64748b" fontSize={11} tickLine={false} />
              <YAxis stroke="#64748b" fontSize={11} tickLine={false} tickFormatter={(val) => `${(val / 1000).toFixed(0)}k`} />
              <Tooltip
                contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '12px' }}
                labelStyle={{ color: '#cbd5e1', fontWeight: 'bold' }}
              />
              <Area type="monotone" dataKey="actual_passengers" stroke="#3B82F6" strokeWidth={2.5} fill="url(#ridershipGradient)" name="Actual Ridership" />
              <Area type="monotone" dataKey="train_capacity_offered" stroke="#10B981" strokeWidth={2} strokeDasharray="3 3" fill="url(#capGradient)" name="Offered Capacity" />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Two Column Section: Top Turnstile Inflow/Outflow & Audit Logs */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Turnstile Inflow vs Outflow Comparison */}
        <div className="bg-slate-900 border border-slate-800 p-5 rounded-2xl shadow-xl space-y-4">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <h3 className="text-sm font-bold text-white flex items-center space-x-2">
              <TrendingUp className="w-4 h-4 text-emerald-400" />
              <span>Busiest Interchange Stations: Inflow vs Outflow</span>
            </h3>
            <span className="text-xs text-slate-400 font-mono">passengers / min</span>
          </div>

          <div className="h-60 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={flowBarData}>
                <XAxis dataKey="name" stroke="#64748b" fontSize={11} tickLine={false} />
                <YAxis stroke="#64748b" fontSize={11} tickLine={false} />
                <Tooltip contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '10px' }} />
                <Legend />
                <Bar dataKey="Inflow" fill="#10B981" radius={[4, 4, 0, 0]} />
                <Bar dataKey="Outflow" fill="#3B82F6" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Operational Audit Log (Tracking Dispatcher Actions) */}
        <div className="bg-slate-900 border border-slate-800 p-5 rounded-2xl shadow-xl space-y-4">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <h3 className="text-sm font-bold text-white flex items-center space-x-2">
              <FileText className="w-4 h-4 text-purple-400" />
              <span>Operational Dispatch Audit Trail</span>
            </h3>
            <span className="text-xs text-slate-400 font-mono">Role-Logged Events</span>
          </div>

          <div className="space-y-2.5 max-h-[250px] overflow-y-auto pr-1">
            {auditLogs.map((log: any) => (
              <div
                key={log.id}
                className="p-3 bg-slate-950 rounded-xl border border-slate-800/80 text-xs space-y-1"
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <span className="font-bold text-white">{log.user_name}</span>
                    <span className="text-[10px] font-mono px-1.5 py-0.2 rounded bg-slate-800 text-slate-400 uppercase">
                      {log.role}
                    </span>
                  </div>
                  <span className="text-[10px] text-slate-500 font-mono">{log.timestamp}</span>
                </div>
                <div className="text-slate-300">{log.details}</div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Station Performance Rankings Table */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl overflow-hidden shadow-xl">
        <div className="p-5 border-b border-slate-800 flex items-center justify-between">
          <h3 className="text-sm font-bold text-white flex items-center space-x-2">
            <Award className="w-4 h-4 text-amber-400" />
            <span>Station Throughput & Congestion Index Rankings</span>
          </h3>
          <span className="text-xs text-slate-400">NYC Network Primary Stations</span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs text-slate-300">
            <thead className="bg-slate-950/70 text-slate-400 uppercase font-bold text-[10px] tracking-wider border-b border-slate-800">
              <tr>
                <th className="py-3 px-4">Rank</th>
                <th className="py-3 px-4">Station Name</th>
                <th className="py-3 px-4">Borough</th>
                <th className="py-3 px-4 text-center">Crowd Density</th>
                <th className="py-3 px-4 text-center">Turnstile Inflow</th>
                <th className="py-3 px-4 text-center">Turnstile Outflow</th>
                <th className="py-3 px-4 text-center">Congestion Status</th>
                <th className="py-3 px-4 text-right">Capacity</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 font-medium">
              {rankings.map(r => (
                <tr key={r.id} className="hover:bg-slate-800/40 transition">
                  <td className="py-3 px-4 font-mono font-bold text-slate-400">#{r.rank}</td>
                  <td className="py-3 px-4 font-bold text-white">{r.name}</td>
                  <td className="py-3 px-4 text-slate-400">{r.borough}</td>
                  <td className="py-3 px-4 text-center font-bold text-cyan-400">{r.density_percent}%</td>
                  <td className="py-3 px-4 text-center text-emerald-400">{r.inflow_rate} /min</td>
                  <td className="py-3 px-4 text-center text-blue-400">{r.outflow_rate} /min</td>
                  <td className="py-3 px-4 text-center">
                    <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase ${
                      r.congestion_level === 'Severe' ? 'bg-red-500/20 text-red-300 border border-red-500/30' :
                      r.congestion_level === 'High' ? 'bg-orange-500/20 text-orange-300 border border-orange-500/30' :
                      r.congestion_level === 'Moderate' ? 'bg-amber-500/20 text-amber-300 border border-amber-500/30' :
                      'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30'
                    }`}>
                      {r.congestion_level}
                    </span>
                  </td>
                  <td className="py-3 px-4 text-right font-mono text-slate-300">
                    {r.capacity.toLocaleString()}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
