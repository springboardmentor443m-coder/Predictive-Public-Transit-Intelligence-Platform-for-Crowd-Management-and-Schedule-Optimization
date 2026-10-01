"use client";

import { useEffect, useState, useCallback } from "react";
import {
  AreaChart, Area, BarChart, Bar, LineChart, Line,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend,
  ResponsiveContainer, RadialBarChart, RadialBar,
  PieChart, Pie, Cell,
} from "recharts";
import {
  Activity, TrendingUp, AlertTriangle, Users, Train,
  Zap, BarChart2, RefreshCw, Brain, MapPin, Clock, Eye,
} from "lucide-react";
import { api } from "./lib/api";

// ─── Types ─────────────────────────────────────────────────────────────────

interface LiveStation {
  station: string;
  ridership: number;
  avg_historical: number;
  hour: number;
  status: "low" | "moderate" | "high" | "critical";
}

interface HourlyPoint { hour: number; avg_ridership: number; }
interface DailyPoint { date: string; total_ridership: number; }
interface Insight { type: string; title: string; message: string; }
interface Anomaly { station: string; current_ridership: number; historical_avg: number; z_score: number; type: string; }
interface LinePt { hour: number; purple_line_avg: number; green_line_avg: number; }
interface Forecast { hour: number; datetime: string; predicted_ridership: number; status: string; }
interface TopStation { station: string; avg_ridership: number; }

// ─── Constants ─────────────────────────────────────────────────────────────

const STATUS_COLOR: Record<string, string> = {
  low: "#10b981",
  moderate: "#f59e0b",
  high: "#f97316",
  critical: "#ef4444",
};

const PURPLE = "#7c3aed";
const GREEN = "#10b981";
const ORANGE = "#f59e0b";
const BLUE = "#3b82f6";
const RED = "#ef4444";

// ─── Small helpers ──────────────────────────────────────────────────────────

function StatusBadge({ status }: { status: string }) {
  return (
    <span className={`badge-${status} text-xs px-2 py-0.5 rounded-full font-medium`}>
      {status.toUpperCase()}
    </span>
  );
}

function Card({ children, className = "" }: { children: React.ReactNode; className?: string }) {
  return (
    <div className={`glass p-5 ${className}`}>{children}</div>
  );
}

function SectionTitle({ icon: Icon, title }: { icon: React.ElementType; title: string }) {
  return (
    <div className="flex items-center gap-2 mb-4">
      <Icon size={18} className="text-violet-400" />
      <h2 className="text-lg font-semibold text-white">{title}</h2>
    </div>
  );
}

function Skeleton({ h = 200 }: { h?: number }) {
  return <div className="skeleton w-full rounded-lg" style={{ height: h }} />;
}

// Custom tooltip
const DarkTooltip = ({ active, payload, label }: any) => {
  if (!active || !payload?.length) return null;
  return (
    <div className="bg-gray-800 border border-gray-700 rounded-lg p-3 shadow-xl text-xs">
      <p className="text-gray-400 mb-1">{label}</p>
      {payload.map((p: any, i: number) => (
        <p key={i} style={{ color: p.color }} className="font-semibold">
          {p.name}: {typeof p.value === "number" ? p.value.toLocaleString() : p.value}
        </p>
      ))}
    </div>
  );
};

// ─── Stat Card ──────────────────────────────────────────────────────────────

function StatCard({
  label, value, icon: Icon, color, sub,
}: { label: string; value: string | number; icon: React.ElementType; color: string; sub?: string }) {
  return (
    <div className="glass p-5 flex items-center gap-4">
      <div className="rounded-xl p-3" style={{ background: `${color}20` }}>
        <Icon size={22} style={{ color }} />
      </div>
      <div>
        <p className="text-gray-400 text-xs font-medium">{label}</p>
        <p className="text-2xl font-bold text-white mt-0.5">{value}</p>
        {sub && <p className="text-gray-500 text-xs mt-0.5">{sub}</p>}
      </div>
    </div>
  );
}

