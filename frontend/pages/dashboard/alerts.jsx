import { useCallback, useEffect, useState } from "react";
import { BellRing, Check, Loader2, Megaphone } from "lucide-react";
import DashboardLayout from "../../components/DashboardLayout";
import StatusBadge from "../../components/StatusBadge";
import { useAuth, withAuth } from "../../lib/auth";
import api from "../../lib/api";
import { getSocket } from "../../lib/socket";

function Alerts() {
  const { hasRole } = useAuth();
  const canOperate = hasRole("admin", "operator");
  const isAdmin = hasRole("admin");

  const [alerts, setAlerts] = useState([]);
  const [filter, setFilter] = useState("open");
  const [busyId, setBusyId] = useState(null);
  const [bcForm, setBcForm] = useState({ title: "", message: "", station_id: "" });
  const [stations, setStations] = useState([]);
  const [sending, setSending] = useState(false);

  const load = useCallback(() => {
    api
      .get(`/alerts?limit=100${filter === "open" ? "&acknowledged=false" : filter === "ack" ? "&acknowledged=true" : ""}`)
      .then((res) => setAlerts(res.data))
      .catch(() => {});
  }, [filter]);

  useEffect(() => {
    load();
    api.get("/stations").then((r) => setStations(r.data)).catch(() => {});
    const iv = setInterval(load, 20000);
    return () => clearInterval(iv);
  }, [load]);

  useEffect(() => {
    let s;
    try {
      s = getSocket();
      s.on("alert", () => load());
    } catch {}
    return () => {
      if (s) s.off("alert");
    };
  }, [load]);

  async function acknowledge(id) {
    setBusyId(id);
    try {
      await api.post(`/alerts/${id}/acknowledge`);
      load();
    } catch (err) {
      alert(err?.response?.data?.detail || "Failed to acknowledge");
    } finally {
      setBusyId(null);
    }
  }

  async function broadcast(e) {
    e.preventDefault();
    setSending(true);
    try {
      await api.post("/alerts/broadcast", {
        type: "emergency",
        severity: "high",
        station_id: bcForm.station_id || null,
        title: bcForm.title,
        message: bcForm.message,
      });
      setBcForm({ title: "", message: "", station_id: "" });
      load();
    } catch (err) {
      alert(err?.response?.data?.detail || "Broadcast failed (admin only)");
    } finally {
      setSending(false);
    }
  }

  return (
    <DashboardLayout title="Alerts & Notifications" subtitle="Overcrowding alerts · delay notices · emergency broadcasts">
      <div className="grid grid-cols-1 gap-4 xl:grid-cols-3">
        {/* Feed */}
        <div className="card xl:col-span-2">
          <div className="flex flex-wrap items-center gap-3 border-b border-slate-200 px-5 py-4">
            <h3 className="font-semibold text-slate-900">Alert Feed</h3>
            <div className="ml-auto flex rounded-lg bg-slate-100 p-0.5 text-xs font-semibold">
              {[
                ["open", "Open"],
                ["ack", "Acknowledged"],
                ["all", "All"],
              ].map(([v, l]) => (
                <button
                  key={v}
                  onClick={() => setFilter(v)}
                  className={`rounded-md px-3 py-1.5 transition ${
                    filter === v ? "bg-white text-slate-800 shadow-sm" : "text-slate-500 hover:text-slate-700"
                  }`}
                >
                  {l}
                </button>
              ))}
            </div>
          </div>
          <div className="divide-y divide-slate-100">
            {alerts.length === 0 && (
              <p className="px-5 py-14 text-center text-sm text-slate-400">No alerts in this view.</p>
            )}
            {alerts.map((a) => (
              <div key={a.id} className={`flex items-start gap-4 px-5 py-4 ${a.type === "emergency" ? "bg-rose-50/50" : ""}`}>
                <span
                  className={`mt-0.5 flex h-10 w-10 shrink-0 items-center justify-center rounded-xl ${
                    a.type === "emergency"
                      ? "bg-rose-100 text-rose-600"
                      : a.type === "overcrowding"
                      ? "bg-orange-50 text-orange-600"
                      : "bg-amber-50 text-amber-600"
                  }`}
                >
                  {a.type === "emergency" ? <Megaphone className="h-5 w-5" /> : <BellRing className="h-5 w-5" />}
                </span>
                <div className="min-w-0 flex-1">
                  <div className="flex flex-wrap items-center gap-2">
                    <p className="text-sm font-semibold text-slate-900">{a.title}</p>
                    <StatusBadge value={a.severity} />
                    <StatusBadge value={a.type} />
                    {a.station_id && <span className="text-xs text-slate-400">· {a.station_id}</span>}
                  </div>
                  <p className="mt-1 text-sm text-slate-600">{a.message}</p>
                  <p className="mt-1 text-[11px] uppercase tracking-wide text-slate-400">
                    {new Date(a.created_at).toLocaleString()}
                    {a.is_acknowledged && a.resolved_at && ` · resolved ${new Date(a.resolved_at).toLocaleTimeString()}`}
                  </p>
                </div>
                {canOperate && !a.is_acknowledged && (
                  <button
                    onClick={() => acknowledge(a.id)}
                    disabled={busyId === a.id}
                    className="btn-ghost shrink-0 py-1.5 text-xs"
                  >
                    {busyId === a.id ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Check className="h-3.5 w-3.5" />}
                    Acknowledge
                  </button>
                )}
                {a.is_acknowledged && (
                  <span className="inline-flex shrink-0 items-center gap-1 rounded-full bg-emerald-50 px-2.5 py-1 text-xs font-semibold text-emerald-700 ring-1 ring-emerald-200">
                    <Check className="h-3 w-3" /> Resolved
                  </span>
                )}
              </div>
            ))}
          </div>
        </div>

        {/* Broadcast panel */}
        <div className="card card-pad self-start">
          <div className="flex items-center gap-2">
            <span className="flex h-9 w-9 items-center justify-center rounded-lg bg-rose-50 text-rose-600">
              <Megaphone className="h-4.5 w-4.5 h-[18px] w-[18px]" />
            </span>
            <div>
              <h3 className="font-semibold text-slate-900">Emergency Broadcast</h3>
              <p className="text-xs text-slate-500">Push announcement to all connected consoles</p>
            </div>
          </div>

          {!isAdmin ? (
            <p className="mt-4 rounded-lg bg-slate-50 p-3 text-xs text-slate-500 ring-1 ring-slate-200">
              Only administrators can issue emergency broadcasts.
            </p>
          ) : (
            <form onSubmit={broadcast} className="mt-4 space-y-3">
              <div>
                <label className="label">Station (optional)</label>
                <select
                  className="input"
                  value={bcForm.station_id}
                  onChange={(e) => setBcForm({ ...bcForm, station_id: e.target.value })}
                >
                  <option value="">Entire network</option>
                  {stations.map((s) => (
                    <option key={s.id} value={s.id}>
                      {s.name}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className="label">Title</label>
                <input
                  required
                  className="input"
                  placeholder="e.g., Platform evacuation drill"
                  value={bcForm.title}
                  onChange={(e) => setBcForm({ ...bcForm, title: e.target.value })}
                />
              </div>
              <div>
                <label className="label">Message</label>
                <textarea
                  required
                  rows={3}
                  className="input resize-none"
                  placeholder="Announcement details…"
                  value={bcForm.message}
                  onChange={(e) => setBcForm({ ...bcForm, message: e.target.value })}
                />
              </div>
              <button type="submit" disabled={sending} className="btn-danger w-full">
                {sending ? <Loader2 className="h-4 w-4 animate-spin" /> : <Megaphone className="h-4 w-4" />}
                Broadcast now
              </button>
            </form>
          )}
        </div>
      </div>
    </DashboardLayout>
  );
}

export default withAuth(Alerts);
