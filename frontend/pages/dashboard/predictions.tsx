import { useEffect, useMemo, useState, type FormEvent } from "react";
import { BrainCircuit, CalendarDays, Clock3, Lightbulb, Loader2, Sparkles, TrainFront, TrendingUp } from "lucide-react";
import {
  Area, AreaChart, CartesianGrid, Legend, ResponsiveContainer, Tooltip, XAxis, YAxis,
} from "recharts";
import DashboardLayout from "../../components/DashboardLayout";
import ModelBadge from "../../components/ModelBadge";
import StatusBadge from "../../components/StatusBadge";
import { withAuth } from "../../lib/auth";
import { useToast } from "../../components/ToastContext";
import api from "../../lib/api";
import type { Station, PredictionPoint, DemandPoint, Recommendation, TrafficPattern, ModelInfo, DelayPredictResponse } from "../../lib/types";

interface TooltipRow {
  dataKey?: string | number;
  value?: number | string | Array<number | string>;
  name?: string | number;
}

function CrowdTooltip({ active, payload, label }: { active?: boolean; payload?: TooltipRow[]; label?: string | number }) {
  if (!active || !payload?.length) return null;
  const base = Number(payload.find((p) => p.dataKey === "bandBase")?.value ?? 0);
  const width = Number(payload.find((p) => p.dataKey === "bandWidth")?.value ?? 0);
  const raw = payload.find((p) => p.dataKey === "predicted")?.value;
  const predicted = raw == null ? null : Number(raw);
  return (
    <div className="rounded-xl border border-slate-700 bg-slate-900 px-3.5 py-2.5 text-xs text-white shadow-xl backdrop-blur-xl">
      <p className="font-extrabold text-brand-400">{label}</p>
      {predicted != null && <p className="text-slate-200 mt-0.5">Predicted Occupancy: <span className="font-mono font-bold text-white">{predicted}%</span></p>}
      {width > 0 && <p className="text-slate-400 text-[11px] font-mono">Confidence Band: {Math.round(base)}–{Math.round(base + width)}%</p>}
    </div>
  );
}

const NJ_LINES = [
  "Northeast Corrdr",
  "North Jersey Coast",
  "Morristown Line",
  "Montclair-Boonton",
  "Gladstone Branch",
  "Raritan Valley",
  "Main Line",
  "Bergen Co. Line",
  "Pascack Valley",
  "Atl. City Line",
  "Princeton Shuttle",
];

