import { useCallback, useEffect, useMemo, useState } from "react";
import { Loader2, MapPin, Radio, Timer, TrainFront, TrendingUp, Waves } from "lucide-react";
import {
  Area, AreaChart, CartesianGrid, Legend, ResponsiveContainer, Tooltip, XAxis, YAxis,
} from "recharts";
import DashboardLayout from "../../components/DashboardLayout";
import StatusBadge, { congestionColor } from "../../components/StatusBadge";
import { withAuth } from "../../lib/auth";
import api from "../../lib/api";
import { getSocket, joinTrainRoom } from "../../lib/socket";

const LINE_COLORS = {
  Red: "#f43f5e",
  Blue: "#3b82f6",
  Green: "#10b981",
};

const LINE_TEXT = {
  Red: "text-rose-400",
  Blue: "text-brand-400",
  Green: "text-emerald-400",
};

function Trains() {
  const [trains, setTrains] = useState([]);
  const [selectedId, setSelectedId] = useState("");
  const [connected, setConnected] = useState(false);
  const [loading, setLoading] = useState(true);
  const [detail, setDetail] = useState(null);
  const [schedule, setSchedule] = useState([]);
  const [forecast, setForecast] = useState([]);
  const [loadingDetail, setLoadingDetail] = useState(false);

  const loadTrains = useCallback(async () => {
    try {
      const res = await api.get("/trains/live");
      setTrains(res.data);
      if (!selectedId && res.data.length) setSelectedId((cur) => cur || res.data[0].train_id);
    } catch {}
    setLoading(false);
  }, [selectedId]);

  useEffect(() => {
    loadTrains();
  }, [loadTrains]);

  // Realtime: Socket.IO train_update feed + 15s polling fallback.
  useEffect(() => {
    let s;
    try {
      s = getSocket();
      s.on("connect", () => setConnected(true));
      s.on("disconnect", () => setConnected(false));
      s.on("train_update", (tr) => {
        setTrains((prev) => {
          const idx = prev.findIndex((t) => t.train_id === tr.train_id);
          if (idx === -1) return [...prev, tr];
          const next = [...prev];
          next[idx] = tr;
          return next;
        });
      });
    } catch {}
    const iv = setInterval(loadTrains, 15000);
    return () => {
      clearInterval(iv);
      if (s) {
        s.off("connect");
        s.off("disconnect");
        s.off("train_update");
      }
    };
  }, [loadTrains]);

  // Subscribe to the selected train's room for precise updates.
  useEffect(() => {
    if (selectedId) joinTrainRoom(selectedId);
  }, [selectedId]);

  // Load detail panel (schedule + per-stop forecast) when a train is selected.
  const loadDetail = useCallback((trainId) => {
    if (!trainId) return;
    setLoadingDetail(true);
    Promise.all([
      api.get(`/trains/${trainId}/schedule`).catch(() => []),
      api.get(`/predictions/train/${trainId}?hours=12`).catch(() => []),
    ])
      .then(([sc, fc]) => {
        setSchedule(sc);
        setForecast(fc);
        setDetail(trains.find((t) => t.train_id === trainId) || null);
      })
      .finally(() => setLoadingDetail(false));
  }, [trains]);

  useEffect(() => {
    if (selectedId) loadDetail(selectedId);
  }, [selectedId, loadDetail]);

  // Keep the detail snapshot live as updates stream in.
  useEffect(() => {
    if (selectedId) {
      const tr = trains.find((t) => t.train_id === selectedId);
      if (tr) setDetail(tr);
    }
  }, [trains, selectedId]);

  const statusCounts = useMemo(() => {
    const counts = { in_transit: 0, at_station: 0, delayed: 0, awaiting_departure: 0, in_depot: 0, out_of_service: 0 };
    trains.forEach((t) => {
      if (counts[t.status] != null) counts[t.status] += 1;
    });
    return counts;
  }, [trains]);

  const selected = trains.find((t) => t.train_id === selectedId) || detail;
  const selLine = selected?.line || "Red";
  const lineAccent = LINE_COLORS[selLine] || "#3b82f6";

  const forecastChart = forecast.map((p) => ({
    label: new Date(p.arrival).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
    occupancy: p.predicted_occupancy_pct,
    entries: p.predicted_entries,
  }));

  return (
    <DashboardLayout title="Real-Time Train Monitoring" subtitle="Fleet telemetry · live position & ETA · per-train forecasting">
      {/* Network Status Hero */}
      <div className="hero-gradient relative overflow-hidden rounded-2xl border border-slate-800 p-6 text-white shadow-2xl">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <span className="inline-flex items-center gap-1.5 rounded-full bg-emerald-500/20 px-3 py-1 text-xs font-bold text-emerald-300 border border-emerald-400/30">
              <Radio className="h-3.5 w-3.5 text-emerald-400" /> Live Fleet Telemetry
            </span>
            <h2 className="mt-2 text-2xl font-extrabold tracking-tight sm:text-3xl text-white">
              {statusCounts.delayed > 0
                ? `${statusCounts.delayed} Train${statusCounts.delayed > 1 ? "s" : ""} Running Behind Schedule`
                : "All Trains Running Per Timetable"}
            </h2>
            <p className="mt-1 text-xs sm:text-sm text-slate-300">
              {trains.length} fleet units tracked · {connected ? "streaming via Socket.IO per-train rooms" : "15s polling fallback"}
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-2.5">
            <span className={`inline-flex items-center gap-2 rounded-xl px-3 py-1.5 text-xs font-bold border ${connected ? "bg-emerald-500/15 text-emerald-300 border-emerald-500/30" : "bg-slate-800 text-slate-400 border-slate-700"}`}>
              <span className={`h-2 w-2 rounded-full ${connected ? "bg-emerald-400 animate-ping" : "bg-slate-500"}`} />
              {connected ? "Realtime Connected" : "Polling Active"}
            </span>

            <div className="flex items-center gap-3 rounded-xl border border-slate-700 bg-slate-950/60 px-3.5 py-2 text-xs">
              <span className="text-slate-400">On time <b className="text-emerald-400">{trains.length - statusCounts.delayed - statusCounts.in_depot - statusCounts.out_of_service}</b></span>
              <span className="text-slate-400">Delayed <b className="text-amber-400">{statusCounts.delayed}</b></span>
              <span className="text-slate-400">Depot <b className="text-slate-300">{statusCounts.in_depot}</b></span>
            </div>
          </div>
        </div>
      </div>

      {/* Live Fleet Cards */}
      <div className="mt-5 grid grid-cols-1 gap-3.5 sm:grid-cols-2 xl:grid-cols-3">
        {trains.map((t) => {
          const isSel = selectedId === t.train_id;
          const acc = LINE_COLORS[t.line] || "#3b82f6";
          const lineTx = LINE_TEXT[t.line] || "text-brand-400";
          const inService = ["in_transit", "at_station", "awaiting_departure", "delayed"].includes(t.status);
          return (
            <button
              key={t.train_id}
              onClick={() => setSelectedId(t.train_id)}
              className={`card card-pad card-hover text-left border-slate-800 ${isSel ? "ring-2 ring-brand-500 bg-brand-950/20 border-brand-500/50" : ""}`}
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2.5">
                  <span className="flex h-9 w-9 items-center justify-center rounded-xl border" style={{ backgroundColor: `${acc}22`, borderColor: `${acc}55`, color: acc }}>
                    <TrainFront className="h-4.5 w-4.5" />
                  </span>
                  <div>
                    <p className="text-sm font-extrabold text-white leading-tight">{t.train_id}</p>
                    <p className={`text-[10px] font-extrabold uppercase tracking-wider ${lineTx}`}>{t.line} Line · {t.model}</p>
                  </div>
                </div>
                <StatusBadge value={t.status === "delayed" ? "critical" : inService ? "on_time" : t.status} />
              </div>

              {/* Position along the line */}
              {inService ? (
                <div className="mt-3.5">
                  <div className="flex items-center justify-between text-[10px] font-mono text-slate-400">
                    <span className="flex items-center gap-1"><MapPin className="h-3 w-3" />{t.current_station?.name || "Depot"}</span>
                    <span className="text-white text-xs font-extrabold">{Math.round(t.position_pct)}%</span>
                    <span className="flex items-center gap-1">{t.next_station?.name || "—"}<MapPin className="h-3 w-3" /></span>
                  </div>
                  <div className="relative mt-1.5 h-2 overflow-hidden rounded-full bg-slate-800">
                    <div className="h-full rounded-full transition-all duration-1000" style={{ width: `${t.position_pct || 0}%`, background: `linear-gradient(90deg, ${acc}88, ${acc})` }} />
                  </div>
                </div>
              ) : (
                <p className="mt-3.5 rounded-lg bg-slate-950/60 border border-slate-800 px-2.5 py-1.5 text-[10px] font-bold uppercase tracking-wider text-slate-400">
                  {t.status === "in_depot" ? "In depot · maintenance / stand-by" : "Out of service"}
                </p>
              )}

              <div className="mt-3 flex items-center justify-between text-[11px]">
                <span className={`font-mono font-bold ${t.delay_min > 2 ? "text-amber-400" : "text-slate-500"}`}>
                  {t.delay_min > 2 ? `+${t.delay_min}m delay` : "on schedule"}
                </span>
                {t.next_eta_min != null && (
                  <span className="flex items-center gap-1 text-slate-400"><Timer className="h-3 w-3" /> ETA {Math.round(t.next_eta_min)}m</span>
                )}
                {t.load_pct != null && (
                  <span className="flex items-center gap-1 font-mono" style={{ color: congestionColor(t.load_pct) }}>
                    <Waves className="h-3 w-3" /> {Math.round(t.load_pct)}% load
                  </span>
                )}
              </div>
            </button>
          );
        })}
        {loading && (
          <div className="col-span-full flex h-40 items-center justify-center text-slate-500">
            <Loader2 className="mr-2 h-5 w-5 animate-spin text-brand-400" /> Polling live fleet telemetry...
          </div>
        )}
      </div>

      {/* Selected Train Detail */}
      {selected && (
        <div className="mt-5 grid grid-cols-1 gap-5 xl:grid-cols-3">
          {/* Live telemetry + upcoming stops table */}
          <div className="card border-slate-800 xl:col-span-2">
            <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-800 px-5 py-4">
              <div>
                <h3 className="font-extrabold tracking-tight text-white">{selected.train_id} — Live Telemetry</h3>
                <p className="text-xs text-slate-400">
                  {selected.model} · capacity {selected.capacity?.toLocaleString()} pax · updated {new Date(selected.last_updated).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" })}
                </p>
              </div>
              <span className="rounded-xl border border-slate-700 bg-slate-950/60 px-3 py-1.5 font-mono text-xs font-bold capitalize text-slate-300">
                {selected.status.replaceAll("_", " ")} · {String(selected.direction || "").toLowerCase()}
              </span>
            </div>

            <div className="p-5">
              <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
                <div className="rounded-2xl border border-slate-800 bg-slate-950/70 p-3">
                  <p className="text-[10px] font-extrabold uppercase tracking-wider text-slate-400">Current Station</p>
                  <p className="mt-1 text-sm font-extrabold text-white truncate">{selected.current_station?.name || "—"}</p>
                </div>
                <div className="rounded-2xl border border-slate-800 bg-slate-950/70 p-3">
                  <p className="text-[10px] font-extrabold uppercase tracking-wider text-slate-400">Next Stop</p>
                  <p className="mt-1 text-sm font-extrabold text-white truncate">{selected.next_station?.name || "—"}</p>
                </div>
                <div className="rounded-2xl border border-slate-800 bg-slate-950/70 p-3">
                  <p className="text-[10px] font-extrabold uppercase tracking-wider text-slate-400">ETA Next Stop</p>
                  <p className="mt-1 text-sm font-extrabold font-mono text-white">{selected.next_eta_min != null ? `${Math.round(selected.next_eta_min)} min` : "—"}</p>
                </div>
                <div className="rounded-2xl border border-slate-800 bg-slate-950/70 p-3">
                  <p className="text-[10px] font-extrabold uppercase tracking-wider text-slate-400">Headway</p>
                  <p className="mt-1 text-sm font-extrabold font-mono text-white">{selected.headway_min != null ? `${selected.headway_min} min` : "—"}</p>
                </div>
              </div>

              {/* Upcoming stops */}
              <div className="mt-4 overflow-x-auto">
                <table className="table-base">
                  <thead>
                    <tr>
                      <th>Next Stop</th>
                      <th>Arrival</th>
                      <th>Status</th>
                      <th>Delay</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/80">
                    {schedule.slice(0, 8).map((s) => (
                      <tr key={s.id} className="hover:bg-slate-850/60 transition">
                        <td className="font-bold text-white">
                          {s.station_name}
                          <span className="ml-2 text-[10px] font-mono uppercase text-slate-500">{s.direction}</span>
                        </td>
                        <td className="font-mono text-xs">{new Date(s.arrival).toLocaleString([], { month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" })}</td>
                        <td><StatusBadge value={s.status} /></td>
                        <td className={s.delay_min > 0 ? "font-mono font-bold text-amber-400" : "text-slate-500"}>{s.delay_min > 0 ? `+${s.delay_min}m` : "—"}</td>
                      </tr>
                    ))}
                    {schedule.length === 0 && (
                      <tr><td colSpan="4" className="py-8 text-center text-xs text-slate-500">No upcoming stops in the current timetable window.</td></tr>
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          </div>

          {/* Per-stop forecast */}
          <div className="card card-pad border-slate-800">
            <div className="flex items-center gap-3 border-b border-slate-800 pb-3 mb-3">
              <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-brand-500/15 border border-brand-500/30 text-brand-400">
                <TrendingUp className="h-4 w-4" />
              </span>
              <div>
                <h3 className="font-extrabold tracking-tight text-white">Forward Stop Forecast</h3>
                <p className="text-xs text-slate-400">Predicted platform crowding per upcoming stop</p>
              </div>
            </div>

            {loadingDetail ? (
              <div className="flex h-[220px] items-center justify-center text-slate-500">
                <Loader2 className="mr-2 h-4 w-4 animate-spin text-brand-400" /> Running AI inference...
              </div>
            ) : forecast.length > 0 ? (
              <ResponsiveContainer width="100%" height={220}>
                <AreaChart data={forecastChart} margin={{ left: -10, right: 10 }}>
                  <defs>
                    <linearGradient id="trainForecastGrad" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stopColor={lineAccent} stopOpacity={0.4} />
                      <stop offset="100%" stopColor={lineAccent} stopOpacity={0.02} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                  <XAxis dataKey="label" tick={{ fontSize: 10, fill: "#94a3b8" }} interval="preserveStartEnd" stroke="#334155" />
                  <YAxis unit="%" domain={[0, 100]} tick={{ fontSize: 10, fill: "#94a3b8" }} stroke="#334155" />
                  <Tooltip contentStyle={{ backgroundColor: "#0f172a", borderColor: "#334155", borderRadius: 12, fontSize: 12, color: "#fff" }} />
                  <Legend wrapperStyle={{ fontSize: 11 }} />
                  <Area type="monotone" name="Predicted Occupancy" dataKey="occupancy" stroke={lineAccent} strokeWidth={2.5} fill="url(#trainForecastGrad)" />
                </AreaChart>
              </ResponsiveContainer>
            ) : (
              <p className="rounded-xl bg-slate-950/60 p-3 text-xs text-slate-400 border border-slate-800">
                No forecast available for this train in the current window.
              </p>
            )}

            <dl className="mt-4 space-y-2 text-xs">
              <div className="flex justify-between border-b border-slate-800/80 pb-2">
                <dt className="text-slate-400">Projected Load</dt>
                <dd className="font-bold font-mono text-white">{selected.load_pct != null ? `${Math.round(selected.load_pct)}%` : "—"}</dd>
              </div>
              <div className="flex justify-between border-b border-slate-800/80 pb-2">
                <dt className="text-slate-400">Current Delay</dt>
                <dd className={selected.delay_min > 2 ? "font-bold font-mono text-amber-400" : "font-bold font-mono text-emerald-400"}>
                  {selected.delay_min > 0 ? `+${selected.delay_min}m` : "0m"}
                </dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-slate-400">Rolling Stock</dt>
                <dd className="font-bold text-white">{selected.model}</dd>
              </div>
            </dl>
          </div>
        </div>
      )}
    </DashboardLayout>
  );
}

export default withAuth(Trains);