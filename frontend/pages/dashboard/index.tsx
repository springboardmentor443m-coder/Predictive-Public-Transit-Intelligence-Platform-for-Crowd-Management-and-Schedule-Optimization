import { useCallback, useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { AlertTriangle, Building2, Gauge, Radio, Search, Sparkles, Timer, TrainFront } from "lucide-react";
import {
  Area, AreaChart, Bar, BarChart, CartesianGrid, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis,
} from "recharts";
import DashboardLayout from "../../components/DashboardLayout";
import InsightPanel from "../../components/InsightPanel";
import KpiCard from "../../components/KpiCard";
import StatusBadge, { congestionColor } from "../../components/StatusBadge";
import { withAuth, useAuth } from "../../lib/auth";
import { useToast } from "../../components/ToastContext";
import api from "../../lib/api";
import { getSocket } from "../../lib/socket";
import type { AnalyticsOverview, TrafficSeriesPoint, TrainLive, LiveCrowdSnapshot, AlertItem, AiInsights, ModelInfo } from "../../lib/types";

function Overview() {
  const { user } = useAuth();
  const { showToast } = useToast();
  const [overview, setOverview] = useState<AnalyticsOverview | null>(null);
  const [live, setLive] = useState<LiveCrowdSnapshot[]>([]);
  const [trains, setTrains] = useState<TrainLive[]>([]);
  const [traffic, setTraffic] = useState<TrafficSeriesPoint[]>([]);
  const [alerts, setAlerts] = useState<AlertItem[]>([]);
  const [insights, setInsights] = useState<AiInsights | null>(null);
  const [modelInfo, setModelInfo] = useState<ModelInfo | null>(null);
  const [connected, setConnected] = useState(false);
  const [search, setSearch] = useState("");
  const [lineFilter, setLineFilter] = useState("all");

  const loadAll = useCallback(async () => {
    try {
      const [ov, lv, trs, tr, al, ins, mi] = await Promise.all([
        api.get<AnalyticsOverview>("/analytics/overview"),
        api.get<LiveCrowdSnapshot[]>("/crowd/live"),
        api.get<TrainLive[]>("/trains/live"),
        api.get<TrafficSeriesPoint[]>("/analytics/traffic?hours=24"),
        api.get<AlertItem[]>("/alerts?limit=6"),
        api.get<AiInsights>("/analytics/insights").catch(() => null),
        api.get<ModelInfo>("/predictions/model-info").catch(() => null),
      ]);
      setOverview(ov.data);
      setLive(lv.data);
      setTrains(trs.data);
      setTraffic(tr.data.map((t) => ({ ...t, label: `${String(t.hour).padStart(2, "0")}:00` })));
      setAlerts(al.data);
      if (ins) setInsights(ins.data);
      if (mi) setModelInfo(mi.data);
    } catch {}
  }, []);

  useEffect(() => {
    loadAll();
    const iv = setInterval(loadAll, 25000);
    return () => clearInterval(iv);
  }, [loadAll]);

  useEffect(() => {
    let s: ReturnType<typeof getSocket> | undefined;
    try {
      s = getSocket();
      s.on("connect", () => setConnected(true));
      s.on("disconnect", () => setConnected(false));
      s.on("crowd_update", (snap: LiveCrowdSnapshot) => {
        setLive((prev) => {
          const idx = prev.findIndex((p) => p.station_id === snap.station_id);
          if (idx === -1) return [...prev, snap];
          const next = [...prev];
          next[idx] = snap;
          return next;
        });
      });
      s.on("train_update", (tr: TrainLive) => {
        setTrains((prev) => {
          const idx = prev.findIndex((t) => t.train_id === tr.train_id);
          if (idx === -1) return [...prev, tr];
          const next = [...prev];
          next[idx] = tr;
          return next;
        });
      });
      s.on("alert", (newAlert: AlertItem) => {
        showToast(newAlert.title || "New system alert triggered", "warning");
        loadAll();
      });
    } catch {}
    return () => {
      if (s) {
        s.off("connect");
        s.off("disconnect");
        s.off("crowd_update");
        s.off("train_update");
        s.off("alert");
      }
    };
  }, [loadAll, showToast]);

  const filteredLive = useMemo(() => {
    return live.filter((s) => {
      const matchesSearch = s.station_name.toLowerCase().includes(search.toLowerCase()) || s.station_id.toLowerCase().includes(search.toLowerCase());
      const matchesLine = lineFilter === "all" || s.line.toLowerCase() === lineFilter.toLowerCase();
      return matchesSearch && matchesLine;
    });
  }, [live, search, lineFilter]);

  const topCongested = useMemo(() => [...live].sort((a, b) => b.occupancy_pct - a.occupancy_pct).slice(0, 8), [live]);

  const chartData = topCongested.map((s) => ({
    name: s.station_name.length > 13 ? s.station_name.slice(0, 12) + "…" : s.station_name,
    occupancy: s.occupancy_pct,
    fill: congestionColor(s.occupancy_pct),
  }));

  const avgOcc = overview?.avg_occupancy_pct ?? 0;
  const inServiceTrains = trains.filter((t) => ["in_transit", "at_station", "awaiting_departure", "delayed"].includes(t.status));
  const delayedTrains = trains.filter((t) => t.status === "delayed");

  return (
    <DashboardLayout title="Operations Control Overview" subtitle="Real-time transit network status & AI telematics">
      {/* Hero Control Console Banner */}
      <div className="hero-gradient relative overflow-hidden rounded-2xl border border-slate-800 p-6 sm:p-8 text-white shadow-2xl">
        <div className="absolute -right-20 -top-20 h-64 w-64 rounded-full bg-brand-500/20 blur-3xl animate-pulse-slow" />
        <div className="absolute -bottom-24 left-1/3 h-56 w-56 rounded-full bg-emerald-400/20 blur-3xl" />

        <div className="relative z-10 flex flex-wrap items-center justify-between gap-6">
          <div className="space-y-2 max-w-2xl">
            <div className="flex items-center gap-2">
              <span className="inline-flex items-center gap-1.5 rounded-full bg-brand-500/20 px-3 py-1 text-xs font-extrabold text-brand-300 border border-brand-400/30">
                <Sparkles className="h-3.5 w-3.5" /> Operations Active
              </span>
              <span className="text-xs font-mono text-slate-400">
                {new Date().toLocaleDateString([], { weekday: "short", month: "short", day: "numeric" })} · Peak {overview ? `${String(overview.predicted_peak_hour).padStart(2, "0")}:00` : "--"}
              </span>
            </div>

            <h2 className="text-3xl font-extrabold tracking-tight sm:text-4xl text-white">
              Network operating at <span className="text-brand-400 font-mono">{avgOcc}%</span> occupancy
            </h2>

            <p className="text-sm text-slate-300 leading-relaxed">
              Monitoring <span className="font-bold text-white">{overview?.total_stations ?? 10} stations</span> across Red, Blue & Green lines ·{" "}
              <span className="font-bold text-emerald-400">{overview?.on_time_pct ?? 96}% on-time performance</span> ·{" "}
              <span className="font-bold text-white">{inServiceTrains.length} trains in service</span>
              {delayedTrains.length > 0 && <span className="text-amber-300"> ({delayedTrains.length} delayed)</span>} · AI Model{" "}
              <span className="font-mono text-brand-300 font-bold">{modelInfo?.city || "hangzhou"} ({modelInfo?.crowd?.algorithm || "XGBoost"})</span> serving live predictions.
            </p>
          </div>

          <div className="flex flex-col sm:flex-row items-start sm:items-center gap-3">
            <span
              className={`inline-flex items-center gap-2 rounded-xl px-3.5 py-2 text-xs font-bold border ${
                connected
                  ? "bg-emerald-500/15 text-emerald-300 border-emerald-500/30"
                  : "bg-amber-500/15 text-amber-300 border-amber-500/30"
              }`}
            >
              <Radio className={`h-4 w-4 ${connected ? "animate-pulse text-emerald-400" : ""}`} />
              {connected ? "Socket.IO Streaming Live" : "Polling 25s Backup"}
            </span>
            <Link
              href="/dashboard/crowd"
              className="btn-primary text-xs py-2.5 px-4 font-extrabold shadow-lg"
            >
              Open Live Network Map →
            </Link>
          </div>
        </div>
      </div>

      {/* KPI Cards Grid */}
      <div className="mt-5 grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <KpiCard
          label="Network Occupancy"
          value={overview ? `${overview.current_overall_occupancy_pct}%` : "—"}
          icon={Gauge}
          accent="brand"
          sub={`${live.filter((s) => s.congestion_level === "critical").length} critical stations`}
        />
        <KpiCard
          label="Active Stations"
          value={overview?.total_stations ?? "—"}
          icon={Building2}
          accent="sky"
          sub="Red · Blue · Green lines active"
        />
        <KpiCard
          label="Fleet Trains Active"
          value={overview?.total_trains ?? "—"}
          icon={TrainFront}
          accent="emerald"
          sub={`${overview?.on_time_pct ?? "—"}% on-time service`}
        />
        <KpiCard
          label="Active Alerts"
          value={overview?.active_alerts ?? "—"}
          icon={AlertTriangle}
          accent={(overview?.active_alerts ?? 0) > 0 ? "rose" : "emerald"}
          sub={overview?.active_alerts ? "Immediate operator review needed" : "Network operating smoothly"}
        />
      </div>

      {/* Live Fleet Strip — realtime train telemetry */}
      <div className="card card-pad mt-5 border-slate-800">
        <div className="mb-3 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <span className="flex h-8 w-8 items-center justify-center rounded-xl bg-emerald-500/15 border border-emerald-500/30 text-emerald-400">
              <TrainFront className="h-4 w-4" />
            </span>
            <div>
              <h3 className="font-extrabold tracking-tight text-white">Live Fleet Position</h3>
              <p className="text-[11px] text-slate-400">Position of each train between stations, streamed via Socket.IO</p>
            </div>
          </div>
          <Link href="/dashboard/trains" className="text-xs font-extrabold text-brand-400 hover:text-brand-300">
            Open Train Monitor →
          </Link>
        </div>

        <div className="flex gap-3 overflow-x-auto pb-2 scroll-thin">
          {trains.map((t) => {
            const inService = ["in_transit", "at_station", "awaiting_departure", "delayed"].includes(t.status);
            const barColor = t.status === "delayed" ? "#f59e0b"
              : t.line === "Red" ? "#f43f5e"
              : t.line === "Blue" ? "#3b82f6"
              : "#10b981";
            return (
              <Link
                key={t.train_id}
                href="/dashboard/trains"
                className="w-52 shrink-0 rounded-2xl border border-slate-800 bg-slate-950/70 p-3 transition hover:border-slate-600"
              >
                <div className="flex items-center justify-between">
                  <p className="text-xs font-extrabold text-white">{t.train_id}</p>
                  <StatusBadge value={!inService ? (t.status === "in_depot" ? "on_time" : "low") : t.status === "delayed" ? "critical" : "on_time"} />
                </div>
                <p className="mt-0.5 text-[10px] font-bold uppercase tracking-wider text-slate-400">{t.line} Line</p>
                {inService ? (
                  <>
                    <div className="mt-2.5 h-1.5 overflow-hidden rounded-full bg-slate-800">
                      <div className="h-full rounded-full transition-all duration-1000" style={{ width: `${t.position_pct || 0}%`, backgroundColor: barColor }} />
                    </div>
                    <p className="mt-1.5 flex items-center justify-between text-[10px] font-mono text-slate-400">
                      <span className="max-w-[45%] truncate">{t.current_station?.name || "Depot"}</span>
                      <span className="text-slate-500">→</span>
                      <span className="max-w-[45%] truncate">{t.next_station?.name || "—"}</span>
                    </p>
                  </>
                ) : (
                  <p className="mt-2.5 text-[10px] font-bold uppercase tracking-wide text-slate-500">{t.status.replaceAll("_", " ")}</p>
                )}
              </Link>
            );
          })}
          {trains.length === 0 && <p className="py-6 text-center text-xs text-slate-500">Waiting for fleet telemetry...</p>}
        </div>
      </div>

      {/* AI Operational Insights Component */}
      <div className="mt-5">
        <InsightPanel insights={insights} />
      </div>

      {/* Main Live Density Feed & Recent Alerts Grid */}
      <div className="mt-5 grid grid-cols-1 gap-5 xl:grid-cols-3">
        {/* Live Station Density Feed */}
        <div className="card xl:col-span-2 border-slate-800">
          <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-800 px-5 py-4">
            <div>
              <h3 className="font-extrabold tracking-tight text-white">Live Station Density Telemetry</h3>
              <p className="text-xs text-slate-400">Streamed gate counters & ridership sensors</p>
            </div>

            <div className="flex flex-wrap items-center gap-2">
              <div className="relative">
                <Search className="absolute left-2.5 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-slate-500" />
                <input
                  type="text"
                  placeholder="Search station..."
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  className="input py-1.5 pl-8 text-xs w-44"
                />
              </div>

              <select
                value={lineFilter}
                onChange={(e) => setLineFilter(e.target.value)}
                className="input py-1.5 text-xs w-auto"
              >
                <option value="all">All Lines</option>
                <option value="red">Red Line</option>
                <option value="blue">Blue Line</option>
                <option value="green">Green Line</option>
              </select>
            </div>
          </div>

          <div className="divide-y divide-slate-800/80 max-h-[460px] overflow-y-auto scroll-thin">
            {filteredLive.length === 0 && (
              <p className="px-5 py-12 text-center text-sm text-slate-500">No stations match search criteria.</p>
            )}
            {filteredLive.map((s) => (
              <div key={s.station_id} className="flex items-center gap-4 px-5 py-3.5 transition hover:bg-slate-850/60">
                <div className="min-w-0 flex-1">
                  <div className="flex items-baseline justify-between gap-2">
                    <p className="truncate text-sm font-extrabold text-white">
                      {s.station_name} <span className="ml-1.5 text-[10px] font-mono font-bold uppercase text-slate-400">({s.line} Line)</span>
                    </p>
                    <p className="text-xs font-mono text-slate-400">
                      In: <span className="font-bold text-sky-400">{s.inflow_rate}</span>/m · Out: <span className="font-bold text-emerald-400">{s.outflow_rate}</span>/m
                    </p>
                  </div>
                  <div className="mt-2 h-2 overflow-hidden rounded-full bg-slate-800">
                    <div
                      className="h-full rounded-full transition-all duration-700"
                      style={{
                        width: `${Math.min(100, s.occupancy_pct)}%`,
                        backgroundColor: congestionColor(s.occupancy_pct),
                      }}
                    />
                  </div>
                </div>
                <div className="w-16 text-right">
                  <p className="text-sm font-extrabold font-mono text-white">{s.occupancy_pct}%</p>
                </div>
                <StatusBadge value={s.congestion_level} />
              </div>
            ))}
          </div>
        </div>

        {/* Recent Alerts Panel */}
        <div className="card border-slate-800 flex flex-col">
          <div className="flex items-center justify-between border-b border-slate-800 px-5 py-4">
            <h3 className="font-extrabold tracking-tight text-white">Recent Dispatch Alerts</h3>
            <Link href="/dashboard/alerts" className="text-xs font-extrabold text-brand-400 hover:text-brand-300">
              View Feed →
            </Link>
          </div>
          <div className="divide-y divide-slate-800/80 flex-1 overflow-y-auto max-h-[460px] scroll-thin">
            {alerts.length === 0 && <p className="px-5 py-12 text-center text-sm text-slate-500">No recent alerts. Network calm.</p>}
            {alerts.map((a) => (
              <div key={a.id} className="flex gap-3 px-5 py-3.5 hover:bg-slate-850/60 transition">
                <span
                  className={`mt-0.5 flex h-9 w-9 shrink-0 items-center justify-center rounded-xl border ${
                    a.severity === "critical" || a.type === "emergency"
                      ? "bg-rose-500/20 text-rose-400 border-rose-500/40"
                      : a.severity === "high"
                      ? "bg-orange-500/20 text-orange-400 border-orange-500/40"
                      : "bg-amber-500/20 text-amber-400 border-amber-500/40"
                  }`}
                >
                  <AlertTriangle className="h-4 w-4" />
                </span>
                <div className="min-w-0 flex-1">
                  <p className="truncate text-xs font-extrabold text-white">{a.title}</p>
                  <p className="line-clamp-2 text-xs text-slate-400 mt-0.5 leading-relaxed">{a.message}</p>
                  <p className="mt-1 text-[10px] font-mono uppercase tracking-wide text-slate-500">
                    {new Date(a.created_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })} · {a.type}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Analytics Charts Grid */}
      <div className="mt-5 grid grid-cols-1 gap-5 xl:grid-cols-2">
        {/* Most Congested Bar Chart */}
        <div className="card card-pad border-slate-800">
          <h3 className="font-extrabold tracking-tight text-white">Most Congested Stations</h3>
          <p className="mb-4 text-xs text-slate-400">Current occupancy percentage by station</p>
          <ResponsiveContainer width="100%" height={280}>
            <BarChart data={chartData} layout="vertical" margin={{ left: 10, right: 16 }}>
              <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="#1e293b" />
              <XAxis type="number" domain={[0, 100]} unit="%" tick={{ fontSize: 11, fill: "#94a3b8" }} stroke="#334155" />
              <YAxis type="category" dataKey="name" width={110} tick={{ fontSize: 11, fill: "#e2e8f0" }} stroke="#334155" />
              <Tooltip
                formatter={(v) => [`${v}%`, "Occupancy"]}
                contentStyle={{ backgroundColor: "#0f172a", borderColor: "#334155", borderRadius: 12, fontSize: 12, color: "#fff" }}
              />
              <Bar dataKey="occupancy" radius={[0, 8, 8, 0]} barSize={16}>
                {chartData.map((d) => (
                  <Cell key={d.name} fill={d.fill} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* 24h Traffic Trend Area Chart */}
        <div className="card card-pad border-slate-800">
          <h3 className="font-extrabold tracking-tight text-white">Network Traffic Trend — 24 Hours</h3>
          <p className="mb-4 text-xs text-slate-400">Passenger throughput volume (thousands per hour)</p>
          <ResponsiveContainer width="100%" height={280}>
            <AreaChart data={traffic} margin={{ left: 0, right: 12 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
              <XAxis dataKey="label" tick={{ fontSize: 10, fill: "#94a3b8" }} interval={2} stroke="#334155" />
              <YAxis tick={{ fontSize: 11, fill: "#94a3b8" }} stroke="#334155" unit="k" />
              <Tooltip contentStyle={{ backgroundColor: "#0f172a", borderColor: "#334155", borderRadius: 12, fontSize: 12, color: "#fff" }} />
              <Area type="monotone" dataKey="passenger_k" name="Passengers (k)" stroke="#3b82f6" strokeWidth={3} fill="rgba(37, 99, 235, 0.2)" />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Network Summary Capsule Footer */}
      <div className="mt-5 flex flex-wrap items-center justify-between gap-6 rounded-2xl border border-slate-800 bg-slate-900/90 px-6 py-4 backdrop-blur-xl">
        <div className="flex items-center gap-4">
          <span className="flex h-11 w-11 items-center justify-center rounded-2xl bg-emerald-500/15 border border-emerald-500/30 text-emerald-400">
            <Timer className="h-5 w-5" />
          </span>
          <div>
            <p className="text-[11px] font-extrabold uppercase tracking-[0.14em] text-slate-400">On-time Performance</p>
            <p className="text-xl font-extrabold font-mono text-white">{overview ? `${overview.on_time_pct}%` : "—"}</p>
          </div>
        </div>

        <div className="flex items-center gap-4">
          <span className="flex h-11 w-11 items-center justify-center rounded-2xl bg-brand-500/15 border border-brand-500/30 text-brand-400">
            <Gauge className="h-5 w-5" />
          </span>
          <div>
            <p className="text-[11px] font-extrabold uppercase tracking-[0.14em] text-slate-400">Average Density</p>
            <p className="text-xl font-extrabold font-mono text-white">{overview ? `${overview.avg_occupancy_pct}%` : "—"}</p>
          </div>
        </div>

        <p className="max-w-xs text-right text-[11px] text-slate-400 leading-relaxed">
          Trained on real-world Kaggle datasets (Hangzhou/Seoul/NJ Transit). <span className="font-bold text-white">Zero CCTV / privacy risks.</span>
        </p>
      </div>
    </DashboardLayout>
  );
}

export default withAuth(Overview);