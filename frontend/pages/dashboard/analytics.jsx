import { useEffect, useState } from "react";
import { Loader2 } from "lucide-react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Line,
  LineChart,
  PolarAngleAxis,
  PolarGrid,
  Radar,
  RadarChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import DashboardLayout from "../../components/DashboardLayout";
import KpiCard from "../../components/KpiCard";
import { congestionColor } from "../../components/StatusBadge";
import { withAuth } from "../../lib/auth";
import api from "../../lib/api";

function Analytics() {
  const [overview, setOverview] = useState(null);
  const [traffic, setTraffic] = useState([]);
  const [perf, setPerf] = useState([]);

  useEffect(() => {
    Promise.all([
      api.get("/analytics/overview"),
      api.get("/analytics/traffic?hours=24"),
      api.get("/analytics/station-performance?limit=10"),
    ])
      .then(([ov, tr, pf]) => {
        setOverview(ov.data);
        setTraffic(tr.data.map((t) => ({ ...t, label: `${String(t.hour).padStart(2, "0")}:00` })));
        setPerf(pf.data);
      })
      .catch(() => {});
  }, []);

  const radarData = perf.slice(0, 6).map((p) => ({
    station: p.station_name.length > 12 ? p.station_name.slice(0, 11) + "…" : p.station_name,
    congestion: p.congestion_score,
    punctuality: p.punctuality_pct,
  }));

  return (
    <DashboardLayout
      title="Analytics & Reports"
      subtitle="Traffic analytics · station performance · operational monitoring"
    >
      {/* KPIs */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <KpiCard label="On-time Performance" value={overview ? `${overview.on_time_pct}%` : "—"} accent="emerald" />
        <KpiCard label="Avg Network Occupancy" value={overview ? `${overview.avg_occupancy_pct}%` : "—"} accent="brand" />
        <KpiCard label="Delayed Services" value={overview ? overview.delayed_count ?? "—" : "—"} accent="amber" />
        <KpiCard label="Open Alerts" value={overview?.active_alerts ?? "—"} accent={overview?.active_alerts > 3 ? "rose" : "sky"} />
      </div>

      <div className="mt-4 grid grid-cols-1 gap-4 xl:grid-cols-2">
        {/* Traffic line */}
        <div className="card card-pad">
          <h3 className="font-semibold text-slate-900">Hourly Passenger Traffic</h3>
          <p className="mb-3 text-xs text-slate-500">Network-wide estimated passengers (thousands)</p>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={traffic} margin={{ left: -12, right: 8 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
              <XAxis dataKey="label" tick={{ fontSize: 10 }} interval={2} stroke="#94a3b8" />
              <YAxis unit="k" tick={{ fontSize: 11 }} stroke="#94a3b8" />
              <Tooltip contentStyle={{ borderRadius: 8, fontSize: 12 }} />
              <Line type="monotone" dataKey="passenger_k" name="Passengers (k)" stroke="#3382fc" strokeWidth={2.5} dot={false} />
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* Station radar */}
        <div className="card card-pad">
          <h3 className="font-semibold text-slate-900">Station Health Radar</h3>
          <p className="mb-3 text-xs text-slate-500">Congestion score vs punctuality (top 6 stations)</p>
          <ResponsiveContainer width="100%" height={300}>
            <RadarChart data={radarData} outerRadius="72%">
              <PolarGrid stroke="#e2e8f0" />
              <PolarAngleAxis dataKey="station" tick={{ fontSize: 10 }} />
              <Tooltip contentStyle={{ borderRadius: 8, fontSize: 12 }} />
              <Legend wrapperStyle={{ fontSize: 12 }} />
              <Radar name="Congestion score" dataKey="congestion" stroke="#f97316" fill="#f97316" fillOpacity={0.25} />
              <Radar name="Punctuality %" dataKey="punctuality" stroke="#3382fc" fill="#3382fc" fillOpacity={0.25} />
            </RadarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Station performance table */}
      <div className="card mt-4">
        <div className="flex items-center justify-between border-b border-slate-200 px-5 py-4">
          <div>
            <h3 className="font-semibold text-slate-900">Station Performance Report</h3>
            <p className="text-xs text-slate-500">Ranked by congestion score — worst first</p>
          </div>
          <button onClick={() => window.print()} className="btn-ghost py-1.5 text-xs">
            Export / Print
          </button>
        </div>
        <div className="overflow-x-auto">
          <table className="table-base">
            <thead>
              <tr>
                <th>#</th>
                <th>Station</th>
                <th>Avg occupancy</th>
                <th>Peak occupancy</th>
                <th>Congestion score</th>
                <th>Entries (48h)</th>
                <th>Exits (48h)</th>
                <th>Punctuality</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {perf.map((p, i) => (
                <tr key={p.station_id}>
                  <td className="text-slate-400">{i + 1}</td>
                  <td className="font-semibold text-slate-800">{p.station_name}</td>
                  <td>{p.avg_occupancy_pct}%</td>
                  <td>{p.peak_occupancy_pct}%</td>
                  <td>
                    <div className="flex items-center gap-2">
                      <div className="h-1.5 w-24 overflow-hidden rounded-full bg-slate-100">
                        <div
                          className="h-full rounded-full"
                          style={{
                            width: `${Math.min(100, p.congestion_score)}%`,
                            backgroundColor: congestionColor(p.congestion_score),
                          }}
                        />
                      </div>
                      <span className="text-xs tabular-nums text-slate-500">{p.congestion_score}</span>
                    </div>
                  </td>
                  <td className="tabular-nums">{p.entries_total.toLocaleString()}</td>
                  <td className="tabular-nums">{p.exits_total.toLocaleString()}</td>
                  <td className={p.punctuality_pct >= 90 ? "font-semibold text-emerald-600" : "font-semibold text-amber-600"}>
                    {p.punctuality_pct}%
                  </td>
                </tr>
              ))}
              {perf.length === 0 && (
                <tr>
                  <td colSpan={8} className="py-10 text-center text-sm text-slate-400">
                    <Loader2 className="mr-2 inline h-4 w-4 animate-spin" /> Loading report…
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Congestion distribution */}
      <div className="card card-pad mt-4">
        <h3 className="font-semibold text-slate-900">Average Occupancy by Station</h3>
        <p className="mb-3 text-xs text-slate-500">48-hour rolling average</p>
        <ResponsiveContainer width="100%" height={260}>
          <BarChart data={perf.slice().reverse()} margin={{ left: -12, right: 8 }}>
            <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" />
            <XAxis dataKey="station_name" tick={{ fontSize: 9 }} interval={0} angle={-20} textAnchor="end" height={50} stroke="#94a3b8" />
            <YAxis unit="%" tick={{ fontSize: 11 }} stroke="#94a3b8" domain={[0, 100]} />
            <Tooltip contentStyle={{ borderRadius: 8, fontSize: 12 }} />
            <Bar dataKey="avg_occupancy_pct" name="Avg occupancy %" radius={[6, 6, 0, 0]} barSize={26}>
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
