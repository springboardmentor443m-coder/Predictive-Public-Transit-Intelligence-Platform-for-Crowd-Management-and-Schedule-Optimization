import { useEffect, useState } from "react";
import { Download, Loader2, Printer, Sparkles } from "lucide-react";
import {
  Bar, BarChart, CartesianGrid, Cell, Legend, Line, LineChart,
  PolarAngleAxis, PolarGrid, Radar, RadarChart, ResponsiveContainer, Tooltip, XAxis, YAxis,
} from "recharts";
import DashboardLayout from "../../components/DashboardLayout";
import InsightPanel from "../../components/InsightPanel";
import KpiCard from "../../components/KpiCard";
import { congestionColor } from "../../components/StatusBadge";
import { withAuth } from "../../lib/auth";
import { useToast } from "../../components/ToastContext";
import api from "../../lib/api";
import { downloadCsv } from "../../lib/csv";

function Analytics() {
  const { showToast } = useToast();
  const [overview, setOverview] = useState(null);
  const [traffic, setTraffic] = useState([]);
  const [perf, setPerf] = useState([]);
  const [insights, setInsights] = useState(null);
  const [trafficHours, setTrafficHours] = useState(24);
  const [histDate, setHistDate] = useState("");
  const [histHour, setHistHour] = useState("now");

  const windowLabel = `last ${trafficHours}h`;
  const anchorLabel = histDate
    ? `as-of ${histDate} ${histHour === "now" ? "00:00" : `${histHour}:00`}`
    : `rolling ${windowLabel}`;

  const today = new Date();
  const minDate = new Date(today.getTime() - 6 * 24 * 3600 * 1000).toISOString().slice(0, 10);
  const maxDate = today.toISOString().slice(0, 10);

  useEffect(() => {
    const anchor = histDate
      ? `&start_time=${encodeURIComponent(`${histDate}T${histHour === "now" ? "00" : histHour}:00:00`)}`
      : "";
    Promise.all([
      api.get("/analytics/overview"),
      api.get(`/analytics/traffic?hours=${trafficHours}${anchor}`),
      api.get(`/analytics/station-performance?limit=10&hours=${trafficHours}${anchor}`),
      api.get("/analytics/insights").catch(() => null),
    ])
      .then(([ov, tr, pf, ins]) => {
        setOverview(ov.data);
        setTraffic(tr.data.map((t) => ({ ...t, label: `${String(t.hour).padStart(2, "0")}:00` })));
        setPerf(pf.data);
        if (ins) setInsights(ins.data);
      })
      .catch(() => {});
  }, [trafficHours, histDate, histHour]);

  const radarData = perf.slice(0, 6).map((p) => ({
    station: p.station_name.length > 12 ? p.station_name.slice(0, 11) + "…" : p.station_name,
    congestion: p.congestion_score,
    punctuality: p.punctuality_pct ?? null,
  }));

  function exportPerf() {
    downloadCsv(`metroflow-station-performance-${Date.now()}.csv`, perf, [
      { label: "station_id", key: "station_id" },
      { label: "station_name", key: "station_name" },
      { label: "avg_occupancy_pct", key: "avg_occupancy_pct" },
      { label: "peak_occupancy_pct", key: "peak_occupancy_pct" },
      { label: "congestion_score", key: "congestion_score" },
      { label: "entries_total", key: "entries_total" },
      { label: "exits_total", key: "exits_total" },
      { label: "punctuality_pct", key: "punctuality_pct" },
    ]);
    showToast("Exported station performance report CSV", "success");
  }

  function exportTraffic() {
    downloadCsv(`metroflow-traffic-${Date.now()}.csv`, traffic, [
      { label: "hour", key: "hour" },
      { label: "label", key: "label" },
      { label: "passenger_k", key: "passenger_k" },
      { label: "congestion_level", key: "congestion_level" },
    ]);
    showToast("Exported hourly traffic CSV", "success");
  }

  return (
    <DashboardLayout title="Analytics & Executive Reports" subtitle="Network performance metrics · traffic volume analysis · station health radar">
      {/* Overview KPIs */}
      <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 xl:grid-cols-4">
        <KpiCard label="On-time Performance" value={overview ? `${overview.on_time_pct}%` : "—"} accent="emerald" />
        <KpiCard label="Avg Network Occupancy" value={overview ? `${overview.avg_occupancy_pct}%` : "—"} accent="brand" />
        <KpiCard label="Delayed Services" value={overview ? overview.delayed_count ?? "—" : "—"} accent="amber" />
        <KpiCard label="Open Alerts" value={overview?.active_alerts ?? "—"} accent={overview?.active_alerts > 3 ? "rose" : "sky"} />
      </div>

      {/* AI Operational Insights */}
      <div className="mt-5">
        <InsightPanel insights={insights} />
      </div>

      {/* Export Bar Card */}
      <div className="mt-5 card card-pad border-slate-800 flex flex-wrap items-center justify-between gap-4">
        <div>
          <h3 className="font-extrabold tracking-tight text-white flex items-center gap-2">
            <Sparkles className="h-4 w-4 text-brand-400" /> Operational Data Export & Reporting
          </h3>
          <p className="text-xs text-slate-400">Download auditable datasets in CSV format or print executive reports</p>
        </div>

        <div className="flex flex-wrap items-center gap-2.5">
          <button onClick={exportPerf} className="btn-ghost text-xs py-2 px-3 font-bold">
            <Download className="h-3.5 w-3.5 text-brand-400" /> Station Performance CSV
          </button>
          <button onClick={exportTraffic} className="btn-ghost text-xs py-2 px-3 font-bold">
            <Download className="h-3.5 w-3.5 text-emerald-400" /> Traffic Volume CSV
          </button>
          <button onClick={() => window.print()} className="btn-ghost text-xs py-2 px-3 font-bold no-print">
            <Printer className="h-3.5 w-3.5 text-slate-400" /> Print PDF Report
          </button>
        </div>
      </div>

      {/* Shared Historical Data Tracker — drives traffic, radar, tables and bar chart */}
      <div className="mt-5 card card-pad border-slate-800">
        <div className="flex flex-wrap items-end gap-4">
          <div className="mr-auto">
            <h3 className="font-extrabold tracking-tight text-white">Historical Data Tracker</h3>
            <p className="text-xs text-slate-400">
              Pick an as-of date/time to replay historical analytics — or use the rolling window.
            </p>
          </div>
          <div>
            <label className="label">As-of Date</label>
            <input
              type="date"
              className="input py-1.5 text-xs"
              value={histDate}
              min={minDate}
              max={maxDate}
              onChange={(e) => setHistDate(e.target.value)}
            />
          </div>
          <div>
            <label className="label">Start Hour</label>
            <select
              className="input py-1.5 text-xs"
              value={histHour}
              disabled={!histDate}
              onChange={(e) => setHistHour(e.target.value)}
            >
              <option value="now">12:00 AM</option>
              {Array.from({ length: 24 }, (_, h) => (
                <option key={h} value={String(h).padStart(2, "0")}>
                  {String(h).padStart(2, "0")}:00
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="label">Window</label>
            <select
              className="input py-1.5 text-xs"
              value={trafficHours}
              onChange={(e) => setTrafficHours(Number(e.target.value))}
            >
              <option value="24">Last 24 hours</option>
              <option value="48">Last 48 hours (2 days)</option>
              <option value="72">Last 72 hours (3 days)</option>
              <option value="168">Last 7 days</option>
            </select>
          </div>
          {histDate && (
            <button onClick={() => { setHistDate(""); setHistHour("now"); }} className="btn-ghost py-1.5 text-xs font-bold">
              Reset to live
            </button>
          )}
        </div>
        <div className="mt-3 font-mono text-[11px] text-brand-400">
          Applied: {trafficHours}h window · {anchorLabel}
        </div>
      </div>

      {/* Charts Grid */}
      <div className="mt-5 grid grid-cols-1 gap-5 xl:grid-cols-2">
        {/* Hourly Passenger Traffic Chart */}
        <div className="card card-pad border-slate-800">
          <div className="mb-4 flex flex-wrap items-start justify-between gap-3">
            <div>
              <h3 className="font-extrabold tracking-tight text-white">Hourly Passenger Throughput Volume</h3>
              <p className="text-xs text-slate-400">
                Estimated passenger volume (thousands per hour) · {anchorLabel}
              </p>
            </div>
          </div>
          
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={traffic} margin={{ left: -10, right: 10 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
              <XAxis dataKey="label" tick={{ fontSize: 10, fill: "#94a3b8" }} interval={Math.max(0, Math.round(trafficHours / 12) - 1)} stroke="#334155" />
              <YAxis unit="k" tick={{ fontSize: 11, fill: "#94a3b8" }} stroke="#334155" />
              <Tooltip contentStyle={{ backgroundColor: "#0f172a", borderColor: "#334155", borderRadius: 12, fontSize: 12, color: "#fff" }} />
              <Line type="monotone" dataKey="passenger_k" name="Passengers (k)" stroke="#3b82f6" strokeWidth={3} dot={false} />
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* Station Health Radar */}
        <div className="card card-pad border-slate-800">
          <h3 className="font-extrabold tracking-tight text-white">Station Health Radar</h3>
          <p className="mb-4 text-xs text-slate-400">
            Congestion Score vs Punctuality % (Top 6 major stations) · {anchorLabel}
          </p>

          <ResponsiveContainer width="100%" height={300}>
            <RadarChart data={radarData} outerRadius="70%">
              <PolarGrid stroke="#1e293b" />
              <PolarAngleAxis dataKey="station" tick={{ fontSize: 10, fill: "#94a3b8" }} />
              <Tooltip contentStyle={{ backgroundColor: "#0f172a", borderColor: "#334155", borderRadius: 12, fontSize: 12, color: "#fff" }} />
              <Legend wrapperStyle={{ fontSize: 12 }} />
              <Radar name="Congestion Score" dataKey="congestion" stroke="#f97316" fill="#f97316" fillOpacity={0.3} />
              <Radar name="Punctuality %" dataKey="punctuality" stroke="#3b82f6" fill="#3b82f6" fillOpacity={0.3} />
            </RadarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Station Performance Detailed Report Table */}
      <div className="card mt-5 border-slate-800">
        <div className="flex items-center justify-between border-b border-slate-800 px-5 py-4">
          <div>
            <h3 className="font-extrabold tracking-tight text-white">Station Performance Detailed Report</h3>
            <p className="text-xs text-slate-400">Ranked by congestion score — worst performing stations first · {anchorLabel}</p>
          </div>
          <button onClick={exportPerf} className="btn-ghost no-print py-1.5 text-xs font-bold">
            <Download className="h-3.5 w-3.5 text-brand-400" /> Export CSV
          </button>
        </div>

        <div className="overflow-x-auto">
          <table className="table-base">
            <thead>
              <tr>
                <th>#</th>
                <th>Station</th>
                <th>Avg Occupancy</th>
                <th>Peak Occupancy</th>
                <th>Congestion Score</th>
                <th>Entries Total ({trafficHours}h)</th>
                <th>Exits Total ({trafficHours}h)</th>
                <th>Punctuality Rate</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/80">
              {perf.map((p, i) => (
                <tr key={p.station_id} className="hover:bg-slate-850/60 transition">
                  <td className="font-mono text-slate-500">{i + 1}</td>
                  <td className="font-extrabold text-white">{p.station_name}</td>
                  <td className="font-mono text-slate-300">{p.avg_occupancy_pct}%</td>
                  <td className="font-mono font-bold text-white">{p.peak_occupancy_pct}%</td>
                  <td>
                    <div className="flex items-center gap-2.5">
                      <div className="h-1.5 w-24 overflow-hidden rounded-full bg-slate-800">
                        <div
                          className="h-full rounded-full bg-gradient-to-r from-emerald-400 via-amber-400 to-rose-500"
                          style={{ width: `${Math.min(100, p.congestion_score)}%` }}
                        />
                      </div>
                      <span className="text-xs font-mono text-slate-400">{p.congestion_score}</span>
                    </div>
                  </td>
                  <td className="font-mono">{p.entries_total.toLocaleString()}</td>
                  <td className="font-mono">{p.exits_total.toLocaleString()}</td>
                  <td>
                    {p.punctuality_pct == null ? (
                      <span className="font-mono text-slate-500">—</span>
                    ) : (
                      <span
                        className={`font-mono font-extrabold ${
                          p.punctuality_pct >= 90 ? "text-emerald-400" : "text-amber-400"
                        }`}
                      >
                        {p.punctuality_pct}%
                      </span>
                    )}
                  </td>
                </tr>
              ))}
              {perf.length === 0 && (
                <tr>
                  <td colSpan={8} className="py-12 text-center text-sm text-slate-500">
                    <Loader2 className="mr-2 inline h-4 w-4 animate-spin text-brand-400" /> Loading performance report...
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Bar chart */}
      <div className="card card-pad mt-5 border-slate-800">
        <h3 className="font-extrabold tracking-tight text-white">{trafficHours}-Hour Average Occupancy per Station</h3>
        <p className="mb-4 text-xs text-slate-400">Color mapped by congestion level · {anchorLabel}</p>

        <ResponsiveContainer width="100%" height={260}>
          <BarChart data={perf.slice().reverse()} margin={{ left: -10, right: 10 }}>
            <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#1e293b" />
            <XAxis dataKey="station_name" tick={{ fontSize: 9, fill: "#94a3b8" }} interval={0} angle={-20} textAnchor="end" height={50} stroke="#334155" />
            <YAxis unit="%" tick={{ fontSize: 11, fill: "#94a3b8" }} stroke="#334155" domain={[0, 100]} />
            <Tooltip contentStyle={{ backgroundColor: "#0f172a", borderColor: "#334155", borderRadius: 12, fontSize: 12, color: "#fff" }} />
            <Bar dataKey="avg_occupancy_pct" name="Avg Occupancy %" radius={[8, 8, 0, 0]} barSize={24}>
              {perf.slice().reverse().map((p) => (
                <Cell key={p.station_id} fill={congestionColor(p.avg_occupancy_pct)} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </DashboardLayout>
  );
}

export default withAuth(Analytics);
