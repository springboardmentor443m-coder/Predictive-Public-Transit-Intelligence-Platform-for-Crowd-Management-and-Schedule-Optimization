import { useCallback, useEffect, useMemo, useState } from "react";
import Link from "next/link";
import {
  AlertTriangle,
  Building2,
  Gauge,
  Timer,
  TrainFront,
  Users,
} from "lucide-react";
import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import DashboardLayout from "../../components/DashboardLayout";
import KpiCard from "../../components/KpiCard";
import StatusBadge, { congestionColor } from "../../components/StatusBadge";
import { withAuth } from "../../lib/auth";
import api from "../../lib/api";
import { getSocket } from "../../lib/socket";

function Overview() {
  const [overview, setOverview] = useState(null);
  const [live, setLive] = useState([]);
  const [traffic, setTraffic] = useState([]);
  const [alerts, setAlerts] = useState([]);
  const [connected, setConnected] = useState(false);

  const loadAll = useCallback(async () => {
    try {
      const [ov, lv, tr, al] = await Promise.all([
        api.get("/analytics/overview"),
        api.get("/crowd/live"),
        api.get("/analytics/traffic?hours=24"),
        api.get("/alerts?limit=6"),
      ]);
      setOverview(ov.data);
      setLive(lv.data);
      setTraffic(tr.data.map((t) => ({ ...t, label: `${String(t.hour).padStart(2, "0")}:00` })));
      setAlerts(al.data);
    } catch {}
  }, []);

  useEffect(() => {
    loadAll();
    const iv = setInterval(loadAll, 30000);
    return () => clearInterval(iv);
  }, [loadAll]);

  useEffect(() => {
    let s;
    try {
      s = getSocket();
      s.on("connect", () => setConnected(true));
      s.on("disconnect", () => setConnected(false));
      s.on("crowd_update", (snap) => {
        setLive((prev) => {
          const idx = prev.findIndex((p) => p.station_id === snap.station_id);
          if (idx === -1) return prev;
          const next = [...prev];
          next[idx] = snap;
          return next;
        });
      });
      s.on("alert", () => loadAll());
    } catch {}
    return () => {
      if (s) {
        s.off("connect");
        s.off("disconnect");
        s.off("crowd_update");
        s.off("alert");
      }
    };
  }, [loadAll]);

  const topCongested = useMemo(
    () => [...live].sort((a, b) => b.occupancy_pct - a.occupancy_pct).slice(0, 8),
    [live]
  );

  const chartData = topCongested.map((s) => ({
    name: s.station_name.length > 14 ? s.station_name.slice(0, 13) + "…" : s.station_name,
    occupancy: s.occupancy_pct,
    fill: congestionColor(s.occupancy_pct),
  }));

  return (
    <DashboardLayout
      title="Operations Overview"
      subtitle="Real-time network status across all metro lines"
    >
      {/* KPI row */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <KpiCard
          label="Network Occupancy"
          value={overview ? `${overview.current_overall_occupancy_pct}%` : "—"}
          icon={Gauge}
          accent="brand"
        />
        <KpiCard
          label="Active Stations"
          value={overview?.total_stations ?? "—"}
          icon={Building2}
          accent="sky"
        />
        <KpiCard
          label="Fleet Active"
          value={overview?.total_trains ?? "—"}
          icon={TrainFront}
          accent="emerald"
        />
        <KpiCard
          label="Open Alerts"
          value={overview?.active_alerts ?? "—"}
          icon={AlertTriangle}
          accent={overview?.active_alerts > 0 ? "rose" : "emerald"}
        />
      </div>

      <div className="mt-4 grid grid-cols-1 gap-4 xl:grid-cols-3">
        {/* Live station board */}
        <div className="card xl:col-span-2">
          <div className="flex items-center justify-between border-b border-slate-200 px-5 py-4">
            <div>
              <h3 className="font-semibold text-slate-900">Live Station Density</h3>
              <p className="text-xs text-slate-500">
                Streaming via Socket.IO · auto-refresh 30s fallback
              </p>
            </div>
            <span
              className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-semibold ring-1 ${
                connected
                  ? "bg-emerald-50 text-emerald-700 ring-emerald-200"
                  : "bg-slate-100 text-slate-500 ring-slate-200"
              }`}
            >
              <span className={`h-1.5 w-1.5 rounded-full ${connected ? "bg-emerald-500" : "bg-slate-400"}`} />
              {connected ? "Socket connected" : "Polling"}
            </span>
          </div>
          <div className="divide-y divide-slate-100">
            {live.length === 0 && (
              <p className="px-5 py-10 text-center text-sm text-slate-400">Waiting for live data…</p>
            )}
            {live.map((s) => (
              <div key={s.station_id} className="flex items-center gap-4 px-5 py-3">
                <div className="min-w-0 flex-1">
                  <div className="flex items-baseline justify-between gap-2">
                    <p className="truncate text-sm font-semibold text-slate-800">{s.station_name}</p>
                    <p className="text-xs tabular-nums text-slate-500">
                      {s.inflow_rate}/min in · {s.outflow_rate}/min out
                    </p>
                  </div>
                  <div className="mt-1.5 h-2 overflow-hidden rounded-full bg-slate-100">
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
                  <p className="text-sm font-bold tabular-nums text-slate-800">{s.occupancy_pct}%</p>
                </div>
                <StatusBadge value={s.congestion_level} />
              </div>
            ))}
          </div>
        </div>

        {/* Alerts feed */}
        <div className="card">
          <div className="flex items-center justify-between border-b border-slate-200 px-5 py-4">
            <h3 className="font-semibold text-slate-900">Recent Alerts</h3>
            <Link href="/dashboard/alerts" className="text-xs font-semibold text-brand-600 hover:text-brand-700">
              View all →
            </Link>
          </div>
          <div className="divide-y divide-slate-100">
            {alerts.length === 0 && (
              <p className="px-5 py-10 text-center text-sm text-slate-400">No alerts. Network is calm.</p>
            )}
            {alerts.map((a) => (
              <div key={a.id} className="flex gap-3 px-5 py-3">
                <span
                  className={`mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-lg ${
                    a.severity === "critical" || a.type === "emergency"
                      ? "bg-rose-50 text-rose-600"
                      : a.severity === "high"
                      ? "bg-orange-50 text-orange-600"
                      : "bg-amber-50 text-amber-600"
                  }`}
                >
                  <AlertTriangle className="h-4 w-4" />
                </span>
                <div className="min-w-0">
                  <p className="truncate text-sm font-semibold text-slate-800">{a.title}</p>
                  <p className="line-clamp-2 text-xs text-slate-500">{a.message}</p>
                  <p className="mt-1 text-[11px] uppercase tracking-wide text-slate-400">
                    {new Date(a.created_at).toLocaleTimeString()} · {a.type}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="mt-4 grid grid-cols-1 gap-4 xl:grid-cols-2">
        {/* Congestion bar chart */}
        <div className="card card-pad">
          <h3 className="font-semibold text-slate-900">Most Congested Stations</h3>
          <p className="mb-4 text-xs text-slate-500">Current occupancy percentage</p>
          <ResponsiveContainer width="100%" height={280}>
            <BarChart data={chartData} layout="vertical" margin={{ left: 8, right: 16 }}>
              <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="#e2e8f0" />
              <XAxis type="number" domain={[0, 100]} unit="%" tick={{ fontSize: 11 }} stroke="#94a3b8" />
              <YAxis type="category" dataKey="name" width={110} tick={{ fontSize: 11 }} stroke="#94a3b8" />
              <Tooltip formatter={(v) => [`${v}%`, "Occupancy"]} contentStyle={{ borderRadius: 8, fontSize: 12 }} />
              <Bar dataKey="occupancy" radius={[0, 6, 6, 0]} barSize={16} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Traffic area chart */}
        <div className="card card-pad">
          <h3 className="font-semibold text-slate-900">Passenger Traffic — Last 24h</h3>
          <p className="mb-4 text-xs text-slate-500">Estimated passengers (thousands) per hour</p>
          <ResponsiveContainer width="100%" height={280}>
            <AreaChart data={traffic} margin={{ left: -12, right: 12 }}>
              <defs>
                <linearGradient id="occGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#3382fc" stopOpacity={0.35} />
                  <stop offset="100%" stopColor="#3382fc" stopOpacity={0.02} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
              <XAxis dataKey="label" tick={{ fontSize: 10 }} interval={2} stroke="#94a3b8" />
              <YAxis tick={{ fontSize: 11 }} stroke="#94a3b8" unit="k" />
              <Tooltip contentStyle={{ borderRadius: 8, fontSize: 12 }} />
              <Area
                type="monotone"
                dataKey="passenger_k"
                name="Passengers (k)"
                stroke="#3382fc"
                strokeWidth={2}
                fill="url(#occGrad)"
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Punctuality strip */}
      <div className="card card-pad mt-4 flex flex-wrap items-center gap-6">
        <div className="flex items-center gap-3">
          <span className="flex h-10 w-10 items-center justify-center rounded-xl bg-emerald-50 text-emerald-600">
            <Timer className="h-5 w-5" />
          </span>
          <div>
            <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">On-time Performance</p>
            <p className="text-xl font-bold text-slate-900">{overview ? `${overview.on_time_pct}%` : "—"}</p>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <span className="flex h-10 w-10 items-center justify-center rounded-xl bg-brand-50 text-brand-600">
            <Users className="h-5 w-5" />
          </span>
          <div>
            <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Avg Occupancy</p>
            <p className="text-xl font-bold text-slate-900">{overview ? `${overview.avg_occupancy_pct}%` : "—"}</p>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <span className="flex h-10 w-10 items-center justify-center rounded-xl bg-amber-50 text-amber-600">
            <AlertTriangle className="h-5 w-5" />
          </span>
          <div>
            <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Predicted Peak Hour</p>
            <p className="text-xl font-bold text-slate-900">
              {overview ? `${String(overview.predicted_peak_hour).padStart(2, "0")}:00` : "—"}
            </p>
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
}

export default withAuth(Overview);