// ─── Live Station Table ─────────────────────────────────────────────────────

function LiveTable({ data, loading }: { data: LiveStation[]; loading: boolean }) {
  const [search, setSearch] = useState("");
  const filtered = data.filter(d => d.station.toLowerCase().includes(search.toLowerCase()));

  return (
    <Card>
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <span className="live-dot" />
          <span className="text-sm font-semibold text-white ml-3">Live Station Ridership</span>
        </div>
        <input
          value={search}
          onChange={e => setSearch(e.target.value)}
          placeholder="Search station…"
          className="bg-gray-800 border border-gray-700 text-sm text-gray-200 rounded-lg px-3 py-1.5 outline-none focus:border-violet-500 w-48"
        />
      </div>
      {loading ? (
        <Skeleton h={320} />
      ) : (
        <div className="overflow-auto max-h-80">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-gray-500 border-b border-gray-800 text-left text-xs">
                <th className="pb-2 pr-4">#</th>
                <th className="pb-2 pr-4">Station</th>
                <th className="pb-2 pr-4 text-right">Live Riders</th>
                <th className="pb-2 pr-4 text-right">Hist. Avg</th>
                <th className="pb-2">Status</th>
              </tr>
            </thead>
            <tbody>
              {filtered.slice(0, 20).map((s, i) => (
                <tr key={s.station} className="border-b border-gray-800/50 hover:bg-gray-800/30 transition-colors">
                  <td className="py-2 pr-4 text-gray-600 text-xs">{i + 1}</td>
                  <td className="py-2 pr-4 text-gray-200 font-medium truncate max-w-[180px]">{s.station}</td>
                  <td className="py-2 pr-4 text-right font-semibold text-white">{s.ridership.toLocaleString()}</td>
                  <td className="py-2 pr-4 text-right text-gray-500">{s.avg_historical.toLocaleString()}</td>
                  <td className="py-2"><StatusBadge status={s.status} /></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </Card>
  );
}

// ─── Network Area Chart ─────────────────────────────────────────────────────

function NetworkDailyChart({ data, loading }: { data: DailyPoint[]; loading: boolean }) {
  return (
    <Card>
      <SectionTitle icon={TrendingUp} title="Network Daily Ridership (Aug–Sep 2025)" />
      {loading ? <Skeleton /> : (
        <ResponsiveContainer width="100%" height={220}>
          <AreaChart data={data} margin={{ left: -10, right: 10 }}>
            <defs>
              <linearGradient id="netGrad" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor={PURPLE} stopOpacity={0.4} />
                <stop offset="95%" stopColor={PURPLE} stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" />
            <XAxis dataKey="date" tick={{ fill: "#6b7280", fontSize: 11 }}
              tickFormatter={v => v.slice(5)} interval={6} />
            <YAxis tick={{ fill: "#6b7280", fontSize: 11 }}
              tickFormatter={v => `${(v / 1000).toFixed(0)}k`} />
            <Tooltip content={<DarkTooltip />} />
            <Area type="monotone" dataKey="total_ridership" name="Total Riders"
              stroke={PURPLE} fill="url(#netGrad)" strokeWidth={2} dot={false} />
          </AreaChart>
        </ResponsiveContainer>
      )}
    </Card>
  );
}

// ─── Hourly Profile ─────────────────────────────────────────────────────────

function HourlyProfileChart({ data, loading }: { data: HourlyPoint[]; loading: boolean }) {
  return (
    <Card>
      <SectionTitle icon={Clock} title="Network Hourly Profile" />
      {loading ? <Skeleton /> : (
        <ResponsiveContainer width="100%" height={220}>
          <BarChart data={data} margin={{ left: -10, right: 10 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" />
            <XAxis dataKey="hour" tick={{ fill: "#6b7280", fontSize: 11 }}
              tickFormatter={v => `${v}h`} />
            <YAxis tick={{ fill: "#6b7280", fontSize: 11 }} />
            <Tooltip content={<DarkTooltip />} />
            <Bar dataKey="avg_ridership" name="Avg Riders" radius={[4, 4, 0, 0]}>
              {data.map((entry, i) => (
                <Cell key={i}
                  fill={entry.avg_ridership > 600 ? RED : entry.avg_ridership > 350 ? ORANGE : GREEN}
                />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      )}
    </Card>
  );
}

// ─── Line Comparison ────────────────────────────────────────────────────────

function LineComparisonChart({ data, loading }: { data: LinePt[]; loading: boolean }) {
  return (
    <Card>
      <SectionTitle icon={Train} title="Purple Line vs Green Line – Hourly Avg" />
      {loading ? <Skeleton /> : (
        <ResponsiveContainer width="100%" height={220}>
          <LineChart data={data} margin={{ left: -10, right: 10 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" />
            <XAxis dataKey="hour" tick={{ fill: "#6b7280", fontSize: 11 }}
              tickFormatter={v => `${v}h`} />
            <YAxis tick={{ fill: "#6b7280", fontSize: 11 }} />
            <Tooltip content={<DarkTooltip />} />
            <Legend wrapperStyle={{ color: "#9ca3af", fontSize: 12 }} />
            <Line type="monotone" dataKey="purple_line_avg" name="Purple Line"
              stroke={PURPLE} strokeWidth={2} dot={false} />
            <Line type="monotone" dataKey="green_line_avg" name="Green Line"
              stroke={GREEN} strokeWidth={2} dot={false} />
          </LineChart>
        </ResponsiveContainer>
      )}
    </Card>
  );
}

// ─── Top Stations Bar ───────────────────────────────────────────────────────

function TopStationsChart({ data, loading }: { data: TopStation[]; loading: boolean }) {
  const truncate = (s: string) => s.length > 22 ? s.slice(0, 22) + "…" : s;
  return (
    <Card>
      <SectionTitle icon={BarChart2} title="Top 10 Busiest Stations" />
      {loading ? <Skeleton h={280} /> : (
        <ResponsiveContainer width="100%" height={280}>
          <BarChart data={data} layout="vertical" margin={{ left: 10, right: 30 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" horizontal={false} />
            <XAxis type="number" tick={{ fill: "#6b7280", fontSize: 11 }}
              tickFormatter={v => `${v}`} />
            <YAxis type="category" dataKey="station" tick={{ fill: "#d1d5db", fontSize: 10 }}
              tickFormatter={truncate} width={140} />
            <Tooltip content={<DarkTooltip />} />
            <Bar dataKey="avg_ridership" name="Avg Riders" fill={BLUE}
              radius={[0, 4, 4, 0]} />
          </BarChart>
        </ResponsiveContainer>
      )}
    </Card>
  );
}

// ─── AI Forecast Chart ──────────────────────────────────────────────────────

function ForecastChart({ data, loading }: { data: Forecast[]; loading: boolean }) {
  return (
    <Card>
      <SectionTitle icon={Brain} title="AI 24-Hour Crowd Forecast (from now)" />
      {loading ? <Skeleton /> : (
        <ResponsiveContainer width="100%" height={220}>
          <AreaChart data={data} margin={{ left: -10, right: 10 }}>
            <defs>
              <linearGradient id="foreGrad" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor={BLUE} stopOpacity={0.4} />
                <stop offset="95%" stopColor={BLUE} stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" />
            <XAxis dataKey="datetime" tick={{ fill: "#6b7280", fontSize: 11 }} />
            <YAxis tick={{ fill: "#6b7280", fontSize: 11 }} />
            <Tooltip content={<DarkTooltip />} />
            <Area type="monotone" dataKey="predicted_ridership" name="Predicted Riders"
              stroke={BLUE} fill="url(#foreGrad)" strokeWidth={2} dot={false} />
          </AreaChart>
        </ResponsiveContainer>
      )}
    </Card>
  );
}

// ─── Station Drill-down ─────────────────────────────────────────────────────

function StationDrilldown({
  stations, loading,
}: { stations: string[]; loading: boolean }) {
  const [selected, setSelected] = useState("");
  const [hourly, setHourly] = useState<HourlyPoint[]>([]);
  const [weekday, setWeekday] = useState<any[]>([]);
  const [predictions, setPredictions] = useState<any[]>([]);
  const [localLoading, setLocalLoading] = useState(false);

  const load = useCallback(async (s: string) => {
    if (!s) return;
    setLocalLoading(true);
    try {
      const [h, w, p] = await Promise.all([
        api.getStationHourly(s),
        api.getStationWeekday(s),
        api.getStationPredict(s, 6),
      ]);
      setHourly(h.data);
      setWeekday(w.data);
      setPredictions(p.predictions);
    } catch { /* ignore */ } finally {
      setLocalLoading(false);
    }
  }, []);

  useEffect(() => { if (selected) load(selected); }, [selected, load]);

  return (
    <Card>
      <div className="flex items-center justify-between mb-4">
        <SectionTitle icon={MapPin} title="Station Deep-Dive" />
        <select
          value={selected}
          onChange={e => setSelected(e.target.value)}
          className="bg-gray-800 border border-gray-700 text-sm text-gray-200 rounded-lg px-3 py-1.5 outline-none focus:border-violet-500"
        >
          <option value="">Select station…</option>
          {stations.map(s => <option key={s} value={s}>{s}</option>)}
        </select>
      </div>

      {!selected && (
        <div className="flex items-center justify-center h-32 text-gray-600 text-sm">
          ← Select a station to view detailed analytics
        </div>
      )}

      {selected && (
        <div className="space-y-6">
          {/* Hourly pattern */}
          <div>
            <p className="text-gray-400 text-xs mb-2 font-medium">Average Hourly Ridership</p>
            {localLoading ? <Skeleton /> : (
              <ResponsiveContainer width="100%" height={180}>
                <AreaChart data={hourly} margin={{ left: -10 }}>
                  <defs>
                    <linearGradient id="stGrad" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor={PURPLE} stopOpacity={0.4} />
                      <stop offset="95%" stopColor={PURPLE} stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" />
                  <XAxis dataKey="hour" tick={{ fill: "#6b7280", fontSize: 10 }}
                    tickFormatter={v => `${v}h`} />
                  <YAxis tick={{ fill: "#6b7280", fontSize: 10 }} />
                  <Tooltip content={<DarkTooltip />} />
                  <Area type="monotone" dataKey="avg_ridership" name="Avg Riders"
                    stroke={PURPLE} fill="url(#stGrad)" strokeWidth={2} dot={false} />
                </AreaChart>
              </ResponsiveContainer>
            )}
          </div>

          {/* Weekday */}
          <div>
            <p className="text-gray-400 text-xs mb-2 font-medium">Day-of-Week Pattern</p>
            {localLoading ? <Skeleton h={160} /> : (
              <ResponsiveContainer width="100%" height={160}>
                <BarChart data={weekday} margin={{ left: -10 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" />
                  <XAxis dataKey="day" tick={{ fill: "#6b7280", fontSize: 10 }} />
                  <YAxis tick={{ fill: "#6b7280", fontSize: 10 }} />
                  <Tooltip content={<DarkTooltip />} />
                  <Bar dataKey="avg_ridership" name="Avg Riders" fill={GREEN}
                    radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            )}
          </div>

          {/* AI Prediction */}
          <div>
            <p className="text-gray-400 text-xs mb-2 font-medium">AI Next 6-Hour Prediction</p>
            {localLoading ? <Skeleton h={160} /> : (
              <ResponsiveContainer width="100%" height={160}>
                <LineChart data={predictions} margin={{ left: -10 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" />
                  <XAxis dataKey="datetime" tick={{ fill: "#6b7280", fontSize: 10 }} />
                  <YAxis tick={{ fill: "#6b7280", fontSize: 10 }} />
                  <Tooltip content={<DarkTooltip />} />
                  <Line type="monotone" dataKey="predicted_ridership" name="Predicted"
                    stroke={ORANGE} strokeWidth={2} strokeDasharray="5 5"
                    dot={{ fill: ORANGE, r: 4 }} />
                </LineChart>
              </ResponsiveContainer>
            )}
            <div className="flex flex-wrap gap-2 mt-3">
              {predictions.map(p => (
                <div key={p.datetime}
                  className="text-xs bg-gray-800 rounded-lg px-2 py-1.5 border border-gray-700">
                  <span className="text-gray-500">{p.datetime.split(" ")[1]}</span>
                  <span className="text-white font-semibold ml-1.5">{Math.round(p.predicted_ridership).toLocaleString()}</span>
                  <StatusBadge status={p.status} />
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </Card>
  );
}

// ─── AI Insights Panel ──────────────────────────────────────────────────────

function InsightsPanel({ insights, loading }: { insights: Insight[]; loading: boolean }) {
  const iconMap: Record<string, { icon: React.ElementType; color: string }> = {
    info: { icon: Eye, color: BLUE },
    trend: { icon: TrendingUp, color: GREEN },
    alert: { icon: Zap, color: ORANGE },
    warning: { icon: AlertTriangle, color: RED },
  };

  return (
    <Card>
      <SectionTitle icon={Brain} title="AI Insights" />
      {loading ? (
        <div className="space-y-3">
          {[1, 2, 3, 4].map(i => <Skeleton key={i} h={70} />)}
        </div>
      ) : (
        <div className="space-y-3">
          {insights.map((ins, i) => {
            const { icon: Icon, color } = iconMap[ins.type] || iconMap.info;
            return (
              <div key={i} className="flex gap-3 p-3 rounded-xl bg-gray-800/50 border border-gray-700/50">
                <div className="shrink-0 mt-0.5 rounded-lg p-1.5" style={{ background: `${color}15` }}>
                  <Icon size={16} style={{ color }} />
                </div>
                <div>
                  <p className="text-sm font-semibold text-white">{ins.title}</p>
                  <p className="text-xs text-gray-400 mt-0.5 leading-relaxed">{ins.message}</p>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </Card>
  );
}

// ─── Anomaly Panel ──────────────────────────────────────────────────────────

function AnomalyPanel({ anomalies, loading }: { anomalies: Anomaly[]; loading: boolean }) {
  return (
    <Card>
      <SectionTitle icon={AlertTriangle} title="Anomaly Detection" />
      {loading ? <Skeleton h={200} /> : (
        anomalies.length === 0 ? (
          <div className="flex items-center justify-center h-20 text-gray-600 text-sm">
            No anomalies detected today ✓
          </div>
        ) : (
          <div className="space-y-2">
            {anomalies.slice(0, 8).map((a, i) => (
              <div key={i} className="flex items-center justify-between p-3 rounded-xl bg-gray-800/50 border border-gray-700/50">
                <div>
                  <p className="text-sm font-medium text-gray-200 truncate max-w-[180px]">{a.station}</p>
                  <p className="text-xs text-gray-500 mt-0.5">
                    Now: <span className="text-white font-semibold">{a.current_ridership.toLocaleString()}</span>
                    {" "}· Avg: {a.historical_avg.toLocaleString()}
                  </p>
                </div>
                <div className="text-right">
                  <span className={`text-sm font-bold ${a.type === "surge" ? "text-red-400" : "text-green-400"}`}>
                    {a.type === "surge" ? "▲" : "▼"} {Math.abs(a.z_score).toFixed(1)}σ
                  </span>
                  <p className="text-xs text-gray-500 capitalize">{a.type}</p>
                </div>
              </div>
            ))}
          </div>
        )
      )}
    </Card>
  );
}

// ─── Live Status Pie ────────────────────────────────────────────────────────

function LiveStatusPie({ data }: { data: LiveStation[] }) {
  const counts = { low: 0, moderate: 0, high: 0, critical: 0 };
  data.forEach(d => { counts[d.status] = (counts[d.status] || 0) + 1; });
  const pieData = Object.entries(counts).filter(([, v]) => v > 0).map(([k, v]) => ({
    name: k.charAt(0).toUpperCase() + k.slice(1),
    value: v,
    color: STATUS_COLOR[k],
  }));
  const total = data.length;

  return (
    <Card>
      <SectionTitle icon={Activity} title="Network Status Distribution" />
      <div className="flex items-center gap-4">
        <ResponsiveContainer width={160} height={160}>
          <PieChart>
            <Pie data={pieData} cx="50%" cy="50%" innerRadius={45} outerRadius={70}
              dataKey="value" strokeWidth={0}>
              {pieData.map((entry, i) => <Cell key={i} fill={entry.color} />)}
            </Pie>
            <Tooltip content={<DarkTooltip />} />
          </PieChart>
        </ResponsiveContainer>
        <div className="flex flex-col gap-2">
          {pieData.map((d, i) => (
            <div key={i} className="flex items-center gap-2 text-sm">
              <span className="w-2.5 h-2.5 rounded-full shrink-0" style={{ background: d.color }} />
              <span className="text-gray-400">{d.name}</span>
              <span className="text-white font-semibold ml-auto">
                {d.value} <span className="text-gray-600 font-normal">({Math.round(d.value / total * 100)}%)</span>
              </span>
            </div>
          ))}
        </div>
      </div>
    </Card>
  );
}

// ─── Header ─────────────────────────────────────────────────────────────────

function Header({
  lastUpdate, refreshAll, refreshing,
}: { lastUpdate: Date | null; refreshAll: () => void; refreshing: boolean }) {
  const now = new Date();
  return (
    <header className="border-b border-gray-800 bg-gray-900/80 backdrop-blur sticky top-0 z-50">
      <div className="max-w-screen-2xl mx-auto px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="rounded-xl bg-violet-600 p-2">
            <Train size={20} className="text-white" />
          </div>
          <div>
            <h1 className="text-lg font-bold text-white leading-tight">MetroFlow</h1>
            <p className="text-xs text-gray-500">AI Public Transit Intelligent Platform · Bengaluru Metro</p>
          </div>
        </div>
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2 text-xs text-gray-500">
            <span className="live-dot" />
            <span className="ml-3">Live · {now.toLocaleTimeString("en-IN")}</span>
          </div>
          {lastUpdate && (
            <span className="text-xs text-gray-600">
              Updated {lastUpdate.toLocaleTimeString("en-IN")}
            </span>
          )}
          <button
            onClick={refreshAll}
            disabled={refreshing}
            className="flex items-center gap-2 text-xs bg-violet-600 hover:bg-violet-700 text-white px-3 py-1.5 rounded-lg transition-colors disabled:opacity-50"
          >
            <RefreshCw size={13} className={refreshing ? "animate-spin" : ""} />
            Refresh
          </button>
        </div>
      </div>
    </header>
  );
}

// ─── Main Page ──────────────────────────────────────────────────────────────

export default function Home() {
  const [liveData, setLiveData] = useState<LiveStation[]>([]);
  const [networkDaily, setNetworkDaily] = useState<DailyPoint[]>([]);
  const [networkHourly, setNetworkHourly] = useState<HourlyPoint[]>([]);
  const [topStations, setTopStations] = useState<TopStation[]>([]);
  const [lineData, setLineData] = useState<LinePt[]>([]);
  const [insights, setInsights] = useState<Insight[]>([]);
  const [anomalies, setAnomalies] = useState<Anomaly[]>([]);
  const [forecast, setForecast] = useState<Forecast[]>([]);
  const [stationList, setStationList] = useState<string[]>([]);

  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null);
  const [apiError, setApiError] = useState(false);

  // Summary stats
  const totalLive = liveData.reduce((s, d) => s + d.ridership, 0);
  const criticalCount = liveData.filter(d => d.status === "critical").length;
  const peakStation = liveData[0]?.station ?? "—";

  const fetchAll = useCallback(async (isRefresh = false) => {
    if (isRefresh) setRefreshing(true);
    setApiError(false);
    try {
      const [live, nd, nh, top, line, ins, anom, fore, stList] = await Promise.all([
        api.getLive(),
        api.getNetworkDaily(),
        api.getNetworkHourly(),
        api.getTopStations(10),
        api.getLineComparison(),
        api.getInsights(),
        api.getAnomalies(),
        api.getForecast(),
        api.getStations(),
      ]);
      setLiveData(live.data);
      setNetworkDaily(nd.data);
      setNetworkHourly(nh.data);
      setTopStations(top.data);
      setLineData(line.data);
      setInsights(ins.insights);
      setAnomalies(anom.anomalies);
      setForecast(fore.forecasts);
      setStationList(stList.stations);
      setLastUpdate(new Date());
    } catch {
      setApiError(true);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => { fetchAll(); }, [fetchAll]);

  // Auto-refresh live data every 30 seconds
  useEffect(() => {
    const t = setInterval(() => {
      api.getLive().then(r => setLiveData(r.data)).catch(() => {});
    }, 30000);
    return () => clearInterval(t);
  }, []);

  return (
    <div className="min-h-screen bg-gray-950">
      <Header lastUpdate={lastUpdate} refreshAll={() => fetchAll(true)} refreshing={refreshing} />

      <main className="max-w-screen-2xl mx-auto px-6 py-6 space-y-6">

        {/* API Error Banner */}
        {apiError && (
          <div className="glass border-red-500/30 bg-red-950/20 p-4 rounded-xl text-sm text-red-400 flex items-center gap-3">
            <AlertTriangle size={16} />
            <span>Cannot connect to MetroFlow backend. Make sure FastAPI is running on <code className="font-mono bg-red-900/30 px-1 rounded">localhost:8000</code></span>
          </div>
        )}

        {/* KPI Stats */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          <StatCard label="Live Network Riders" value={totalLive.toLocaleString()}
            icon={Users} color={PURPLE} sub="Across all stations" />
          <StatCard label="Critical Stations" value={criticalCount}
            icon={AlertTriangle} color={RED} sub="Require attention now" />
          <StatCard label="Top Station" value={peakStation.split(",")[0]}
            icon={MapPin} color={ORANGE} sub="Highest live ridership" />
          <StatCard label="Total Stations" value={stationList.length || 84}
            icon={Train} color={GREEN} sub="Bengaluru Metro Network" />
        </div>

        {/* Row 1: Live Table + Status Pie */}
        <div className="grid grid-cols-1 xl:grid-cols-3 gap-4">
          <div className="xl:col-span-2">
            <LiveTable data={liveData} loading={loading} />
          </div>
          <LiveStatusPie data={liveData} />
        </div>

        {/* Row 2: Network Charts */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          <NetworkDailyChart data={networkDaily} loading={loading} />
          <HourlyProfileChart data={networkHourly} loading={loading} />
        </div>

        {/* Row 3: Line Comparison + Forecast */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          <LineComparisonChart data={lineData} loading={loading} />
          <ForecastChart data={forecast} loading={loading} />
        </div>

        {/* Row 4: Top Stations + AI Insights */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          <TopStationsChart data={topStations} loading={loading} />
          <InsightsPanel insights={insights} loading={loading} />
        </div>

        {/* Row 5: Anomalies + Station Drilldown */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          <AnomalyPanel anomalies={anomalies} loading={loading} />
          <StationDrilldown stations={stationList} loading={loading} />
        </div>

        {/* Footer */}
        <footer className="text-center text-xs text-gray-700 py-4 border-t border-gray-800">
          MetroFlow AI Platform · Bengaluru Metro Dataset Aug–Sep 2025 · 92,280 records · {stationList.length} stations
        </footer>
      </main>
    </div>
  );
}
