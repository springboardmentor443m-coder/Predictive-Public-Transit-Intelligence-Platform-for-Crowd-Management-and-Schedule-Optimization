import { useCallback, useEffect, useMemo, useState, type FormEvent } from "react";
import { ArrowDown, ArrowUp, Download, Loader2, Radio, Send, Sparkles } from "lucide-react";
import {
  Area,
  AreaChart,
  CartesianGrid,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import DashboardLayout from "../../components/DashboardLayout";
import HeatmapGrid from "../../components/HeatmapGrid";
import MetroMap from "../../components/MetroMap";
import StatusBadge, { congestionColor } from "../../components/StatusBadge";
import { withAuth, useAuth } from "../../lib/auth";
import { useToast } from "../../components/ToastContext";
import api from "../../lib/api";
import { getSocket, joinStationRoom } from "../../lib/socket";
import { downloadCsv } from "../../lib/csv";
import type { Station, LiveCrowdSnapshot, StationHeatmapPoint, StationHistoryPoint, ModelInfo } from "../../lib/types";

interface HistoryRow {
  time: string;
  full: string;
  entries: number;
  exits: number;
  occupancy: number;
}

function CrowdMonitoring() {
  const { hasRole } = useAuth();
  const { showToast } = useToast();
  const canIngest = hasRole("admin", "operator");

  const [stations, setStations] = useState<Station[]>([]);
  const [live, setLive] = useState<LiveCrowdSnapshot[]>([]);
  const [heatmap, setHeatmap] = useState<StationHeatmapPoint[]>([]);
  const [modelInfo, setModelInfo] = useState<ModelInfo | null>(null);
  const [selected, setSelected] = useState("ST01");
  const [history, setHistory] = useState<HistoryRow[]>([]);
  const [loadingHist, setLoadingHist] = useState(false);
  const [histDate, setHistDate] = useState("");
  const [histHour, setHistHour] = useState("now");
  const [histHours, setHistHours] = useState(24);
  const [connected, setConnected] = useState(false);
  const [ingest, setIngest] = useState({ entries: 140, exits: 110, occupancy: 350 });
  const [ingesting, setIngesting] = useState(false);

  const loadStatic = useCallback(async () => {
    try {
      const [st, lv, hm, mi] = await Promise.all([
        api.get<Station[]>("/stations"),
        api.get<LiveCrowdSnapshot[]>("/crowd/live"),
        api.get<StationHeatmapPoint[]>("/crowd/heatmap"),
        api.get<ModelInfo>("/predictions/model-info").catch(() => null),
      ]);
      setStations(st.data);
      setLive(lv.data);
      setHeatmap(hm.data);
      if (mi) setModelInfo(mi.data);
    } catch {}
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    loadStatic();
  }, [loadStatic]);

  const loadHistory = useCallback((stationId: string) => {
    setLoadingHist(true);
    const start = histDate ? `${histDate}T${String(histHour).padStart(2, "0")}:00:00` : "";
    const qs = `hours=${histHours}` + (start ? `&start_time=${encodeURIComponent(start)}` : "");
    api.get<StationHistoryPoint[]>(`/crowd/station/${stationId}/history?${qs}`)
      .then((res) => {
        setHistory(
          res.data.map((r) => ({
            time: new Date(r.timestamp).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
            full: new Date(r.timestamp).toLocaleString([], { month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" }),
            entries: r.entries,
            exits: r.exits,
            occupancy: r.occupancy,
          }))
        );
      })
      .catch(() => setHistory([]))
      .finally(() => setLoadingHist(false));
  }, [histDate, histHour, histHours]);

  useEffect(() => {
    if (selected) loadHistory(selected);
  }, [selected, loadHistory]);

  const historyAnchorLabel = histDate
    ? `Historical data from ${new Date(`${histDate}T${String(histHour).padStart(2, "0")}:00:00Z`).toLocaleString([], {
        month: "short", day: "numeric", year: "numeric", hour: "2-digit", minute: "2-digit",
      })}`
    : "Last 24h live window (up to date)";

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
    } catch {}
    const iv = setInterval(() => {
      api.get<LiveCrowdSnapshot[]>("/crowd/live").then((r) => setLive(r.data)).catch(() => {});
    }, 25000);
    return () => {
      clearInterval(iv);
      if (s) {
        s.off("connect");
        s.off("disconnect");
        s.off("crowd_update");
      }
    };
  }, []);

  useEffect(() => {
    if (selected) joinStationRoom(selected);
  }, [selected]);

  const selectedStation = stations.find((s) => s.id === selected);
  const selectedLive = live.find((s) => s.station_id === selected);
  const strained = useMemo(() => live.filter((s) => ["high", "critical"].includes(s.congestion_level)).length, [live]);

  async function submitIngest(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setIngesting(true);
    try {
      const res = await api.post<LiveCrowdSnapshot>("/crowd/ingest", {
        station_id: selected,
        entries: Number(ingest.entries),
        exits: Number(ingest.exits),
        occupancy: Number(ingest.occupancy),
      });
      setLive((prev) => prev.map((p) => (p.station_id === selected ? res.data : p)));
      loadHistory(selected);
      showToast(`Ingested gate reading for ${selectedStation?.name || selected}`, "success");
    } catch (err) {
      showToast((err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || "Ingest failed", "error");
    } finally {
      setIngesting(false);
    }
  }

  function exportHeatmap() {
    downloadCsv<StationHeatmapPoint>(`metroflow-heatmap-${Date.now()}.csv`, heatmap, [
      { label: "station_id", key: "station_id" },
      { label: "station_name", key: "station_name" },
      { label: "hour", key: "hour" },
      { label: "occupancy_pct", key: "occupancy_pct" },
      { label: "congestion_level", key: "congestion_level" },
    ]);
    showToast("Exported heatmap CSV", "success");
  }

  return (
    <DashboardLayout title="Crowd Density Monitoring" subtitle="Passenger flow tracking · congestion heatmaps · sensor telemetry">
      {/* Network Status Hero */}
      <div className="hero-gradient relative overflow-hidden rounded-2xl border border-slate-800 p-6 text-white shadow-2xl">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <span className="inline-flex items-center gap-1.5 rounded-full bg-brand-500/20 px-3 py-1 text-xs font-bold text-brand-300 border border-brand-400/30">
              <Radio className="h-3.5 w-3.5 text-emerald-400" /> Live Gate Telemetry
            </span>
            <h2 className="mt-2 text-2xl font-extrabold tracking-tight sm:text-3xl text-white">
              {strained === 0 ? "Passenger Flow Smooth Across All Lines" : `${strained} Station${strained > 1 ? "s" : ""} Experiencing Congestion`}
            </h2>
            <p className="mt-1 text-xs sm:text-sm text-slate-300">
              {live.length} stations active · {connected ? "streaming via Socket.IO room subscriptions" : "25s polling fallback"} · Model: {modelInfo?.city || "hangzhou"}
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-2.5">
            <span className={`inline-flex items-center gap-2 rounded-xl px-3 py-1.5 text-xs font-bold border ${connected ? "bg-emerald-500/15 text-emerald-300 border-emerald-500/30" : "bg-slate-800 text-slate-400 border-slate-700"}`}>
              <span className={`h-2 w-2 rounded-full ${connected ? "bg-emerald-400 animate-ping" : "bg-slate-500"}`} />
              {connected ? "Socket Room Connected" : "Polling Active"}
            </span>

            <button
              onClick={exportHeatmap}
              className="btn-ghost text-xs py-1.5 px-3 font-bold"
            >
              <Download className="h-3.5 w-3.5 text-brand-400" /> Export Heatmap CSV
            </button>
          </div>
        </div>
      </div>

      {/* Operator Sensor Data Ingest Widget */}
      <div className="mt-5 card card-pad border-slate-800">
        <div className="flex items-center justify-between border-b border-slate-800 pb-3 mb-4">
          <div>
            <h3 className="font-extrabold tracking-tight text-white flex items-center gap-2">
              <Sparkles className="h-4 w-4 text-brand-400" /> Sensor Gate Ingest Tool
            </h3>
            <p className="text-xs text-slate-400">
              Simulate turnstile & sensor gate readings for station: <span className="font-bold text-white">{selectedStation?.name || selected}</span>
            </p>
          </div>
          <span className="text-[11px] font-mono text-slate-500">POST /crowd/ingest</span>
        </div>

        {canIngest ? (
          <form onSubmit={submitIngest} className="grid grid-cols-1 gap-3 sm:grid-cols-4">
            <div>
              <label className="label">Entries / min</label>
              <input
                type="number"
                min={0}
                className="input py-2 font-mono"
                value={ingest.entries}
                onChange={(e) => setIngest({ ...ingest, entries: Number(e.target.value) })}
              />
            </div>
            <div>
              <label className="label">Exits / min</label>
              <input
                type="number"
                min={0}
                className="input py-2 font-mono"
                value={ingest.exits}
                onChange={(e) => setIngest({ ...ingest, exits: Number(e.target.value) })}
              />
            </div>
            <div>
              <label className="label">Occupancy Pax</label>
              <input
                type="number"
                min={0}
                className="input py-2 font-mono"
                value={ingest.occupancy}
                onChange={(e) => setIngest({ ...ingest, occupancy: Number(e.target.value) })}
              />
            </div>
            <div className="flex items-end">
              <button
                type="submit"
                disabled={ingesting}
                className="btn-primary w-full py-2.5 text-xs font-extrabold"
              >
                {ingesting ? <Loader2 className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4" />}
                Ingest Telemetry
              </button>
            </div>
          </form>
        ) : (
          <p className="rounded-xl bg-slate-950/60 p-3 text-xs text-slate-400 border border-slate-800">
            Viewers have read-only permissions. Operators and Admins can push live gate readings.
          </p>
        )}
      </div>

      {/* Interactive Metro Track Map */}
      <div className="card card-pad mt-5 border-slate-800">
        <div className="mb-3">
          <h3 className="font-extrabold tracking-tight text-white">Interactive Schematic Metro Network</h3>
          <p className="text-xs text-slate-400">Click any station node to drill down into historical inflow/outflow curves</p>
        </div>
        <MetroMap stations={stations} live={live} selected={selected} onSelect={setSelected} />
      </div>

      {/* Station Cards Grid */}
      <div className="mt-5 grid grid-cols-2 gap-3.5 md:grid-cols-3 xl:grid-cols-5">
        {live.map((s) => {
          const isSel = selected === s.station_id;
          return (
            <button
              key={s.station_id}
              onClick={() => setSelected(s.station_id)}
              className={`card card-pad card-hover text-left border-slate-800 ${
                isSel ? "ring-2 ring-brand-500 bg-brand-950/20 border-brand-500/50" : ""
              }`}
            >
              <div className="flex items-center justify-between">
                <p className="truncate text-xs font-extrabold text-white">{s.station_name}</p>
                <span className="h-2.5 w-2.5 shrink-0 rounded-full" style={{ backgroundColor: congestionColor(s.occupancy_pct) }} />
              </div>
              <p className="mt-1 text-2xl font-extrabold font-mono tracking-tight text-white">{s.occupancy_pct}%</p>
              <div className="mt-2 flex items-center justify-between">
                <span className="text-[10px] font-extrabold uppercase text-slate-400">{s.line} line</span>
                <StatusBadge value={s.congestion_level} />
              </div>
            </button>
          );
        })}
      </div>

      {/* Heatmap Grid */}
      <div className="card card-pad mt-5 border-slate-800">
        <div className="mb-4">
          <h3 className="font-extrabold tracking-tight text-white">24-Hour Station Congestion Heatmap</h3>
          <p className="text-xs text-slate-400">Average occupancy profile per station across hours of the day</p>
        </div>
        <HeatmapGrid points={heatmap} stations={stations.map((s) => ({ id: s.id, name: s.name }))} onSelectStation={setSelected} />
      </div>

      {/* Selected Station History & Telemetry Detail */}
      <div className="mt-5 grid grid-cols-1 gap-5 xl:grid-cols-3">
        {/* History Chart */}
        <div className="card card-pad xl:col-span-2 border-slate-800">
          <div className="mb-3 flex flex-wrap items-center justify-between gap-3">
            <div>
              <h3 className="font-extrabold tracking-tight text-white">
                Inflow vs Outflow — {selectedStation?.name || "Station"}
              </h3>
              <p className="text-xs text-slate-400">{historyAnchorLabel}</p>
            </div>
            <select
              className="input w-auto py-1 text-xs"
              value={selected}
              onChange={(e) => setSelected(e.target.value)}
            >
              {stations.map((s) => (
                <option key={s.id} value={s.id}>{s.name} ({s.id})</option>
              ))}
            </select>
          </div>

          {/* Historical Data Tracker: pick a past date/time window to inspect */}
          <div className="mb-4 flex flex-wrap items-end gap-3 rounded-2xl border border-slate-800 bg-slate-950/60 px-4 py-3">
            <div>
              <label className="label">As-of Date (blank = latest/live)</label>
              <input
                type="date"
                className="input py-1.5 text-xs"
                value={histDate}
                onChange={(e) => setHistDate(e.target.value)}
              />
            </div>
            <div>
              <label className="label">Start Hour</label>
              <select className="input py-1.5 text-xs" value={histHour} onChange={(e) => setHistHour(e.target.value)}>
                <option value="now">Now</option>
                {Array.from({ length: 24 }, (_, h) => (
                  <option key={h} value={h}>{String(h).padStart(2, "0")}:00</option>
                ))}
              </select>
            </div>
            <div>
              <label className="label">Window</label>
              <select className="input py-1.5 text-xs" value={histHours} onChange={(e) => setHistHours(Number(e.target.value))}>
                <option value="12">12 hours</option>
                <option value="24">24 hours</option>
                <option value="48">48 hours (2 days)</option>
                <option value="72">72 hours (3 days)</option>
                <option value="168">7 days</option>
              </select>
            </div>
            <p className="text-[10px] text-slate-500 pb-1">
              Track recorded gate entries/exits for a chosen past date · leave date blank to keep the feed up to date.
            </p>
          </div>

          {loadingHist ? (
            <div className="flex h-[300px] items-center justify-center text-slate-500">
              <Loader2 className="mr-2 h-5 w-5 animate-spin text-brand-400" /> Loading station telemetry history...
            </div>
          ) : history.length === 0 ? (
            <div className="flex h-[300px] items-center justify-center rounded-xl border border-dashed border-slate-800 text-center">
              <p className="px-6 text-xs text-slate-500">
                No recorded telemetry for this station and window. Try a wider window or reset the date to live.
              </p>
            </div>
          ) : (
            <ResponsiveContainer width="100%" height={300}>
              <AreaChart data={history} margin={{ left: -10, right: 10 }}>
                <defs>
                  <linearGradient id="inGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#3b82f6" stopOpacity={0.4} />
                    <stop offset="100%" stopColor="#3b82f6" stopOpacity={0.02} />
                  </linearGradient>
                  <linearGradient id="outGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#10b981" stopOpacity={0.4} />
                    <stop offset="100%" stopColor="#10b981" stopOpacity={0.02} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                <XAxis dataKey="time" tick={{ fontSize: 10, fill: "#94a3b8" }} interval={2} stroke="#334155" />
                <YAxis tick={{ fontSize: 11, fill: "#94a3b8" }} stroke="#334155" />
                <Tooltip contentStyle={{ backgroundColor: "#0f172a", borderColor: "#334155", borderRadius: 12, fontSize: 12, color: "#fff" }} />
                <Legend wrapperStyle={{ fontSize: 12 }} />
                <Area type="monotone" dataKey="entries" name="Gate Entries" stroke="#3b82f6" strokeWidth={2.5} fill="url(#inGrad)" />
                <Area type="monotone" dataKey="exits" name="Gate Exits" stroke="#10b981" strokeWidth={2.5} fill="url(#outGrad)" />
              </AreaChart>
            </ResponsiveContainer>
          )}
        </div>

        {/* Selected Station Telemetry Card */}
        <div className="card card-pad border-slate-800">
          <h3 className="font-extrabold tracking-tight text-white">Telemetry & Specifications</h3>
          <p className="text-xs text-slate-400">{selectedStation?.name} ({selectedStation?.id})</p>

          <div className="mt-4 space-y-3.5">
            <div className="rounded-2xl border border-slate-800 bg-slate-950/80 p-4">
              <p className="text-[10px] font-extrabold uppercase tracking-wider text-slate-400">Current Occupancy</p>
              <div className="mt-1 flex items-end justify-between">
                <p className="text-3xl font-extrabold font-mono text-white">{selectedLive?.occupancy_pct ?? "—"}%</p>
                <StatusBadge value={selectedLive?.congestion_level || "low"} />
              </div>
              <div className="mt-2.5 h-2.5 overflow-hidden rounded-full bg-slate-800">
                <div
                  className="h-full rounded-full transition-all duration-700"
                  style={{
                    width: `${Math.min(100, selectedLive?.occupancy_pct || 0)}%`,
                    backgroundColor: congestionColor(selectedLive?.occupancy_pct || 0),
                  }}
                />
              </div>
              <p className="mt-1.5 text-xs font-mono text-slate-400">
                {selectedLive ? `${Number(selectedLive.occupancy).toLocaleString()} / ${Number(selectedLive.capacity).toLocaleString()} capacity` : "—"}
              </p>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div className="rounded-2xl bg-sky-950/30 p-3 border border-sky-800/40">
                <p className="flex items-center gap-1 text-xs font-bold text-sky-400">
                  <ArrowDown className="h-3.5 w-3.5" /> Inflow Rate
                </p>
                <p className="mt-1 text-xl font-extrabold font-mono text-white">
                  {selectedLive?.inflow_rate ?? "—"}<span className="text-xs font-sans text-slate-400">/min</span>
                </p>
              </div>

              <div className="rounded-2xl bg-emerald-950/30 p-3 border border-emerald-800/40">
                <p className="flex items-center gap-1 text-xs font-bold text-emerald-400">
                  <ArrowUp className="h-3.5 w-3.5" /> Outflow Rate
                </p>
                <p className="mt-1 text-xl font-extrabold font-mono text-white">
                  {selectedLive?.outflow_rate ?? "—"}<span className="text-xs font-sans text-slate-400">/min</span>
                </p>
              </div>
            </div>

            <dl className="space-y-2 pt-1 text-xs">
              <div className="flex justify-between border-b border-slate-800/80 pb-2">
                <dt className="text-slate-400">Metro Line</dt>
                <dd className="font-bold text-white">{selectedStation?.line || "—"}</dd>
              </div>
              <div className="flex justify-between border-b border-slate-800/80 pb-2">
                <dt className="text-slate-400">Zone</dt>
                <dd className="font-bold text-white">{selectedStation?.zone || "—"}</dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-slate-400">Hourly Capacity</dt>
                <dd className="font-bold font-mono text-white">{selectedStation?.capacity_per_hour?.toLocaleString() || "—"}</dd>
              </div>
            </dl>
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
}

export default withAuth(CrowdMonitoring);