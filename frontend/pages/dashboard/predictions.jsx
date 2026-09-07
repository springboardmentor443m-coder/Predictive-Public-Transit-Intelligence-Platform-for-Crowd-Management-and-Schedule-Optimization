import { useEffect, useState } from "react";
import { BrainCircuit, Lightbulb, Loader2, TrendingUp } from "lucide-react";
import {
  Area,
  AreaChart,
  CartesianGrid,
  Legend,
  Line,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import DashboardLayout from "../../components/DashboardLayout";
import StatusBadge from "../../components/StatusBadge";
import { withAuth } from "../../lib/auth";
import api from "../../lib/api";

function CrowdTooltip({ active, payload, label }) {
  if (!active || !payload?.length) return null;
  const base = payload.find((p) => p.dataKey === "bandBase")?.value ?? 0;
  const width = payload.find((p) => p.dataKey === "bandWidth")?.value ?? 0;
  const predicted = payload.find((p) => p.dataKey === "predicted")?.value;
  return (
    <div className="rounded-lg bg-white px-3 py-2 text-xs shadow-lg ring-1 ring-slate-200">
      <p className="font-semibold text-slate-700">{label}</p>
      {predicted != null && <p className="text-slate-600">Predicted: {predicted}%</p>}
      {width > 0 && (
        <p className="text-slate-400">
          Range: {Math.round(base)}–{Math.round(base + width)}%
        </p>
      )}
    </div>
  );
}

function Predictions() {
  const [stations, setStations] = useState([]);
  const [stationId, setStationId] = useState("");
  const [crowd, setCrowd] = useState([]);
  const [demand, setDemand] = useState([]);
  const [recs, setRecs] = useState([]);
  const [recsState, setRecsState] = useState("loading");
  const [patterns, setPatterns] = useState([]);
  const [patternsState, setPatternsState] = useState("loading");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api
      .get("/stations/")
      .then((res) => {
        setStations(res.data);
        if (res.data.length) setStationId(res.data[0].id);
      })
      .catch(() => {});
    api
      .get("/predictions/recommendations")
      .then((res) => {
        setRecs(res.data);
        setRecsState("loaded");
      })
      .catch(() => setRecsState("error"));
    api
      .get("/predictions/patterns")
      .then((res) => {
        setPatterns(res.data);
        setPatternsState("loaded");
      })
      .catch(() => setPatternsState("error"));
  }, []);

  useEffect(() => {
    if (!stationId) return;
    setLoading(true);
    Promise.all([
      api.get(`/predictions/crowd?station_id=${stationId}&hours=12`),
      api.get(`/predictions/demand?station_id=${stationId}&hours=12`),
    ])
      .then(([c, d]) => {
        setCrowd(c.data);
        setDemand(d.data);
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [stationId]);

  const crowdChart = crowd.map((p) => ({
    label: `${String(p.hour).padStart(2, "0")}:00`,
    predicted: p.predicted_occupancy_pct,
    bandBase: p.lower,
    bandWidth: Math.max(0, p.upper - p.lower),
  }));

  const demandChart = demand.map((p) => ({
    label: `${String(p.hour).padStart(2, "0")}:00`,
    entries: p.predicted_entries,
    exits: p.predicted_exits,
    peakProb: Math.round(p.peak_probability * 100),
  }));

  const peakHour = demand.reduce(
    (best, cur) => (cur.predicted_entries > best.predicted_entries ? cur : best),
    demand[0] || { hour: "--", predicted_entries: 0 }
  );

  return (
    <DashboardLayout
      title="AI Predictions"
      subtitle="Crowd forecasting · demand prediction · smart recommendations"
    >
      {/* Summary strip */}
      <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
        <div className="card card-pad flex items-center gap-4">
          <span className="flex h-11 w-11 items-center justify-center rounded-xl bg-brand-50 text-brand-600">
            <BrainCircuit className="h-5 w-5" />
          </span>
          <div>
            <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Model</p>
            <p className="font-bold text-slate-900">GradientBoosting · R² 0.98</p>
          </div>
        </div>
        <div className="card card-pad flex items-center gap-4">
          <span className="flex h-11 w-11 items-center justify-center rounded-xl bg-emerald-50 text-emerald-600">
            <TrendingUp className="h-5 w-5" />
          </span>
          <div>
            <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Forecast Peak</p>
            <p className="font-bold text-slate-900">
              {String(peakHour.hour).padStart(2, "0")}:00 · {peakHour.predicted_entries?.toLocaleString()} pax
            </p>
          </div>
        </div>
        <div className="card card-pad">
          <label className="label">Station under analysis</label>
          <select className="input" value={stationId} onChange={(e) => setStationId(e.target.value)}>
            {stations.map((s) => (
              <option key={s.id} value={s.id}>
                {s.name}
              </option>
            ))}
          </select>
        </div>
      </div>

      <div className="mt-4 grid grid-cols-1 gap-4 xl:grid-cols-2">
        {/* Crowd forecast */}
        <div className="card card-pad">
          <h3 className="font-semibold text-slate-900">Crowd Density Forecast — Next 12h</h3>
          <p className="mb-3 text-xs text-slate-500">Predicted occupancy % with confidence band</p>
          {loading ? (
            <div className="flex h-[300px] items-center justify-center text-slate-400">
              <Loader2 className="mr-2 h-5 w-5 animate-spin" /> Running inference…
            </div>
          ) : (
            <ResponsiveContainer width="100%" height={300}>
              <AreaChart data={crowdChart} margin={{ left: -12, right: 8 }}>
                <defs>
                  <linearGradient id="predGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#3382fc" stopOpacity={0.35} />
                    <stop offset="100%" stopColor="#3382fc" stopOpacity={0.02} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                <XAxis dataKey="label" tick={{ fontSize: 10 }} stroke="#94a3b8" />
                <YAxis unit="%" tick={{ fontSize: 11 }} stroke="#94a3b8" domain={[0, 100]} />
                <Tooltip content={<CrowdTooltip />} contentStyle={{ borderRadius: 8, fontSize: 12 }} />
                <Legend wrapperStyle={{ fontSize: 12 }} />
                {/* Confidence band: stacked invisible base (lower) + shaded width
                    renders an area between lower and upper bounds. */}
                <Area
                  name="bandBase"
                  dataKey="bandBase"
                  stackId="band"
                  stroke="none"
                  fill="none"
                  legendType="none"
                  isAnimationActive={false}
                />
                <Area
                  name="Confidence band"
                  dataKey="bandWidth"
                  stackId="band"
                  stroke="none"
                  fill="#3382fc"
                  fillOpacity={0.12}
                  legendType="none"
                />
                <Area
                  name="Predicted occupancy"
                  dataKey="predicted"
                  type="monotone"
                  stroke="#3382fc"
                  strokeWidth={2.5}
                  fill="url(#predGrad)"
                />
              </AreaChart>
            </ResponsiveContainer>
          )}
        </div>

        {/* Demand forecast */}
        <div className="card card-pad">
          <h3 className="font-semibold text-slate-900">Passenger Demand Forecast — Next 12h</h3>
          <p className="mb-3 text-xs text-slate-500">Predicted gate entries vs exits</p>
          {loading ? (
            <div className="flex h-[300px] items-center justify-center text-slate-400">
              <Loader2 className="mr-2 h-5 w-5 animate-spin" /> Running inference…
            </div>
          ) : (
            <ResponsiveContainer width="100%" height={300}>
              <AreaChart data={demandChart} margin={{ left: -8, right: 8 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                <XAxis dataKey="label" tick={{ fontSize: 10 }} stroke="#94a3b8" />
                <YAxis tick={{ fontSize: 11 }} stroke="#94a3b8" />
                <Tooltip contentStyle={{ borderRadius: 8, fontSize: 12 }} />
                <Legend wrapperStyle={{ fontSize: 12 }} />
                <Area type="monotone" name="Entries" dataKey="entries" stroke="#3382fc" strokeWidth={2} fill="#3382fc" fillOpacity={0.08} />
                <Area type="monotone" name="Exits" dataKey="exits" stroke="#10b981" strokeWidth={2} fill="#10b981" fillOpacity={0.08} />
              </AreaChart>
            </ResponsiveContainer>
          )}
        </div>
      </div>

      {/* Recommendations table */}
      <div className="card mt-4">
        <div className="flex items-center gap-2 border-b border-slate-200 px-5 py-4">
          <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-amber-50 text-amber-600">
            <Lightbulb className="h-4 w-4" />
          </span>
          <div>
            <h3 className="font-semibold text-slate-900">Smart Recommendations</h3>
            <p className="text-xs text-slate-500">AI-generated scheduling actions to prevent overcrowding</p>
          </div>
        </div>
        <div className="overflow-x-auto">
          <table className="table-base">
            <thead>
              <tr>
                <th>Station</th>
                <th>Current headway</th>
                <th>Recommended</th>
                <th>Capacity utilization</th>
                <th>Rationale</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {recs.map((r) => (
                <tr key={r.station_id}>
                  <td className="font-semibold text-slate-800">{r.station_name}</td>
                  <td>{r.current_headway_min} min</td>
                  <td>
                    <span
                      className={`inline-flex rounded-md px-2 py-0.5 text-sm font-bold ${
                        r.recommended_headway_min < r.current_headway_min
                          ? "bg-emerald-50 text-emerald-700"
                          : "bg-slate-100 text-slate-600"
                      }`}
                    >
                      {r.recommended_headway_min} min
                    </span>
                  </td>
                  <td>
                    <div className="flex items-center gap-2">
                      <div className="h-1.5 w-24 overflow-hidden rounded-full bg-slate-100">
                        <div
                          className="h-full rounded-full bg-brand-500"
                          style={{ width: `${Math.min(100, r.capacity_utilization_pct)}%` }}
                        />
                      </div>
                      <span className="text-xs tabular-nums text-slate-500">{r.capacity_utilization_pct}%</span>
                    </div>
                  </td>
                  <td className="max-w-xs whitespace-normal text-xs text-slate-500">{r.reason}</td>
                </tr>
              ))}
              {recs.length === 0 && recsState !== "loaded" && (
                <tr>
                  <td colSpan={5} className="py-10 text-center text-sm text-slate-400">
                    {recsState === "error" ? "Could not load recommendations." : "Loading recommendations…"}
                  </td>
                </tr>
              )}
              {recs.length === 0 && recsState === "loaded" && (
                <tr>
                  <td colSpan={5} className="py-10 text-center text-sm text-slate-400">
                    No recommendations available — all stations are within capacity targets.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Traffic pattern analysis */}
      <div className="card mt-4">
        <div className="flex items-center gap-2 border-b border-slate-200 px-5 py-4">
          <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-sky-50 text-sky-600">
            <TrendingUp className="h-4 w-4" />
          </span>
          <div>
            <h3 className="font-semibold text-slate-900">Traffic Pattern Analysis</h3>
            <p className="text-xs text-slate-500">Historical peak-hour detection and weekday/weekend profiling per station</p>
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
            <tbody className="divide-y divide-slate-100">
              {patterns.map((p) => (
                <tr key={p.station_id}>
                  <td className="font-semibold text-slate-800">{p.station_name}</td>
                  <td>{p.line}</td>
                  <td>{String(p.am_peak_hour).padStart(2, "0")}:00</td>
                  <td>{String(p.pm_peak_hour).padStart(2, "0")}:00</td>
                  <td>
                    <span className="rounded-md bg-brand-50 px-2 py-0.5 text-sm font-bold text-brand-700">
                      {String(p.peak_hour).padStart(2, "0")}:00
                    </span>
                  </td>
                  <td>{p.peak_occupancy_pct}%</td>
                  <td className={p.weekend_factor < 0.8 ? "text-emerald-600" : "text-slate-600"}>
                    {p.weekend_factor}×
                  </td>
                </tr>
              ))}
              {patterns.length === 0 && (
                <tr>
                  <td colSpan={7} className="py-10 text-center text-sm text-slate-400">
                    {patternsState === "error"
                      ? "Could not analyze traffic patterns."
                      : patternsState === "loading"
                        ? "Analyzing traffic patterns…"
                        : "No ridership history available yet."}
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Hourly detail cards */}
      <div className="mt-4 grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-6">
        {crowd.slice(0, 6).map((p) => (
          <div key={p.hour} className="card p-4 text-center">
            <p className="text-xs font-semibold uppercase tracking-wide text-slate-400">
              {String(p.hour).padStart(2, "0")}:00
            </p>
            <p className="mt-1 text-xl font-bold tabular-nums text-slate-900">{p.predicted_occupancy_pct}%</p>
            <div className="mt-1.5 flex justify-center">
              <StatusBadge value={p.congestion_level} />
            </div>
          </div>
        ))}
      </div>
    </DashboardLayout>
  );
}

export default withAuth(Predictions);
