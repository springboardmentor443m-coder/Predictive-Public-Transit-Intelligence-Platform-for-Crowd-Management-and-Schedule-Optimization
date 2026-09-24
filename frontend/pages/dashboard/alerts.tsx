import { useCallback, useEffect, useState, type FormEvent } from "react";
import { BellRing, Check, Download, Loader2, Megaphone, Radio, ShieldAlert } from "lucide-react";
import DashboardLayout from "../../components/DashboardLayout";
import StatusBadge from "../../components/StatusBadge";
import { useAuth, withAuth } from "../../lib/auth";
import { useToast } from "../../components/ToastContext";
import api from "../../lib/api";
import { getSocket } from "../../lib/socket";
import { downloadCsv } from "../../lib/csv";
import type { AlertItem, Station } from "../../lib/types";

type Filter = "open" | "ack" | "all";

function Alerts() {
  const { hasRole } = useAuth();
  const { showToast } = useToast();
  const canOperate = hasRole("admin", "operator");
  const isAdmin = hasRole("admin");

  const [alerts, setAlerts] = useState<AlertItem[]>([]);
  const [filter, setFilter] = useState<Filter>("open");
  const [typeF, setTypeF] = useState("");
  const [sevF, setSevF] = useState("");
  const [stationF, setStationF] = useState("");
  const [busyId, setBusyId] = useState<string | null>(null);
  const [bcForm, setBcForm] = useState({ title: "", message: "", station_id: "" });
  const [stations, setStations] = useState<Station[]>([]);
  const [sending, setSending] = useState(false);

  const load = useCallback(() => {
    const params = new URLSearchParams({ limit: "100" });
    if (filter === "open") params.set("acknowledged", "false");
    if (filter === "ack") params.set("acknowledged", "true");
    if (typeF) params.set("type", typeF);
    if (sevF) params.set("severity", sevF);
    if (stationF) params.set("station_id", stationF);

    api.get<AlertItem[]>(`/alerts?${params.toString()}`)
      .then((res) => setAlerts(res.data))
      .catch(() => {});
  }, [filter, typeF, sevF, stationF]);

  useEffect(() => {
    load();
    api.get<Station[]>("/stations").then((r) => setStations(r.data)).catch(() => {});
    const iv = setInterval(load, 20000);
    return () => clearInterval(iv);
  }, [load]);

  useEffect(() => {
    let s: ReturnType<typeof getSocket> | undefined;
    try {
      s = getSocket();
      s.on("alert", (newAlert: AlertItem) => {
        showToast(newAlert.title || "New emergency broadcast", "error", "ALERT RECEIVED");
        load();
      });
    } catch {}
    return () => {
      if (s) s.off("alert");
    };
  }, [load, showToast]);

  async function acknowledge(id: string) {
    setBusyId(id);
    try {
      await api.post(`/alerts/${id}/acknowledge`);
      showToast("Alert acknowledged & resolved", "success");
      load();
    } catch (err) {
      showToast((err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || "Failed to acknowledge alert", "error");
    } finally {
      setBusyId(null);
    }
  }

  async function broadcast(e: FormEvent<HTMLFormElement>) {
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
      showToast("Emergency broadcast dispatched to all active consoles", "warning");
      setBcForm({ title: "", message: "", station_id: "" });
      load();
    } catch (err) {
      showToast((err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || "Broadcast failed (admin privileges required)", "error");
    } finally {
      setSending(false);
    }
  }

  function exportCsv() {
    downloadCsv<AlertItem>(`metroflow-alerts-${Date.now()}.csv`, alerts, [
      { label: "id", key: "id" },
      { label: "type", key: "type" },
      { label: "severity", key: "severity" },
      { label: "station_id", key: "station_id" },
      { label: "title", key: "title" },
      { label: "message", key: "message" },
      { label: "is_acknowledged", key: "is_acknowledged" },
      { label: "created_at", key: "created_at" },
    ]);
    showToast("Exported alert log CSV", "success");
  }

  const counts = {
    open: alerts.filter((a) => !a.is_acknowledged).length,
    critical: alerts.filter((a) => a.severity === "critical" && !a.is_acknowledged).length,
  };

  return (
    <DashboardLayout title="Alerts & Broadcast Center" subtitle="Overcrowding notifications · delay logs · network emergency broadcasts">
      <div className="grid grid-cols-1 gap-5 xl:grid-cols-3">
        {/* Left Column: Alert Feed */}
        <div className="card xl:col-span-2 border-slate-800">
          <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-800 px-5 py-4">
            <div className="flex items-center gap-2">
              <h3 className="font-extrabold tracking-tight text-white">Live Alert Feed</h3>
              {counts.critical > 0 && (
                <span className="rounded-full bg-rose-500/20 px-2.5 py-0.5 text-[11px] font-extrabold text-rose-300 border border-rose-500/40 animate-pulse">
                  {counts.critical} Critical
                </span>
              )}
            </div>

            <div className="flex flex-wrap items-center gap-2.5">
              <div className="flex rounded-xl bg-slate-950 p-1 text-xs font-bold border border-slate-800">
                {([
                  ["open", "Open"],
                  ["ack", "Resolved"],
                  ["all", "All Logs"],
                ] as Array<[Filter, string]>).map(([v, l]) => (
                  <button
                    key={v}
                    onClick={() => setFilter(v)}
                    className={`rounded-lg px-3 py-1.5 transition ${
                      filter === v ? "bg-brand-600 text-white shadow" : "text-slate-400 hover:text-white"
                    }`}
                  >
                    {l}
                  </button>
                ))}
              </div>

              <button onClick={exportCsv} className="btn-ghost py-1.5 text-xs font-bold">
                <Download className="h-3.5 w-3.5 text-brand-400" /> CSV Log
              </button>
            </div>
          </div>

          {/* Filter Bar */}
          <div className="flex flex-wrap gap-2.5 border-b border-slate-800/80 bg-slate-950/60 px-5 py-3">
            <select value={typeF} onChange={(e) => setTypeF(e.target.value)} className="input w-auto py-1.5 text-xs">
              <option value="">All Alert Types</option>
              <option value="overcrowding">Overcrowding</option>
              <option value="delay">Delay Notice</option>
              <option value="emergency">Emergency</option>
              <option value="info">Information</option>
            </select>

            <select value={sevF} onChange={(e) => setSevF(e.target.value)} className="input w-auto py-1.5 text-xs">
              <option value="">All Severities</option>
              <option value="low">Low</option>
              <option value="medium">Medium</option>
              <option value="high">High</option>
              <option value="critical">Critical</option>
            </select>

            <select value={stationF} onChange={(e) => setStationF(e.target.value)} className="input w-auto max-w-[200px] py-1.5 text-xs">
              <option value="">All Stations</option>
              {stations.map((s) => (
                <option key={s.id} value={s.id}>{s.name}</option>
              ))}
            </select>

            {(typeF || sevF || stationF) && (
              <button
                onClick={() => {
                  setTypeF("");
                  setSevF("");
                  setStationF("");
                }}
                className="text-xs font-bold text-brand-400 hover:text-brand-300 self-center ml-1"
              >
                Clear Filters ×
              </button>
            )}
          </div>

          {/* Alert Stream List */}
          <div className="divide-y divide-slate-800/80 max-h-[600px] overflow-y-auto scroll-thin">
            {alerts.length === 0 && (
              <p className="px-5 py-16 text-center text-sm text-slate-500">No alerts match current filter criteria.</p>
            )}
            {alerts.map((a) => (
              <div
                key={a.id}
                className={`flex items-start gap-4 px-5 py-4 transition hover:bg-slate-850/60 ${
                  a.type === "emergency" ? "bg-rose-950/20" : ""
                }`}
              >
                <span
                  className={`mt-0.5 flex h-10 w-10 shrink-0 items-center justify-center rounded-2xl border ${
                    a.type === "emergency"
                      ? "bg-rose-500/20 text-rose-400 border-rose-500/40"
                      : a.type === "overcrowding"
                      ? "bg-orange-500/20 text-orange-400 border-orange-500/40"
                      : "bg-amber-500/20 text-amber-400 border-amber-500/40"
                  }`}
                >
                  {a.type === "emergency" ? <Megaphone className="h-5 w-5 animate-bounce" /> : <BellRing className="h-5 w-5" />}
                </span>

                <div className="min-w-0 flex-1">
                  <div className="flex flex-wrap items-center gap-2">
                    <p className="text-sm font-extrabold text-white">{a.title}</p>
                    <StatusBadge value={a.severity} />
                    <StatusBadge value={a.type} />
                    {a.station_id && (
                      <span className="rounded-md bg-slate-800 px-1.5 py-0.5 text-[10px] font-mono text-slate-300">
                        {a.station_id}
                      </span>
                    )}
                  </div>

                  <p className="mt-1 text-xs text-slate-300 leading-relaxed">{a.message}</p>
                  
                  <p className="mt-1.5 text-[10px] font-mono uppercase tracking-wide text-slate-500">
                    {new Date(a.created_at).toLocaleString([], { dateStyle: "short", timeStyle: "medium" })}
                    {a.is_acknowledged && a.resolved_at && ` · Resolved ${new Date(a.resolved_at).toLocaleTimeString()}`}
                  </p>
                </div>

                {canOperate && !a.is_acknowledged && (
                  <button
                    onClick={() => acknowledge(a.id)}
                    disabled={busyId === a.id}
                    className="btn-ghost shrink-0 py-1.5 px-3 text-xs font-bold"
                  >
                    {busyId === a.id ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Check className="h-3.5 w-3.5 text-emerald-400" />}
                    Ack
                  </button>
                )}

                {a.is_acknowledged && (
                  <span className="inline-flex shrink-0 items-center gap-1 rounded-full bg-emerald-500/10 px-2.5 py-1 text-xs font-bold text-emerald-400 border border-emerald-500/30">
                    <Check className="h-3 w-3" /> Resolved
                  </span>
                )}
              </div>
            ))}
          </div>
        </div>

        {/* Right Column: Emergency Broadcast Panel */}
        <div className="card card-pad border-slate-800 self-start space-y-4">
          <div className="flex items-center gap-3 border-b border-slate-800 pb-3">
            <span className="flex h-10 w-10 items-center justify-center rounded-2xl bg-rose-500/20 border border-rose-500/40 text-rose-400 shadow-lg shadow-rose-500/20">
              <Megaphone className="h-5 w-5" />
            </span>
            <div>
              <h3 className="font-extrabold tracking-tight text-white">Emergency Network Broadcast</h3>
              <p className="text-xs text-slate-400">Push high-priority announcements to all connected operator consoles</p>
            </div>
          </div>

          {!isAdmin ? (
            <div className="rounded-xl bg-slate-950/60 p-4 text-xs text-slate-400 border border-slate-800 space-y-2">
              <div className="flex items-center gap-2 font-bold text-amber-400">
                <ShieldAlert className="h-4 w-4" /> Admin Authorization Required
              </div>
              <p>Only administrators can trigger emergency announcements. Operators can acknowledge and resolve alerts.</p>
            </div>
          ) : (
            <form onSubmit={broadcast} className="space-y-3.5">
              <div>
                <label className="label">Target Station Scope</label>
                <select
                  className="input"
                  value={bcForm.station_id}
                  onChange={(e) => setBcForm({ ...bcForm, station_id: e.target.value })}
                >
                  <option value="">Entire Metro Network (All Lines)</option>
                  {stations.map((s) => (
                    <option key={s.id} value={s.id}>{s.name} ({s.id})</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="label">Broadcast Title</label>
                <input
                  required
                  className="input"
                  placeholder="e.g. Platform Evacuation Drill - Red Line"
                  value={bcForm.title}
                  onChange={(e) => setBcForm({ ...bcForm, title: e.target.value })}
                />
              </div>

              <div>
                <label className="label">Announcement Content</label>
                <textarea
                  required
                  rows={3}
                  className="input resize-none"
                  placeholder="Details and operational instructions for station masters..."
                  value={bcForm.message}
                  onChange={(e) => setBcForm({ ...bcForm, message: e.target.value })}
                />
              </div>

              <button type="submit" disabled={sending} className="btn-danger w-full py-3 text-xs font-extrabold shadow-lg">
                {sending ? <Loader2 className="h-4 w-4 animate-spin" /> : <Megaphone className="h-4 w-4" />}
                Dispatch Emergency Announcement
              </button>
            </form>
          )}

          <div className="rounded-xl bg-slate-950 p-4 text-[11px] text-slate-400 border border-slate-800 space-y-1.5">
            <p className="font-extrabold text-white uppercase tracking-wider">Alert Engine Rules</p>
            <p>· Station occupancy ≥90% → High overcrowding alert</p>
            <p>· Station occupancy ≥100% → Critical emergency alert</p>
            <p>· Train delay ≥3 min → Automatic dispatch notification</p>
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
}

export default withAuth(Alerts);