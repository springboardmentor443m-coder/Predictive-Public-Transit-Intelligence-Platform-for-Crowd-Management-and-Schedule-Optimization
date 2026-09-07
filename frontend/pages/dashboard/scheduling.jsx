import { useCallback, useEffect, useState } from "react";
import { Loader2, Plus, Sparkles, Trash2, Zap } from "lucide-react";
import DashboardLayout from "../../components/DashboardLayout";
import StatusBadge from "../../components/StatusBadge";
import { withAuth, useAuth } from "../../lib/auth";
import api from "../../lib/api";

function Scheduling() {
  const { hasRole } = useAuth();
  const canEdit = hasRole("admin", "operator");

  const [schedules, setSchedules] = useState([]);
  const [trains, setTrains] = useState([]);
  const [stations, setStations] = useState([]);
  const [recs, setRecs] = useState([]);
  const [recsState, setRecsState] = useState("loading"); // loading | loaded | error
  const [schedulesState, setSchedulesState] = useState("loading");
  const [showForm, setShowForm] = useState(false);
  const [busy, setBusy] = useState(false);
  const [filter, setFilter] = useState("all");
  const [form, setForm] = useState({
    train_id: "",
    station_id: "",
    direction: "northbound",
    arrival: "",
    headway_min: 5,
    is_peak: "no",
  });

  const load = useCallback(async () => {
    const st = await api.get("/stations").catch(() => null);
    if (st) setStations(st.data);
    api
      .get("/predictions/recommendations")
      .then((res) => {
        setRecs(res.data);
        setRecsState("loaded");
      })
      .catch(() => setRecsState((prev) => (prev === "loaded" ? prev : "error")));
    try {
      const sc = await api.get("/scheduling/schedules?limit=200");
      setSchedules(sc.data);
      setSchedulesState("loaded");
      // trains endpoint not exposed; derive unique train ids from schedules
      const ids = [...new Set(sc.data.map((s) => s.train_id))];
      setTrains(ids);
      if (!form.train_id && ids.length) setForm((f) => ({ ...f, train_id: ids[0] }));
      if (!form.station_id && st?.data?.length) setForm((f) => ({ ...f, station_id: st.data[0].id }));
    } catch {
      setSchedulesState("error");
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    load();
    const iv = setInterval(load, 30000);
    return () => clearInterval(iv);
  }, [load]);

  async function createSchedule(e) {
    e.preventDefault();
    setBusy(true);
    try {
      const arrival = new Date(form.arrival);
      await api.post("/scheduling/schedules", {
        id: `SCH-${form.train_id}-${Date.now()}`,
        train_id: form.train_id,
        station_id: form.station_id,
        direction: form.direction,
        arrival: arrival.toISOString(),
        departure: new Date(arrival.getTime() + 30000).toISOString(),
        headway_min: Number(form.headway_min),
        status: "on_time",
        delay_min: 0,
        is_peak: form.is_peak,
      });
      setShowForm(false);
      load();
    } catch (err) {
      alert(err?.response?.data?.detail || "Failed to create schedule");
    } finally {
      setBusy(false);
    }
  }

  async function applyHeadway(stationId) {
    try {
      const res = await api.post(`/scheduling/apply-headway/${stationId}`, {});
      alert(
        `Applied ${res.data.applied_headway_min} min headway at ${res.data.station_name}\n` +
        `${res.data.schedules_updated} schedules updated (${res.data.source}).`
      );
      load();
    } catch (err) {
      alert(err?.response?.data?.detail || "Failed to apply headway");
    }
  }

  async function reportDelay(s) {
    const val = prompt(`Report delay (minutes) for ${s.train_id} at ${s.station_id}:`, "5");
    if (val === null) return;
    try {
      await api.post(`/scheduling/delay/${s.id}`, { delay_min: Number(val) || 0 });
      load();
    } catch (err) {
      alert(err?.response?.data?.detail || "Failed to report delay");
    }
  }

  async function removeSchedule(id) {
    if (!confirm("Delete this schedule entry?")) return;
    try {
      await api.delete(`/scheduling/schedules/${id}`);
      load();
    } catch {}
  }

  const filtered = schedules.filter((s) => filter === "all" || s.status === filter);

  return (
    <DashboardLayout
      title="Scheduling Management"
      subtitle="Timetable operations · peak-hour optimization · delay handling"
    >
      {/* Optimizer strip */}
      <div className="card card-pad">
        <div className="mb-3 flex items-center gap-2">
          <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-brand-50 text-brand-600">
            <Sparkles className="h-4 w-4" />
          </span>
          <div>
            <h3 className="font-semibold text-slate-900">AI Frequency Recommendations</h3>
            <p className="text-xs text-slate-500">Demand-driven headway suggestions per station</p>
          </div>
        </div>
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 xl:grid-cols-5">
          {recs.slice(0, 5).map((r) => (
            <div key={r.station_id} className="rounded-xl border border-slate-200 p-3">
              <p className="truncate text-sm font-semibold text-slate-800">{r.station_name}</p>
              <div className="mt-1 flex items-baseline gap-1.5">
                <span className="text-lg font-bold text-slate-500 line-through decoration-slate-300">
                  {r.current_headway_min}m
                </span>
                <Zap className="h-3.5 w-3.5 text-brand-500" />
                <span
                  className={`text-lg font-bold ${
                    r.recommended_headway_min < r.current_headway_min ? "text-emerald-600" : "text-slate-700"
                  }`}
                >
                  {r.recommended_headway_min}m
                </span>
              </div>
              <p className="mt-0.5 text-[11px] text-slate-400">Utilization {r.capacity_utilization_pct}%</p>
              {canEdit && (
                <button
                  onClick={() => applyHeadway(r.station_id)}
                  className="mt-2 w-full rounded-md bg-brand-50 px-2 py-1 text-[11px] font-bold uppercase tracking-wide text-brand-700 transition hover:bg-brand-100"
                >
                  Apply
                </button>
              )}
            </div>
          ))}
          {recsState === "loading" && recs.length === 0 && (
            <p className="col-span-full py-4 text-center text-sm text-slate-400">Loading recommendations…</p>
          )}
          {recsState === "error" && recs.length === 0 && (
            <p className="col-span-full py-4 text-center text-sm text-rose-500">
              Could not load recommendations. Check your connection and try again.
            </p>
          )}
          {recsState === "loaded" && recs.length === 0 && (
            <p className="col-span-full py-4 text-center text-sm text-slate-400">
              No recommendations right now — all stations are within capacity targets.
            </p>
          )}
        </div>
      </div>

      {/* Schedules table */}
      <div className="card mt-4">
        <div className="flex flex-wrap items-center gap-3 border-b border-slate-200 px-5 py-4">
          <h3 className="font-semibold text-slate-900">Train Schedules</h3>
          <select className="input w-auto py-1.5 text-xs" value={filter} onChange={(e) => setFilter(e.target.value)}>
            <option value="all">All statuses</option>
            <option value="on_time">On time</option>
            <option value="delayed">Delayed</option>
          </select>
          <span className="text-xs text-slate-400">{filtered.length} entries</span>
          {canEdit && (
            <button onClick={() => setShowForm(true)} className="btn-primary ml-auto py-1.5">
              <Plus className="h-4 w-4" /> New schedule
            </button>
          )}
        </div>

        <div className="overflow-x-auto">
          <table className="table-base">
            <thead>
              <tr>
                <th>Train</th>
                <th>Station</th>
                <th>Direction</th>
                <th>Arrival</th>
                <th>Headway</th>
                <th>Peak</th>
                <th>Status</th>
                <th>Delay</th>
                {canEdit && <th className="text-right">Actions</th>}
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {filtered.slice(0, 50).map((s) => (
                <tr key={s.id}>
                  <td className="font-semibold text-slate-800">{s.train_id}</td>
                  <td>{s.station_id}</td>
                  <td className="capitalize">{s.direction}</td>
                  <td>{new Date(s.arrival).toLocaleString([], { month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" })}</td>
                  <td>{s.headway_min} min</td>
                  <td>
                    <StatusBadge value={s.is_peak === "yes" ? "high" : "low"} />
                  </td>
                  <td>
                    <StatusBadge value={s.status} />
                  </td>
                  <td className={s.delay_min > 0 ? "font-semibold text-amber-600" : "text-slate-400"}>
                    {s.delay_min > 0 ? `+${s.delay_min} min` : "—"}
                  </td>
                  {canEdit && (
                    <td className="text-right">
                      <button
                        onClick={() => reportDelay(s)}
                        className="mr-2 rounded-md px-2 py-1 text-xs font-semibold text-amber-600 hover:bg-amber-50"
                      >
                        Report delay
                      </button>
                      <button
                        onClick={() => removeSchedule(s.id)}
                        className="rounded-md p-1.5 text-slate-400 hover:bg-rose-50 hover:text-rose-600"
                        title="Delete"
                      >
                        <Trash2 className="h-4 w-4" />
                      </button>
                    </td>
                  )}
                </tr>
              ))}
              {schedulesState === "loading" && filtered.length === 0 && (
                <tr>
                  <td colSpan={canEdit ? 9 : 8} className="py-10 text-center text-sm text-slate-400">
                    Loading schedules…
                  </td>
                </tr>
              )}
              {schedulesState === "error" && filtered.length === 0 && (
                <tr>
                  <td colSpan={canEdit ? 9 : 8} className="py-10 text-center text-sm text-rose-500">
                    Could not load schedules. Check your connection and try again.
                  </td>
                </tr>
              )}
              {schedulesState === "loaded" && filtered.length === 0 && (
                <tr>
                  <td colSpan={canEdit ? 9 : 8} className="py-10 text-center text-sm text-slate-400">
                    No schedules found.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Create modal */}
      {showForm && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 p-4" onClick={() => setShowForm(false)}>
          <div className="card w-full max-w-lg p-6" onClick={(e) => e.stopPropagation()}>
            <h3 className="text-lg font-bold text-slate-900">New Schedule Entry</h3>
            <form onSubmit={createSchedule} className="mt-4 grid grid-cols-2 gap-4">
              <div>
                <label className="label">Train</label>
                <select className="input" value={form.train_id} onChange={(e) => setForm({ ...form, train_id: e.target.value })}>
                  {trains.map((t) => (
                    <option key={t} value={t}>{t}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="label">Station</label>
                <select className="input" value={form.station_id} onChange={(e) => setForm({ ...form, station_id: e.target.value })}>
                  {stations.map((s) => (
                    <option key={s.id} value={s.id}>{s.name}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="label">Direction</label>
                <select className="input" value={form.direction} onChange={(e) => setForm({ ...form, direction: e.target.value })}>
                  <option value="northbound">Northbound</option>
                  <option value="southbound">Southbound</option>
                </select>
              </div>
              <div>
                <label className="label">Arrival</label>
                <input type="datetime-local" required className="input" value={form.arrival} onChange={(e) => setForm({ ...form, arrival: e.target.value })} />
              </div>
              <div>
                <label className="label">Headway (min)</label>
                <input type="number" min="2" max="30" className="input" value={form.headway_min} onChange={(e) => setForm({ ...form, headway_min: e.target.value })} />
              </div>
              <div>
                <label className="label">Peak service</label>
                <select className="input" value={form.is_peak} onChange={(e) => setForm({ ...form, is_peak: e.target.value })}>
                  <option value="no">No</option>
                  <option value="yes">Yes</option>
                </select>
              </div>
              <div className="col-span-2 mt-2 flex justify-end gap-2">
                <button type="button" className="btn-ghost" onClick={() => setShowForm(false)}>
                  Cancel
                </button>
                <button type="submit" disabled={busy} className="btn-primary">
                  {busy && <Loader2 className="h-4 w-4 animate-spin" />}
                  Create schedule
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </DashboardLayout>
  );
}

export default withAuth(Scheduling);
