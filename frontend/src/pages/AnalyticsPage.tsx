import React, { useState, useEffect, useMemo } from 'react';
import { api } from '../api/client';
import { SystemAnalytics, StationRankingItem } from '../types';
import { MetricCard } from '../components/MetricCard';
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  Legend,
} from 'recharts';
import {
  BarChart3,
  TrendingUp,
  ArrowUpDown,
  Train,
  AlertTriangle,
  Users,
  Activity,
  ArrowRight,
} from 'lucide-react';
import { Link } from 'react-router-dom';

type SortField = 'total_traffic' | 'total_inflow' | 'total_outflow' | 'alert_count';

export const AnalyticsPage: React.FC = () => {
  const [analytics, setAnalytics] = useState<SystemAnalytics | null>(null);
  const [sortField, setSortField] = useState<SortField>('total_traffic');
  const [sortAsc, setSortAsc] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadAnalytics = async () => {
      try {
        setLoading(true);
        const data = await api.getAnalyticsOverview(15);
        setAnalytics(data);
      } catch (err) {
        console.error('Failed to load analytics:', err);
      } finally {
        setLoading(false);
      }
    };

    loadAnalytics();
  }, []);

  const handleSort = (field: SortField) => {
    if (sortField === field) {
      setSortAsc(!sortAsc);
    } else {
      setSortField(field);
      setSortAsc(false);
    }
  };

  const sortedRankings = useMemo(() => {
    if (!analytics?.busiest_stations) return [];
    return [...analytics.busiest_stations].sort((a, b) => {
      const valA = a[sortField];
      const valB = b[sortField];
      return sortAsc ? valA - valB : valB - valA;
    });
  }, [analytics, sortField, sortAsc]);

  // Chart data for top 8 busiest stations
  const chartData = useMemo(() => {
    if (!analytics?.busiest_stations) return [];
    return analytics.busiest_stations.slice(0, 8).map((st) => ({
      name: st.name_en,
      Inflow: Math.round(st.total_inflow / 1000),
      Outflow: Math.round(st.total_outflow / 1000),
    }));
  }, [analytics]);

  if (loading || !analytics) {
    return (
      <div className="p-8 text-center text-slate-400 font-mono text-xs">
        <div className="inline-block animate-spin mb-3">
          <BarChart3 className="w-8 h-8 text-metro-cyan" />
        </div>
        <p>Aggregating system-wide traffic distributions and ranking tables...</p>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6 max-w-7xl mx-auto">
      {/* Page Title */}
      <div>
        <h1 className="text-2xl font-extrabold text-slate-100 tracking-tight font-sans">
          Network Analytics & Station Performance Rankings
        </h1>
        <p className="text-xs text-slate-400 font-mono mt-1">
          Aggregated ridership volume trends, station bottleneck rankings, and capacity utilization
        </p>
      </div>

      {/* KPI Metric Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard
          title="Monitored Stations"
          value={analytics.total_stations}
          subtitle="9 Metropolitan Lines"
          icon={Train}
          accentColor="cyan"
        />
        <MetricCard
          title="Network Avg Occupancy"
          value={`${analytics.average_network_occupancy}%`}
          subtitle="Across All Active Consists"
          icon={Activity}
          trend="+1.8% vs last week"
          trendPositive={true}
          accentColor="emerald"
        />
        <MetricCard
          title="Total Alert Events"
          value={analytics.total_alerts}
          subtitle="Logged Incident Records"
          icon={AlertTriangle}
          accentColor="amber"
        />
        <MetricCard
          title="Active Congestion Surges"
          value={analytics.active_alerts}
          subtitle="Currently Open Incidents"
          icon={Users}
          accentColor="crimson"
        />
      </div>

      {/* Recharts Busiest Stations Comparison Bar Chart */}
      <div className="bg-bg-surface border border-border-dark rounded-2xl p-6 shadow-card space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-base font-bold text-slate-100">
              Top Transit Hub Passenger Volume (k Pax)
            </h3>
            <p className="text-xs font-mono text-slate-400 mt-0.5">
              Comparative passenger entries (inflow) vs exits (outflow) at key transfer stations
            </p>
          </div>
          <span className="text-xs font-mono text-metro-cyan bg-metro-cyan/10 border border-metro-cyan/30 px-2.5 py-1 rounded-lg">
            Recharts Engine
          </span>
        </div>

        <div className="h-[320px] w-full pt-2">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={chartData} margin={{ top: 10, right: 10, left: -15, bottom: 20 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1F2B44" vertical={false} />
              <XAxis
                dataKey="name"
                stroke="#64748B"
                fontSize={11}
                tickLine={false}
                fontFamily="JetBrains Mono"
                angle={-15}
                textAnchor="end"
              />
              <YAxis
                stroke="#64748B"
                fontSize={11}
                tickLine={false}
                fontFamily="JetBrains Mono"
                unit="k"
              />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#121A2D',
                  borderColor: '#25334D',
                  borderRadius: '10px',
                  color: '#F1F5F9',
                  fontFamily: 'JetBrains Mono',
                  fontSize: '12px',
                }}
              />
              <Legend
                wrapperStyle={{
                  paddingTop: '10px',
                  fontFamily: 'JetBrains Mono',
                  fontSize: '12px',
                }}
              />
              <Bar dataKey="Inflow" name="Inflow (k)" fill="#00F0FF" radius={[4, 4, 0, 0]} />
              <Bar dataKey="Outflow" name="Outflow (k)" fill="#6366F1" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Sortable Station Performance Ranking Table */}
      <div className="bg-bg-surface border border-border-dark rounded-2xl p-6 shadow-card space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
          <div>
            <h3 className="text-base font-bold text-slate-100">
              Station Performance & Congestion Rankings
            </h3>
            <p className="text-xs font-mono text-slate-400 mt-0.5">
              Sort by passenger traffic volume, entry/exit dynamics, and historical alert frequencies
            </p>
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs font-mono">
            <thead>
              <tr className="border-b border-border-dark text-slate-400 uppercase text-[10px]">
                <th className="py-3 px-3">Rank</th>
                <th className="py-3 px-3">Station Name</th>
                <th className="py-3 px-3">Line</th>
                <th className="py-3 px-3">District</th>
                <th
                  onClick={() => handleSort('total_traffic')}
                  className="py-3 px-3 cursor-pointer hover:text-metro-cyan transition-colors"
                >
                  <div className="flex items-center gap-1.5">
                    <span>Total Traffic</span>
                    <ArrowUpDown className="w-3 h-3" />
                  </div>
                </th>
                <th
                  onClick={() => handleSort('total_inflow')}
                  className="py-3 px-3 cursor-pointer hover:text-metro-cyan transition-colors"
                >
                  <div className="flex items-center gap-1.5">
                    <span>Inflow</span>
                    <ArrowUpDown className="w-3 h-3" />
                  </div>
                </th>
                <th
                  onClick={() => handleSort('total_outflow')}
                  className="py-3 px-3 cursor-pointer hover:text-metro-cyan transition-colors"
                >
                  <div className="flex items-center gap-1.5">
                    <span>Outflow</span>
                    <ArrowUpDown className="w-3 h-3" />
                  </div>
                </th>
                <th
                  onClick={() => handleSort('alert_count')}
                  className="py-3 px-3 cursor-pointer hover:text-metro-cyan transition-colors"
                >
                  <div className="flex items-center gap-1.5">
                    <span>Alerts</span>
                    <ArrowUpDown className="w-3 h-3" />
                  </div>
                </th>
                <th className="py-3 px-3 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border-dark/60 text-slate-200">
              {sortedRankings.map((st, idx) => (
                <tr
                  key={st.station_code}
                  className="hover:bg-bg-card/70 transition-colors"
                >
                  <td className="py-3 px-3 text-slate-400 font-bold">#{idx + 1}</td>
                  <td className="py-3 px-3">
                    <div className="font-sans font-bold text-slate-100">{st.name_en}</div>
                    {st.name_kr && (
                      <div className="text-[11px] text-slate-400 font-sans">{st.name_kr}</div>
                    )}
                  </td>
                  <td className="py-3 px-3">
                    <span className="px-2 py-0.5 rounded bg-bg-card border border-border-dark text-[11px] text-metro-cyan font-bold">
                      {st.line}
                    </span>
                  </td>
                  <td className="py-3 px-3 text-slate-400">{st.district || 'Seoul'}</td>
                  <td className="py-3 px-3 font-bold text-slate-100">
                    {st.total_traffic.toLocaleString()}
                  </td>
                  <td className="py-3 px-3 text-metro-cyan">{st.total_inflow.toLocaleString()}</td>
                  <td className="py-3 px-3 text-indigo-400">{st.total_outflow.toLocaleString()}</td>
                  <td className="py-3 px-3">
                    <span
                      className={`px-2 py-0.5 rounded text-[11px] font-bold ${
                        st.alert_count > 0
                          ? 'bg-amber-950/60 text-amber-400 border border-amber-800/60'
                          : 'bg-slate-800 text-slate-400'
                      }`}
                    >
                      {st.alert_count}
                    </span>
                  </td>
                  <td className="py-3 px-3 text-right">
                    <Link
                      to={`/stations/${st.station_code}`}
                      className="inline-flex items-center gap-1 text-metro-cyan hover:underline font-semibold text-[11px]"
                    >
                      <span>View</span>
                      <ArrowRight className="w-3 h-3" />
                    </Link>
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
