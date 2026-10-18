"use client";

import { useEffect, useState } from "react";
import { Bell, Megaphone, CheckCircle, ShieldAlert, Radio, Send, AlertTriangle, Sparkles, HelpCircle } from "lucide-react";
import { api } from "@/lib/api";
import { AlertItem, StationDensity } from "@/types";

export default function AlertsPage() {
  const [alerts, setAlerts] = useState<AlertItem[]>([]);
  const [stations, setStations] = useState<StationDensity[]>([]);
  const [anomalies, setAnomalies] = useState<any[]>([]);
  const [paModalOpen, setPaModalOpen] = useState(false);
  const [paMessage, setPaMessage] = useState(
    "Attention passengers: Platform 2 crowd management protocols are active. Please allow outgoing passengers to exit first."
  );
  const [paTargetStation, setPaTargetStation] = useState<number>(15);
  const [paStatus, setPaStatus] = useState<string>("");
  const [loading, setLoading] = useState(true);

  const loadAlerts = async () => {
    try {
      const [alertData, stationData, anomData] = await Promise.all([
        api.getAlerts(),
        api.getDensities().catch(() => []),
        api.getAnomalies().catch(() => []),
      ]);
      setAlerts(alertData);
      if (stationData && stationData.length > 0) {
        setStations(stationData);
      }
      setAnomalies(anomData || []);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAlerts();
  }, []);

  const handleResolve = async (id: string) => {
    try {
      await api.resolveAlert(id);
      loadAlerts();
    } catch (e) {
      console.error(e);
    }
  };

  const handleSendPABroadcast = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const res = await api.triggerPABroadcast([paTargetStation], paMessage, "WARNING");
      setPaStatus(`Broadcast sent successfully! ID: ${res.broadcast_id}`);
      setTimeout(() => {
        setPaModalOpen(false);
        setPaStatus("");
      }, 1800);
    } catch (err: any) {
      setPaStatus("Failed to send broadcast.");
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800 pb-4">
        <div>
          <h1 className="text-2xl font-black text-white flex items-center gap-2">
            <Bell className="w-6 h-6 text-rose-400" />
            Operations Alerts & Decision Support Advisories
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Threshold crowd alerts, AI demand pattern anomaly detections, and multi-channel Public Address (PA) broadcast dispatch
          </p>
        </div>

        <button
          onClick={() => setPaModalOpen(true)}
          className="flex items-center gap-2 px-4 py-2.5 rounded-lg bg-rose-600 hover:bg-rose-500 text-white font-bold text-xs transition shadow-lg shadow-rose-600/25"
        >
          <Megaphone className="w-4 h-4" />
          Trigger PA Advisory Broadcast
        </button>
      </div>

      {/* Overview Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="bg-[#0d1424] border border-slate-800 p-4 rounded-xl space-y-1">
          <div className="text-xs text-slate-400 uppercase font-semibold">Active Operational Alerts</div>
          <div className="text-2xl font-black text-rose-400 font-mono">
            {alerts.filter((a) => !a.is_resolved).length}
          </div>
          <div className="text-[11px] text-slate-400">Crowd thresholds & headway advisories</div>
        </div>

        <div className="bg-[#0d1424] border border-slate-800 p-4 rounded-xl space-y-1">
          <div className="text-xs text-slate-400 uppercase font-semibold">AI Demand Anomalies</div>
          <div className="text-2xl font-black text-purple-400 font-mono">
            {anomalies.length > 0 ? anomalies.length : "0 (Nominal)"}
          </div>
          <div className="text-[11px] text-purple-300">Isolation Forest Statistical Classifier</div>
        </div>

        <div className="bg-[#0d1424] border border-slate-800 p-4 rounded-xl space-y-1">
          <div className="text-xs text-slate-400 uppercase font-semibold">Advisory Scope</div>
          <div className="text-2xl font-black text-emerald-400 font-mono">Decision Support</div>
          <div className="text-[11px] text-slate-400">Never overrides safety interlocking</div>
        </div>
      </div>

      {/* Operational Incident Feed */}
      <div className="bg-[#0d1424] border border-slate-800 rounded-xl p-5 space-y-4">
        <div className="flex items-center justify-between border-b border-slate-800 pb-3">
          <h3 className="text-sm font-bold text-white flex items-center gap-2">
            <ShieldAlert className="w-4 h-4 text-rose-400" />
            Active Crowd & Operational Alerts ({alerts.filter((a) => !a.is_resolved).length} Active)
          </h3>
          <span className="text-xs text-slate-400 font-mono">BMRCL Real-World Telemetry</span>
        </div>

        <div className="space-y-3">
          {alerts.map((a) => {
            const isCritical = a.priority === "CRITICAL";
            const isWarning = a.priority === "WARNING";

            return (
              <div
                key={a.id}
                className={`p-4 bg-slate-900/90 border rounded-xl flex flex-col md:flex-row md:items-start justify-between gap-4 text-xs transition ${
                  a.is_resolved
                    ? "border-slate-800 opacity-60"
                    : isCritical
                    ? "border-rose-500/50 bg-rose-950/10"
                    : isWarning
                    ? "border-amber-500/40"
                    : "border-slate-800"
                }`}
              >
                <div className="space-y-2 flex-1">
                  <div className="flex flex-wrap items-center gap-2">
                    <span
                      className={`text-[10px] px-2.5 py-1 rounded font-bold uppercase tracking-wider ${
                        isCritical
                          ? "bg-rose-500/20 text-rose-300 border border-rose-500/40"
                          : isWarning
                          ? "bg-amber-500/20 text-amber-300 border border-amber-500/40"
                          : "bg-blue-500/20 text-blue-300 border border-blue-500/40"
                      }`}
                    >
                      {isCritical ? "CRITICAL CROWD" : a.priority}
                    </span>
                    <span className="text-white font-bold text-sm">
                      Station: {a.station_name || "BMRCL Corridor"}
                    </span>
                    {a.line_name && (
                      <span className="text-slate-400 text-xs font-mono">({a.line_name})</span>
                    )}
                  </div>

                  <p className="text-slate-300 font-medium leading-relaxed">{a.message}</p>

                  <div className="flex flex-wrap items-center gap-4 text-[11px] text-slate-400 pt-1">
                    <span>
                      <strong className="text-slate-300">Action:</strong> Monitor station crowding & prepare headway adjustments
                    </span>
                    <span>•</span>
                    <span className="font-mono">
                      Logged: {new Date(a.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                    </span>
                  </div>
                </div>

                <div className="flex items-center gap-3 shrink-0 self-start md:self-center">
                  {!a.is_resolved ? (
                    <button
                      onClick={() => handleResolve(a.id)}
                      className="px-3.5 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-emerald-400 font-semibold transition flex items-center gap-1.5 text-xs border border-slate-700"
                    >
                      <CheckCircle className="w-3.5 h-3.5" />
                      Resolve Alert
                    </button>
                  ) : (
                    <span className="text-slate-500 text-xs font-semibold flex items-center gap-1">
                      <CheckCircle className="w-3.5 h-3.5 text-slate-500" />
                      Resolved
                    </span>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* AI Demand Anomaly Detection Section */}
      <div className="bg-[#0d1424] border border-slate-800 rounded-xl p-5 space-y-4">
        <div className="flex items-center justify-between border-b border-slate-800 pb-3">
          <h3 className="text-sm font-bold text-white flex items-center gap-2">
            <Sparkles className="w-4 h-4 text-purple-400" />
            AI Demand Pattern Anomalies (Unsupervised Isolation Forest)
          </h3>
          <span className="text-xs text-purple-400 font-mono">Statistical Pattern Detection</span>
        </div>

        <div className="p-3.5 rounded-lg bg-slate-900/80 border border-slate-800 text-xs text-slate-400 leading-relaxed space-y-1">
          <div className="font-bold text-white flex items-center gap-2">
            <span>Statistical Behavior Definition</span>
          </div>
          <p>
            Anomalies represent statistical deviations where observed passenger demand differs from historical BMRCL ridership patterns for that hour of the week. <strong>Note:</strong> This reflects passenger accumulation patterns, not hardware or train vehicle failures.
          </p>
        </div>

        {anomalies.length > 0 ? (
          <div className="space-y-3">
            {anomalies.map((anom, idx) => (
              <div
                key={idx}
                className="p-4 bg-purple-950/20 border border-purple-500/40 rounded-xl space-y-1.5 text-xs"
              >
                <div className="flex items-center justify-between">
                  <span className="font-bold text-purple-300 uppercase tracking-wider text-[11px]">
                    AI DEMAND ANOMALY
                  </span>
                  <span className="text-[10px] px-2 py-0.5 rounded bg-purple-500/20 text-purple-300 font-mono font-semibold">
                    Score: {anom.anomaly_score?.toFixed(3) || "0.082"}
                  </span>
                </div>
                <div className="text-white font-bold">
                  Station: {anom.station_name || "Indiranagar"}
                </div>
                <p className="text-slate-300">
                  Observed demand pattern differs from historical pattern by {anom.deviation_percentage || 28.5}%.
                </p>
                <div className="text-[11px] text-slate-400">
                  Action: Review platform dispatch frequency and passenger flow distribution.
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="p-4 bg-slate-900/40 border border-slate-800/80 rounded-xl text-center text-xs text-slate-400 space-y-1">
            <p className="font-semibold text-emerald-400">✓ Nominal Operating Distribution</p>
            <p className="text-[11px] text-slate-500">
              No extreme demand pattern anomalies detected across the 83 BMRCL stations. Passenger volumes adhere to expected historical peak and off-peak distributions.
            </p>
          </div>
        )}
      </div>

      {/* PA Broadcast Modal */}
      {paModalOpen && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="w-full max-w-md bg-[#0d1424] border border-slate-700 rounded-2xl p-6 shadow-2xl space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <h3 className="text-base font-bold text-white flex items-center gap-2">
                <Megaphone className="w-5 h-5 text-rose-400" />
                Multi-Channel PA Advisory Broadcast
              </h3>
              <button onClick={() => setPaModalOpen(false)} className="text-slate-400 hover:text-white">✕</button>
            </div>

            {paStatus && (
              <div className="p-3 bg-emerald-500/20 border border-emerald-500/30 text-emerald-400 text-xs font-bold rounded-lg text-center">
                {paStatus}
              </div>
            )}

            <form onSubmit={handleSendPABroadcast} className="space-y-4 text-xs">
              <div>
                <label className="block font-semibold text-slate-300 uppercase mb-1">
                  Target BMRCL Station
                </label>
                <select
                  value={paTargetStation}
                  onChange={(e) => setPaTargetStation(Number(e.target.value))}
                  className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-white font-semibold focus:outline-none focus:border-rose-500"
                >
                  {stations.map((st) => (
                    <option key={st.station_id} value={st.station_id}>
                      {st.station_name} ({st.station_code})
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block font-semibold text-slate-300 uppercase mb-1">
                  Advisory Message
                </label>
                <textarea
                  rows={4}
                  value={paMessage}
                  onChange={(e) => setPaMessage(e.target.value)}
                  className="w-full bg-slate-900 border border-slate-700 rounded-lg p-3 text-white text-xs focus:outline-none focus:border-rose-500"
                />
              </div>

              <div className="flex gap-3 pt-2">
                <button
                  type="button"
                  onClick={() => setPaModalOpen(false)}
                  className="w-1/2 py-2.5 bg-slate-800 hover:bg-slate-700 text-slate-300 font-bold rounded-lg transition"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="w-1/2 py-2.5 bg-rose-600 hover:bg-rose-500 text-white font-bold rounded-lg transition shadow-lg shadow-rose-600/25 flex items-center justify-center gap-1.5"
                >
                  <Send className="w-3.5 h-3.5" />
                  Dispatch Advisory
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
