import { useCallback, useEffect, useMemo, useState } from "react";
import { Download, Loader2, Pencil, Plus, Search, Sparkles, Trash2, Zap } from "lucide-react";
import DashboardLayout from "../../components/DashboardLayout";
import StatusBadge from "../../components/StatusBadge";
import { withAuth, useAuth } from "../../lib/auth";
import { useToast } from "../../components/ToastContext";
import api from "../../lib/api";
import { downloadCsv } from "../../lib/csv";

const PAGE_SIZE = 12;

function Scheduling() {
  const { hasRole } = useAuth();
  const { showToast } = useToast();
  const canEdit = hasRole("admin", "operator");

  const [schedules, setSchedules] = useState([]);
  const [trains, setTrains] = useState([]);
  const [stations, setStations] = useState([]);
  const [recs, setRecs] = useState([]);
  const [recsState, setRecsState] = useState("loading");
  const [schedulesState, setSchedulesState] = useState("loading");
  const [showForm, setShowForm] = useState(false);
  const [editing, setEditing] = useState(null);
  const [busy, setBusy] = useState(false);
  const [filter, setFilter] = useState("all");
  const [query, setQuery] = useState("");
  const [page, setPage] = useState(0);
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

    api.get("/predictions/recommendations")
      .then((res) => {
        setRecs(res.data);
        setRecsState("loaded");
      })
      .catch(() => setRecsState("error"));

    try {
      const sc = await api.get("/scheduling/schedules?limit=200");
      setSchedules(sc.data);
      setSchedulesState("loaded");
      const ids = [...new Set(sc.data.map((s) => s.train_id))];
      setTrains(ids);
      if (!form.train_id && ids.length) setForm((f) => ({ ...f, train_id: ids[0] }));
      if (!form.station_id && st?.data?.length) setForm((f) => ({ ...f, station_id: st.data[0].id }));
    } catch {
      setSchedulesState("error");
    }
  }, [form.train_id, form.station_id]);

  useEffect(() => {
    load();
    const iv = setInterval(load, 30000);
    return () => clearInterval(iv);
  }, [load]);

  const stationName = useCallback((id) => stations.find((s) => s.id === id)?.name || id, [stations]);

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    return schedules.filter((s) => {
      if (filter !== "all" && s.status !== filter) return false;
      if (!q) return true;
      return `${s.train_id} ${s.station_id} ${stationName(s.station_id)} ${s.direction}`.toLowerCase().includes(q);
    });
  }, [schedules, filter, query, stationName]);

  const pages = Math.max(1, Math.ceil(filtered.length / PAGE_SIZE));
  const pageRows = filtered.slice(page * PAGE_SIZE, page * PAGE_SIZE + PAGE_SIZE);

  useEffect(() => {
    setPage(0);
  }, [filter, query]);

  function openCreate() {
    setEditing(null);
    setShowForm(true);
  }

  function openEdit(s) {
    setEditing(s);
    setForm({
      train_id: s.train_id,
      station_id: s.station_id,
      direction: s.direction,
      arrival: new Date(s.arrival).toISOString().slice(0, 16),
      headway_min: s.headway_min,
      is_peak: s.is_peak,
    });
    setShowForm(true);
  }

  async function saveSchedule(e) {
    e.preventDefault();
    setBusy(true);
    try {
      const arrival = new Date(form.arrival);
      const payload = {
        train_id: form.train_id,
        station_id: form.station_id,
        direction: form.direction,
        arrival: arrival.toISOString(),
        departure: new Date(arrival.getTime() + 30000).toISOString(),
        headway_min: Number(form.headway_min),
        status: editing?.status || "on_time",
        delay_min: editing?.delay_min || 0,
        is_peak: form.is_peak,
      };

      if (editing) {
        await api.put(`/scheduling/schedules/${editing.id}`, { id: editing.id, ...payload });
        showToast(`Updated schedule ${editing.id}`, "success");
      } else {
        await api.post("/scheduling/schedules", { id: `SCH-${form.train_id}-${Date.now()}`, ...payload });
        showToast("Created new timetable entry", "success");
      }

      setShowForm(false);
      setEditing(null);
      load();
    } catch (err) {
      showToast(err?.response?.data?.detail || "Failed to save schedule", "error");
    } finally {
      setBusy(false);
    }
  }

  async function applyHeadway(stationId) {
    try {
      const res = await api.post(`/scheduling/apply-headway/${stationId}`, {});
      showToast(
        `Applied ${res.data.applied_headway_min}m headway at ${res.data.station_name} (${res.data.schedules_updated} updated)`,
        "success"
      );
      load();
    } catch (err) {
      showToast(err?.response?.data?.detail || "Failed to apply headway", "error");
    }
  }

  async function reportDelay(s) {
    const val = prompt(`Report delay (minutes) for ${s.train_id} at ${stationName(s.station_id)}:`, "5");
    if (val === null) return;
    try {
      await api.post(`/scheduling/delay/${s.id}`, { delay_min: Number(val) || 0 });
      showToast(`Reported +${val} min delay on ${s.train_id}`, "warning");
      load();
    } catch (err) {
      showToast(err?.response?.data?.detail || "Failed to report delay", "error");
    }
  }

  async function removeSchedule(id) {
    if (!confirm("Delete this schedule entry?")) return;
    try {
      await api.delete(`/scheduling/schedules/${id}`);
      showToast("Deleted schedule entry", "info");
      load();
    } catch {}
  }

  function exportCsv() {
    downloadCsv(`metroflow-schedules-${Date.now()}.csv`, filtered, [
      { label: "id", key: "id" },
      { label: "train_id", key: "train_id" },
      { label: "station", get: (r) => stationName(r.station_id) },
      { label: "direction", key: "direction" },
      { label: "arrival", key: "arrival" },
      { label: "headway_min", key: "headway_min" },
      { label: "status", key: "status" },
      { label: "delay_min", key: "delay_min" },
    ]);
    showToast("Exported timetables CSV", "success");
  }

  return (
    <DashboardLayout title="Scheduling Management" subtitle="Train timetables · headway optimization · delay dispatch">
      {/* AI Recommendations Section */}
      <div className="card card-pad border-slate-800">
        <div className="mb-4 flex items-center justify-between border-b border-slate-800 pb-3">
          <div className="flex items-center gap-3">
            <span className="flex h-10 w-10 items-center justify-center rounded-2xl bg-brand-500/15 border border-brand-500/30 text-brand-400">
              <Sparkles className="h-5 w-5" />
            </span>
            <div>
              <h3 className="font-extrabold tracking-tight text-white">AI Demand-Driven Headway Recommendations</h3>
              <p className="text-xs text-slate-400">Calculated from peak hour predictions & station capacity targets</p>
            </div>
          </div>
          <span className="text-[11px] font-mono text-slate-500">Live Machine Inference</span>
        </div>

        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 xl:grid-cols-5">
          {recs.slice(0, 5).map((r) => (
            <div
              key={r.station_id}
              className="rounded-2xl border border-slate-800 bg-slate-950/70 p-4 transition hover:border-slate-700"
            >
              <p className="truncate text-xs font-extrabold text-white">{r.station_name}</p>
              
              <div className="mt-2 flex items-baseline gap-2">
                <span className="text-sm font-bold text-slate-500 line-through font-mono">{r.current_headway_min}m</span>
                <Zap className="h-3.5 w-3.5 text-brand-400" />
                <span
                  className={`text-xl font-extrabold font-mono ${
                    r.recommended_headway_min < r.current_headway_min ? "text-emerald-400" : "text-white"
                  }`}
                >
                  {r.recommended_headway_min}m
                </span>
              </div>

              <div className="mt-2.5 h-1.5 overflow-hidden rounded-full bg-slate-800">
                <div
                  className="h-full rounded-full bg-gradient-to-r from-brand-500 to-emerald-400"
                  style={{ width: `${Math.min(100, r.capacity_utilization_pct || 0)}%` }}
                />
              </div>
              <p className="mt-1 text-[10px] font-mono text-slate-400">Utilization: {r.capacity_utilization_pct}%</p>

              {canEdit && (
                <button
                  onClick={() => applyHeadway(r.station_id)}
                  className="mt-3 w-full rounded-xl bg-brand-500/15 border border-brand-500/30 px-2 py-1.5 text-[10px] font-extrabold uppercase tracking-wider text-brand-300 transition hover:bg-brand-500/25"
                >
                  Apply Frequency
                </button>
              )}
            </div>
          ))}

          {recsState === "loading" && recs.length === 0 && (
            <p className="col-span-full py-6 text-center text-xs text-slate-500">Calculating headway recommendations...</p>
          )}
        </div>
      </div>

      {/* Schedules Data Table */}
      <div className="card mt-5 border-slate-800">
        <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-800 px-5 py-4">
          <h3 className="font-extrabold tracking-tight text-white">Train Timetables & Schedules</h3>

          <div className="flex flex-wrap items-center gap-2.5">
            <div className="relative">
              <Search className="absolute left-2.5 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-slate-500" />
              <input
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Search train, station or line..."
                className="input w-56 py-1.5 pl-8 text-xs"
              />
            </div>

            <select className="input w-auto py-1.5 text-xs" value={filter} onChange={(e) => setFilter(e.target.value)}>
              <option value="all">All Statuses</option>
              <option value="on_time">On time</option>
              <option value="delayed">Delayed</option>
              <option value="cancelled">Cancelled</option>
            </select>

            <button onClick={exportCsv} className="btn-ghost py-1.5 text-xs">
              <Download className="h-3.5 w-3.5 text-brand-400" /> CSV
            </button>

            {canEdit && (
              <button onClick={openCreate} className="btn-primary py-1.5 text-xs">
                <Plus className="h-4 w-4" /> New Schedule
              </button>
            )}
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="table-base">
            <thead>
              <tr>
                <th>Train</th>
                <th>Station</th>
                <th>Direction</th>
                <th>Arrival Time</th>
                <th>Headway</th>
                <th>Peak</th>
                <th>Status</th>
                <th>Delay</th>
                {canEdit && <th className="text-right">Actions</th>}
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/80">
              {pageRows.map((s) => (
                <tr key={s.id} className="hover:bg-slate-850/60 transition">
                  <td className="font-mono font-bold text-white">{s.train_id}</td>
                  <td>{stationName(s.station_id)}</td>
                  <td className="capitalize text-slate-300">{s.direction}</td>
                  <td className="font-mono text-xs">
                    {new Date(s.arrival).toLocaleString([], {
                      month: "short",
                      day: "numeric",
                      hour: "2-digit",
                      minute: "2-digit",
                    })}
                  </td>
                  <td className="font-mono">{s.headway_min}m</td>
                  <td>
                    <StatusBadge value={s.is_peak === "yes" ? "high" : "low"} />
                  </td>
                  <td>
                    <StatusBadge value={s.status} />
                  </td>
                  <td className={s.delay_min > 0 ? "font-mono font-bold text-amber-400" : "text-slate-500"}>
                    {s.delay_min > 0 ? `+${s.delay_min}m` : "—"}
                  </td>
                  {canEdit && (
                    <td className="text-right">
                      <button
                        onClick={() => openEdit(s)}
                        className="mr-1 rounded-lg p-1.5 text-slate-400 hover:bg-slate-800 hover:text-white"
                        title="Edit entry"
                      >
                        <Pencil className="h-4 w-4" />
                      </button>
                      <button
                        onClick={() => reportDelay(s)}
                        className="mr-1 rounded-lg px-2 py-1 text-xs font-bold text-amber-400 hover:bg-amber-500/15"
                      >
                        Delay
                      </button>
                      <button
                        onClick={() => removeSchedule(s.id)}
                        className="rounded-lg p-1.5 text-slate-400 hover:bg-rose-500/15 hover:text-rose-400"
                        title="Delete entry"
                      >
                        <Trash2 className="h-4 w-4" />
                      </button>
                    </td>
                  )}
                </tr>
              ))}
              {schedulesState === "loading" && filtered.length === 0 && (
                <tr>
                  <td colSpan={canEdit ? 9 : 8} className="py-12 text-center text-sm text-slate-500">
                    Loading schedules from database...
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination Footer */}
        <div className="flex items-center justify-between border-t border-slate-800 px-5 py-3 text-xs text-slate-400">
          <button
            disabled={page === 0}
            onClick={() => setPage((p) => Math.max(0, p - 1))}
            className="btn-ghost py-1 text-xs disabled:opacity-40"
          >
            ← Prev
          </button>
          <span>
            Page <span className="font-bold text-white">{page + 1}</span> of {pages} ({filtered.length} total entries)
          </span>
          <button
            disabled={page + 1 >= pages}
            onClick={() => setPage((p) => p + 1)}
            className="btn-ghost py-1 text-xs disabled:opacity-40"
          >
            Next →
          </button>
        </div>
      </div>

      {/* Modal Dialog Form */}
      {showForm && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/80 p-4 backdrop-blur-md"
          onClick={() => {
            setShowForm(false);
            setEditing(null);
          }}
        >
          <div
            className="card w-full max-w-lg border-slate-800 bg-slate-900 p-6 shadow-2xl"
            onClick={(e) => e.stopPropagation()}
          >
            <h3 className="text-lg font-extrabold tracking-tight text-white">
              {editing ? `Edit Schedule ${editing.id}` : "Create New Timetable Entry"}
            </h3>
            <p className="text-xs text-slate-400 mb-4">Specify train headway and arrival parameters</p>

            <form onSubmit={saveSchedule} className="grid grid-cols-2 gap-4">
              <div>
                <label className="label">Train ID</label>
                <select
                  className="input"
                  value={form.train_id}
                  onChange={(e) => setForm({ ...form, train_id: e.target.value })}
                >
                  {trains.map((t) => (
                    <option key={t} value={t}>{t}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="label">Station</label>
                <select
                  className="input"
                  value={form.station_id}
                  onChange={(e) => setForm({ ...form, station_id: e.target.value })}
                >
                  {stations.map((s) => (
                    <option key={s.id} value={s.id}>{s.name}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="label">Direction</label>
                <select
                  className="input"
                  value={form.direction}
                  onChange={(e) => setForm({ ...form, direction: e.target.value })}
                >
                  <option value="northbound">Northbound</option>
                  <option value="southbound">Southbound</option>
                </select>
              </div>

              <div>
                <label className="label">Arrival Date/Time</label>
                <input
                  type="datetime-local"
                  required
                  className="input"
                  value={form.arrival}
                  onChange={(e) => setForm({ ...form, arrival: e.target.value })}
                />
              </div>

              <div>
                <label className="label">Headway (min)</label>
                <input
                  type="number"
                  min="2"
                  max="30"
                  className="input"
                  value={form.headway_min}
                  onChange={(e) => setForm({ ...form, headway_min: e.target.value })}
                />
              </div>

              <div>
                <label className="label">Peak Period Flag</label>
                <select
                  className="input"
                  value={form.is_peak}
                  onChange={(e) => setForm({ ...form, is_peak: e.target.value })}
                >
                  <option value="no">No (Off-Peak)</option>
                  <option value="yes">Yes (Peak Hour)</option>
                </select>
              </div>

              <div className="col-span-2 mt-3 flex justify-end gap-2.5">
                <button
                  type="button"
                  className="btn-ghost"
                  onClick={() => {
                    setShowForm(false);
                    setEditing(null);
                  }}
                >
                  Cancel
                </button>
                <button type="submit" disabled={busy} className="btn-primary">
                  {busy && <Loader2 className="h-4 w-4 animate-spin" />}
                  {editing ? "Save Changes" : "Create Schedule"}
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
