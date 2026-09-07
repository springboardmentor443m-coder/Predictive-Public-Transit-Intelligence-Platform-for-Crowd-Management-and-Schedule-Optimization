import { useCallback, useEffect, useState } from "react";
import { ArrowDown, ArrowUp, Loader2 } from "lucide-react";
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
import StatusBadge, { congestionColor } from "../../components/StatusBadge";
import { withAuth } from "../../lib/auth";
import api from "../../lib/api";

function CrowdMonitoring() {
  const [stations, setStations] = useState([]);
  const [live, setLive] = useState([]);
  const [heatmap, setHeatmap] = useState([]);
  const [selected, setSelected] = useState("ST01");
  const [history, setHistory] = useState([]);
  const [loadingHist, setLoadingHist] = useState(false);

  useEffect(() => {
    Promise.all([api.get("/stations"), api.get("/crowd/live"), api.get("/crowd/heatmap")])
      .then(([st, lv, hm]) => {
        setStations(st.data);
        setLive(lv.data);
        setHeatmap(hm.data);
        if (st.data.length && !st.data.find((s) => s.id === selected)) {
          setSelected(st.data[0].id);
        }
      })
      .catch(() => {});
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const loadHistory = useCallback((stationId) => {
    setLoadingHist(true);
    api
      .get(`/crowd/station/${stationId}/history?hours=24`)
      .then((res) => {
        setHistory(
          res.data.map((r) => ({
            time: new Date(r.timestamp).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
            entries: r.entries,
            exits: r.exits,
            occupancy: r.occupancy,
          }))
        );
      })
      .catch(() => {})
      .finally(() => setLoadingHist(false));
  }, []);

  useEffect(() => {
    if (selected) loadHistory(selected);
  }, [selected, loadHistory]);

  const selectedStation = stations.find((s) => s.id === selected);
  const selectedLive = live.find((s) => s.station_id === selected);

  return (
    <DashboardLayout
      title="Crowd Monitoring"
      subtitle="Passenger density tracking · congestion heatmaps · inflow/outflow analysis"
    >
      {/* Station cards */}
      <div className="grid grid-cols-2 gap-3 md:grid-cols-3 xl:grid-cols-5">
        {live.map((s) => (
          <button
            key={s.station_id}
            onClick={() => setSelected(s.station_id)}
            className={`card card-pad text-left transition hover:shadow-pop ${
              selected === s.station_id ? "ring-2 ring-brand-500" : ""
            }`}
          >
            <div className="flex items-center justify-between">
              <p className="truncate text-sm font-semibold text-slate-800">{s.station_name}</p>
              <span
                className="h-2.5 w-2.5 shrink-0 rounded-full"
                style={{ backgroundColor: congestionColor(s.occupancy_pct) }}
              />
            </div>
            <p className="mt-1 text-2xl font-bold tabular-nums text-slate-900">{s.occupancy_pct}%</p>
            <div className="mt-1 flex items-center justify-between">
              <span className="text-[11px] font-medium uppercase tracking-wide text-slate-400">{s.line} line</span>
              <StatusBadge value={s.congestion_level} />
            </div>
          </button>
        ))}
      </div>

      {/* Heatmap */}
      <div className="card card-pad mt-4">
        <div className="mb-4 flex items-center justify-between">
          <div>
            <h3 className="font-semibold text-slate-900">Congestion Heatmap — Station × Hour</h3>
            <p className="text-xs text-slate-500">Average occupancy by hour of day across the network</p>
          </div>
        </div>
        <HeatmapGrid points={heatmap} stations={stations.map((s) => ({ id: s.id, name: s.name }))} onSelectStation={setSelected} />
      </div>

      <div className="mt-4 grid grid-cols-1 gap-4 xl:grid-cols-3">
        {/* Inflow/outflow chart */}
        <div className="card card-pad xl:col-span-2">
          <div className="mb-4 flex items-center justify-between">
            <div>
              <h3 className="font-semibold text-slate-900">
                Inflow / Outflow — {selectedStation?.name || "Station"}
              </h3>
              <p className="text-xs text-slate-500">Last 24 hours · gate records</p>
            </div>
            <select className="input w-auto py-1.5" value={selected} onChange={(e) => setSelected(e.target.value)}>
              {stations.map((s) => (
                <option key={s.id} value={s.id}>
                  {s.name}
                </option>
              ))}
            </select>
          </div>
          {loadingHist ? (
            <div className="flex h-[300px] items-center justify-center text-slate-400">
              <Loader2 className="mr-2 h-5 w-5 animate-spin" /> Loading history…
            </div>
          ) : (
            <ResponsiveContainer width="100%" height={300}>
              <AreaChart data={history} margin={{ left: -8, right: 8 }}>
                <defs>
                  <linearGradient id="inGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#3382fc" stopOpacity={0.35} />
                    <stop offset="100%" stopColor="#3382fc" stopOpacity={0.02} />
                  </linearGradient>
                  <linearGradient id="outGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#10b981" stopOpacity={0.3} />
                    <stop offset="100%" stopColor="#10b981" stopOpacity={0.02} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                <XAxis dataKey="time" tick={{ fontSize: 10 }} interval={2} stroke="#94a3b8" />
                <YAxis tick={{ fontSize: 11 }} stroke="#94a3b8" />
                <Tooltip contentStyle={{ borderRadius: 8, fontSize: 12 }} />
                <Legend wrapperStyle={{ fontSize: 12 }} />
                <Area type="monotone" dataKey="entries" name="Entries" stroke="#3382fc" strokeWidth={2} fill="url(#inGrad)" />
                <Area type="monotone" dataKey="exits" name="Exits" stroke="#10b981" strokeWidth={2} fill="url(#outGrad)" />
              </AreaChart>
            </ResponsiveContainer>
          )}
        </div>

        {/* Selected station detail */}
        <div className="card card-pad">
          <h3 className="font-semibold text-slate-900">Station Detail</h3>
          <p className="text-xs text-slate-500">{selectedStation?.name}</p>

          <div className="mt-4 space-y-3">
            <div className="rounded-xl bg-slate-50 p-4 ring-1 ring-slate-200">
              <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Current Occupancy</p>
              <div className="mt-1 flex items-end justify-between">
                <p className="text-3xl font-bold text-slate-900">{selectedLive?.occupancy_pct ?? "—"}%</p>
                <StatusBadge value={selectedLive?.congestion_level || "low"} />
              </div>
              <div className="mt-2 h-2 overflow-hidden rounded-full bg-slate-200">
                <div
                  className="h-full rounded-full transition-all duration-700"
                  style={{
                    width: `${Math.min(100, selectedLive?.occupancy_pct || 0)}%`,
                    backgroundColor: congestionColor(selectedLive?.occupancy_pct || 0),
                  }}
                />
              </div>
              <p className="mt-1.5 text-xs text-slate-400">
                {selectedLive ? `${selectedLive.occupancy} / ${selectedLive.capacity} capacity` : "—"}
              </p>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div className="rounded-xl bg-sky-50 p-3 ring-1 ring-sky-100">
                <p className="flex items-center gap-1 text-xs font-semibold text-sky-700">
                  <ArrowDown className="h-3.5 w-3.5" /> Inflow
                </p>
                <p className="mt-0.5 text-xl font-bold text-sky-800">
                  {selectedLive?.inflow_rate ?? "—"}
                  <span className="text-xs font-medium"> /min</span>
                </p>
              </div>
              <div className="rounded-xl bg-emerald-50 p-3 ring-1 ring-emerald-100">
                <p className="flex items-center gap-1 text-xs font-semibold text-emerald-700">
                  <ArrowUp className="h-3.5 w-3.5" /> Outflow
                </p>
                <p className="mt-0.5 text-xl font-bold text-emerald-800">
                  {selectedLive?.outflow_rate ?? "—"}
                  <span className="text-xs font-medium"> /min</span>
                </p>
              </div>
            </div>

            <dl className="space-y-2 pt-1 text-sm">
              <div className="flex justify-between border-b border-slate-100 pb-2">
                <dt className="text-slate-500">Line</dt>
                <dd className="font-semibold text-slate-800">{selectedStation?.line || "—"}</dd>
              </div>
              <div className="flex justify-between border-b border-slate-100 pb-2">
                <dt className="text-slate-500">Zone</dt>
                <dd className="font-semibold text-slate-800">{selectedStation?.zone || "—"}</dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-slate-500">Hourly Capacity</dt>
                <dd className="font-semibold text-slate-800">
                  {selectedStation?.capacity_per_hour?.toLocaleString() || "—"}
                </dd>
              </div>
            </dl>
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
}

export default withAuth(CrowdMonitoring);