function Predictions() {
  const { showToast } = useToast();
  const [stations, setStations] = useState<Station[]>([]);
  const [stationId, setStationId] = useState("");
  const [crowd, setCrowd] = useState<PredictionPoint[]>([]);
  const [demand, setDemand] = useState<DemandPoint[]>([]);
  const [recs, setRecs] = useState<Recommendation[]>([]);
  const [patterns, setPatterns] = useState<TrafficPattern[]>([]);
  const [modelInfo, setModelInfo] = useState<ModelInfo | null>(null);
  const [loading, setLoading] = useState(true);

  // Forecast window controls: pick an explicit date + start hour, or run from
  // the current hour ("now"). The models resolve day-of-week per hour so the
  // window can span multiple days.
  const [forecastDate, setForecastDate] = useState(() => {
    const d = new Date();
    d.setMinutes(0, 0, 0);
    return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
  });
  const [forecastHour, setForecastHour] = useState("now");
  const [forecastSpan, setForecastSpan] = useState(12);

  const startTimeParam = useMemo(() => {
    if (forecastHour === "now") return "";
    return `${forecastDate}T${String(forecastHour).padStart(2, "0")}:00:00`;
  }, [forecastDate, forecastHour]);

  const formatPoint = (p: { hour: number; timestamp?: string | null }) => {
    const t = p.timestamp ? new Date(p.timestamp) : null;
    if (!t || Number.isNaN(t.getTime())) return `${String(p.hour).padStart(2, "0")}:00`;
    const day = t.toLocaleDateString([], { month: "short", day: "numeric" });
    const todayStr = new Date().toLocaleDateString([], { month: "short", day: "numeric" });
    return day === todayStr ? `${String(p.hour).padStart(2, "0")}:00` : `${day} ${String(p.hour).padStart(2, "0")}:00`;
  };

  const [delayForm, setDelayForm] = useState({
    line: "Northeast Corrdr",
    from_station: "NY Penn",
    to_station: "Newark Penn",
    stop_sequence: "5",
    hour: "8",
    weekday: "1",
    scheduled_time: "08:30",
    train_type: "NJ Transit",
  });
  const [delayRes, setDelayRes] = useState<DelayPredictResponse | null>(null);
  const [delayBusy, setDelayBusy] = useState(false);
  const [delayErr, setDelayErr] = useState("");

  useEffect(() => {
    api.get<Station[]>("/stations/").then((res) => {
      setStations(res.data);
      if (res.data.length) setStationId(res.data[0].id);
    }).catch(() => {});

    api.get<Recommendation[]>("/predictions/recommendations").then((res) => setRecs(res.data)).catch(() => {});
    api.get<TrafficPattern[]>("/predictions/patterns").then((res) => setPatterns(res.data)).catch(() => {});
    api.get<ModelInfo>("/predictions/model-info").then((res) => setModelInfo(res.data)).catch(() => {});
  }, []);

  useEffect(() => {
    if (!stationId) return;
    setLoading(true);
    const qs =
      `station_id=${stationId}&hours=${forecastSpan}` +
      (startTimeParam ? `&start_time=${encodeURIComponent(startTimeParam)}` : "");
    Promise.all([
      api.get<PredictionPoint[]>(`/predictions/crowd?${qs}`),
      api.get<DemandPoint[]>(`/predictions/demand?${qs}`),
    ])
      .then(([c, d]) => {
        setCrowd(c.data);
        setDemand(d.data);
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [stationId, forecastSpan, startTimeParam]);

  const crowdChart = crowd.map((p) => ({
    label: formatPoint(p),
    predicted: p.predicted_occupancy_pct,
    bandBase: p.lower,
    bandWidth: Math.max(0, p.upper - p.lower),
  }));

  const demandChart = demand.map((p) => ({
    label: formatPoint(p),
    entries: p.predicted_entries,
    exits: p.predicted_exits,
  }));

  const peakHour = demand.reduce(
    (best, cur) => (cur.predicted_entries > best.predicted_entries ? cur : best),
    demand[0] || { hour: "--", predicted_entries: 0 }
  );

  async function runDelay(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setDelayBusy(true);
    setDelayErr("");
    setDelayRes(null);
    try {
      const res = await api.post<DelayPredictResponse>("/predictions/delay", {
        line: delayForm.line,
        from_station: delayForm.from_station,
        to_station: delayForm.to_station,
        stop_sequence: Number(delayForm.stop_sequence),
        hour: Number(delayForm.hour),
        weekday: Number(delayForm.weekday),
        scheduled_time: delayForm.scheduled_time,
        train_type: delayForm.train_type,
      });
      setDelayRes(res.data);
      showToast(`Predicted delay bucket: ${res.data.delay_bucket}`, "info");
    } catch (err) {
      setDelayErr((err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || "Delay model offline. Ensure model artifacts exist.");
    } finally {
      setDelayBusy(false);
    }
  }

  return (
    <DashboardLayout title="AI Predictions & Delay Predictor" subtitle="Crowd forecasting · passenger demand inference · XGBoost delay models">
      {/* Model Specs Header Grid */}
      <div className="grid grid-cols-1 gap-5 xl:grid-cols-3">
        <div className="xl:col-span-2">
          <ModelBadge info={modelInfo} />
        </div>

        <div className="grid grid-cols-1 gap-4">
          <div className="card card-pad border-slate-800 flex items-center gap-4">
            <span className="flex h-12 w-12 items-center justify-center rounded-2xl bg-emerald-500/15 border border-emerald-500/30 text-emerald-400">
              <TrendingUp className="h-6 w-6" />
            </span>
            <div>
              <p className="text-[11px] font-extrabold uppercase tracking-[0.14em] text-slate-400">Forecasted Peak Demand</p>
              <p className="text-xl font-extrabold font-mono text-white mt-0.5">
                {String(peakHour.hour).padStart(2, "0")}:00 · {peakHour.predicted_entries?.toLocaleString()} pax
              </p>
            </div>
          </div>

          <div className="card card-pad border-slate-800">
            <label className="label">Target Station for AI Inference</label>
            <select className="input" value={stationId} onChange={(e) => setStationId(e.target.value)}>
              {stations.map((s) => (
                <option key={s.id} value={s.id}>{s.name} ({s.id})</option>
              ))}
            </select>
            <p className="mt-2 text-[11px] text-slate-400">
              One-hot feature encoding + hourly capacity features · {modelInfo?.crowd?.algorithm}
            </p>
          </div>
        </div>
      </div>

      {/* Forecast Window Controls */}
      <div className="card card-pad mt-5 border-slate-800">
        <div className="flex flex-wrap items-end gap-4">
          <div className="flex items-center gap-3">
            <span className="flex h-11 w-11 items-center justify-center rounded-2xl bg-brand-500/15 border border-brand-500/30 text-brand-400">
              <CalendarDays className="h-5 w-5" />
            </span>
            <div>
              <p className="text-[11px] font-extrabold uppercase tracking-[0.14em] text-slate-400">Forecast Window</p>
              <p className="text-xs text-slate-500">
                {startTimeParam
                  ? `Predicting from ${new Date(`${startTimeParam}Z`).toLocaleString([], { month: "short", day: "numeric", year: "numeric", hour: "2-digit", minute: "2-digit" })}`
                  : "Predicting from the current hour"}
              </p>
            </div>
          </div>

          <div>
            <label className="label">Forecast Date</label>
            <input
              type="date"
              className="input"
              value={forecastDate}
              onChange={(e) => setForecastDate(e.target.value)}
            />
          </div>

          <div>
            <label className="label">Start Hour</label>
            <select className="input" value={forecastHour} onChange={(e) => setForecastHour(e.target.value)}>
              <option value="now">Now</option>
              {Array.from({ length: 24 }, (_, h) => (
                <option key={h} value={h}>{String(h).padStart(2, "0")}:00</option>
              ))}
            </select>
          </div>

          <div>
            <label className="label">Forecast Span</label>
            <select className="input" value={forecastSpan} onChange={(e) => setForecastSpan(Number(e.target.value))}>
              <option value="6">6 hours</option>
              <option value="12">12 hours</option>
              <option value="24">24 hours (1 day)</option>
              <option value="48">48 hours (2 days)</option>
              <option value="72">72 hours (3 days)</option>
            </select>
          </div>
        </div>
      </div>

      {/* Forecast Charts Row */}
      <div className="mt-5 grid grid-cols-1 gap-5 xl:grid-cols-2">
        {/* Crowd Density Forecast Area Chart */}
        <div className="card card-pad border-slate-800">
          <h3 className="font-extrabold tracking-tight text-white">{forecastSpan}-Hour Crowd Density Forecast</h3>
          <p className="mb-4 text-xs text-slate-400">Predicted occupancy % with confidence upper/lower bounds</p>

          {loading ? (
            <div className="flex h-[300px] items-center justify-center text-slate-500">
              <Loader2 className="mr-2 h-5 w-5 animate-spin text-brand-400" /> Running AI crowd inference...
            </div>
          ) : (
            <ResponsiveContainer width="100%" height={300}>
              <AreaChart data={crowdChart} margin={{ left: -10, right: 10 }}>
                <defs>
                  <linearGradient id="predGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#3b82f6" stopOpacity={0.4} />
                    <stop offset="100%" stopColor="#3b82f6" stopOpacity={0.02} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                <XAxis dataKey="label" tick={{ fontSize: 9, fill: "#94a3b8" }} interval="preserveStartEnd" stroke="#334155" />
                <YAxis unit="%" tick={{ fontSize: 11, fill: "#94a3b8" }} stroke="#334155" domain={[0, 100]} />
                <Tooltip content={<CrowdTooltip />} />
                <Legend wrapperStyle={{ fontSize: 12 }} />
                <Area name="bandBase" dataKey="bandBase" stackId="band" stroke="none" fill="none" legendType="none" isAnimationActive={false} />
                <Area name="Confidence Band" dataKey="bandWidth" stackId="band" stroke="none" fill="#3b82f6" fillOpacity={0.15} legendType="none" />
                <Area name="Predicted Occupancy" dataKey="predicted" type="monotone" stroke="#3b82f6" strokeWidth={3} fill="url(#predGrad)" />
              </AreaChart>
            </ResponsiveContainer>
          )}
        </div>

        {/* Passenger Demand Forecast Area Chart */}
        <div className="card card-pad border-slate-800">
          <h3 className="font-extrabold tracking-tight text-white">{forecastSpan}-Hour Passenger Demand Forecast</h3>
          <p className="mb-4 text-xs text-slate-400">Predicted gate entries vs exits volume</p>

          {loading ? (
            <div className="flex h-[300px] items-center justify-center text-slate-500">
              <Loader2 className="mr-2 h-5 w-5 animate-spin text-emerald-400" /> Running AI demand inference...
            </div>
          ) : (
            <ResponsiveContainer width="100%" height={300}>
              <AreaChart data={demandChart} margin={{ left: -10, right: 10 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                <XAxis dataKey="label" tick={{ fontSize: 9, fill: "#94a3b8" }} interval="preserveStartEnd" stroke="#334155" />
                <YAxis tick={{ fontSize: 11, fill: "#94a3b8" }} stroke="#334155" />
                <Tooltip contentStyle={{ backgroundColor: "#0f172a", borderColor: "#334155", borderRadius: 12, fontSize: 12, color: "#fff" }} />
                <Legend wrapperStyle={{ fontSize: 12 }} />
                <Area type="monotone" name="Entries Forecast" dataKey="entries" stroke="#3b82f6" strokeWidth={2.5} fill="#3b82f6" fillOpacity={0.1} />
                <Area type="monotone" name="Exits Forecast" dataKey="exits" stroke="#10b981" strokeWidth={2.5} fill="#10b981" fillOpacity={0.1} />
              </AreaChart>
            </ResponsiveContainer>
          )}
        </div>
      </div>

      {/* Delay Predictor Widget */}
      <div className="card mt-5 border-slate-800 overflow-hidden">
        <div className="flex items-center gap-3 border-b border-slate-800 bg-gradient-to-r from-indigo-950/40 to-transparent px-5 py-4">
          <span className="flex h-10 w-10 items-center justify-center rounded-2xl bg-indigo-500/15 border border-indigo-500/30 text-indigo-400">
            <TrainFront className="h-5 w-5" />
          </span>
          <div>
            <h3 className="font-extrabold tracking-tight text-white">Live Delay Inference Machine — NJ Transit & Amtrak</h3>
            <p className="text-xs text-slate-400">
              Dual-stage XGBoost Classifier & Regressor · AUC 0.733 · MAE 3.15 min
            </p>
          </div>
        </div>

        <div className="grid grid-cols-1 gap-0 lg:grid-cols-2 divide-y divide-slate-800 lg:divide-y-0 lg:divide-x">
          {/* Form */}
          <form onSubmit={runDelay} className="grid grid-cols-2 gap-3.5 p-5">
            <div className="col-span-2">
              <label className="label">Transit Line</label>
              <select
                className="input"
                value={delayForm.line}
                onChange={(e) => setDelayForm({ ...delayForm, line: e.target.value })}
              >
                {NJ_LINES.map((l) => (
                  <option key={l} value={l}>{l}</option>
                ))}
              </select>
            </div>

            <div>
              <label className="label">Origin Station</label>
              <input
                className="input"
                value={delayForm.from_station}
                onChange={(e) => setDelayForm({ ...delayForm, from_station: e.target.value })}
              />
            </div>

            <div>
              <label className="label">Destination Station</label>
              <input
                className="input"
                value={delayForm.to_station}
                onChange={(e) => setDelayForm({ ...delayForm, to_station: e.target.value })}
              />
            </div>

            <div>
              <label className="label">Stop Sequence #</label>
              <input
                type="number"
                className="input font-mono"
                value={delayForm.stop_sequence}
                onChange={(e) => setDelayForm({ ...delayForm, stop_sequence: e.target.value })}
              />
            </div>

            <div>
              <label className="label">Hour & Weekday (0-6)</label>
              <div className="flex gap-2">
                <input
                  type="number"
                  min={0}
                  max={23}
                  className="input font-mono"
                  value={delayForm.hour}
                  onChange={(e) => setDelayForm({ ...delayForm, hour: e.target.value })}
                />
                <input
                  type="number"
                  min={0}
                  max={6}
                  className="input font-mono"
                  value={delayForm.weekday}
                  onChange={(e) => setDelayForm({ ...delayForm, weekday: e.target.value })}
                />
              </div>
            </div>

            <div>
              <label className="label">Scheduled Time (HH:MM)</label>
              <input
                className="input font-mono"
                value={delayForm.scheduled_time}
                onChange={(e) => setDelayForm({ ...delayForm, scheduled_time: e.target.value })}
              />
            </div>

            <div>
              <label className="label">Operator Type</label>
              <select
                className="input"
                value={delayForm.train_type}
                onChange={(e) => setDelayForm({ ...delayForm, train_type: e.target.value })}
              >
                <option>NJ Transit</option>
                <option>Amtrak</option>
              </select>
            </div>

            <button type="submit" disabled={delayBusy} className="btn-primary col-span-2 py-3 text-xs font-extrabold mt-1">
              {delayBusy ? <Loader2 className="h-4 w-4 animate-spin" /> : <Clock3 className="h-4 w-4" />}
              Run Delay Prediction Inference
            </button>

            {delayErr && (
              <p className="col-span-2 rounded-xl bg-rose-500/10 p-3 text-xs font-semibold text-rose-400 border border-rose-500/30">
                {delayErr}
              </p>
            )}
          </form>

          {/* Results Panel */}
          <div className="p-5 bg-slate-950/60 flex flex-col justify-center">
            {!delayRes ? (
              <div className="text-center py-12 text-slate-500 space-y-2">
                <BrainCircuit className="mx-auto h-8 w-8 text-slate-600" />
                <p className="text-xs font-medium">Run inference to view predicted delay minutes & probability distribution.</p>
              </div>
            ) : (
              <div className="space-y-4">
                <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                  <div>
                    <p className="text-xs font-extrabold uppercase text-slate-400">Prediction Outcome</p>
                    <div className="flex items-center gap-2 mt-1">
                      <StatusBadge
                        value={
                          delayRes.delay_bucket === "delayed"
                            ? "critical"
                            : delayRes.delay_bucket === "minor_delay"
                            ? "medium"
                            : "low"
                        }
                      />
                      <span className="text-lg font-extrabold text-white">{delayRes.delay_bucket}</span>
                    </div>
                  </div>
                  <span className="text-3xl font-extrabold font-mono text-white">
                    +{delayRes.predicted_delay_minutes} <span className="text-xs font-sans text-slate-400">min delay</span>
                  </span>
                </div>

                <div className="space-y-2.5">
                  <p className="text-[11px] font-extrabold uppercase tracking-wider text-slate-400">Bucket Probabilities</p>
                  {Object.entries(delayRes.probabilities || {}).map(([k, v]) => (
                    <div key={k} className="flex items-center gap-3 text-xs">
                      <span className="w-28 font-bold text-slate-300 capitalize">{k.replace("_", " ")}</span>
                      <div className="h-2 flex-1 overflow-hidden rounded-full bg-slate-800">
                        <div
                          className="h-full rounded-full bg-gradient-to-r from-brand-500 to-indigo-500 transition-all duration-500"
                          style={{ width: `${Math.round(v * 100)}%` }}
                        />
                      </div>
                      <span className="w-10 text-right font-mono font-extrabold text-slate-300">{Math.round(v * 100)}%</span>
                    </div>
                  ))}
                </div>

                <p className="mt-3 text-[11px] text-slate-500 font-mono">
                  {delayRes.line} · {delayRes.from_station} → {delayRes.to_station}
                </p>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Smart Recommendations Matrix Table */}
      <div className="card mt-5 border-slate-800">
        <div className="flex items-center gap-3 border-b border-slate-800 px-5 py-4">
          <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-amber-500/15 border border-amber-500/30 text-amber-400">
            <Lightbulb className="h-4 w-4" />
          </span>
          <div>
            <h3 className="font-extrabold tracking-tight text-white">Smart Frequency Recommendations Matrix</h3>
            <p className="text-xs text-slate-400">Demand-driven headway adjustments calculated per station</p>
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="table-base">
            <thead>
              <tr>
                <th>Station</th>
                <th>Current Headway</th>
                <th>Recommended Headway</th>
                <th>Capacity Utilization</th>
                <th>AI Rationale</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/80">
              {recs.map((r) => (
                <tr key={r.station_id} className="hover:bg-slate-850/60 transition">
                  <td className="font-extrabold text-white">{r.station_name}</td>
                  <td className="font-mono text-slate-400">{r.current_headway_min}m</td>
                  <td>
                    <span
                      className={`inline-flex rounded-lg px-2.5 py-1 text-xs font-mono font-extrabold border ${
                        r.recommended_headway_min < r.current_headway_min
                          ? "bg-emerald-500/15 text-emerald-300 border-emerald-500/30"
                          : "bg-slate-800 text-slate-300 border-slate-700"
                      }`}
                    >
                      {r.recommended_headway_min}m
                    </span>
                  </td>
                  <td>
                    <div className="flex items-center gap-2.5">
                      <div className="h-1.5 w-24 overflow-hidden rounded-full bg-slate-800">
                        <div
                          className="h-full rounded-full bg-gradient-to-r from-brand-500 to-emerald-400"
                          style={{ width: `${Math.min(100, r.capacity_utilization_pct)}%` }}
                        />
                      </div>
                      <span className="text-xs font-mono text-slate-400">{r.capacity_utilization_pct}%</span>
                    </div>
                  </td>
                  <td className="max-w-xs whitespace-normal text-xs text-slate-400">{r.reason}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Traffic Pattern Analysis Table */}
      <div className="card mt-5 border-slate-800">
        <div className="flex items-center gap-3 border-b border-slate-800 px-5 py-4">
          <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-sky-500/15 border border-sky-500/30 text-sky-400">
            <TrendingUp className="h-4 w-4" />
          </span>
          <div>
            <h3 className="font-extrabold tracking-tight text-white">Historical Traffic Pattern Analysis</h3>
            <p className="text-xs text-slate-400">Peak hour detection & weekday vs weekend multiplier factors</p>
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="table-base">
            <thead>
              <tr>
                <th>Station</th>
                <th>Line</th>
                <th>AM Peak</th>
                <th>PM Peak</th>
                <th>Dominant Peak</th>
                <th>Peak Occupancy</th>
                <th>Weekend Factor</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/80">
              {patterns.map((p) => (
                <tr key={p.station_id} className="hover:bg-slate-850/60 transition">
                  <td className="font-extrabold text-white">{p.station_name}</td>
                  <td className="text-slate-400">{p.line}</td>
                  <td className="font-mono">{String(p.am_peak_hour).padStart(2, "0")}:00</td>
                  <td className="font-mono">{String(p.pm_peak_hour).padStart(2, "0")}:00</td>
                  <td>
                    <span className="rounded-lg bg-brand-500/20 border border-brand-500/30 px-2 py-0.5 text-xs font-mono font-extrabold text-brand-300">
                      {String(p.peak_hour).padStart(2, "0")}:00
                    </span>
                  </td>
                  <td className="font-mono font-bold text-white">{p.peak_occupancy_pct}%</td>
                  <td className={p.weekend_factor < 0.8 ? "font-mono font-bold text-emerald-400" : "font-mono text-slate-400"}>
                    {p.weekend_factor}×
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </DashboardLayout>
  );
}

export default withAuth(Predictions);