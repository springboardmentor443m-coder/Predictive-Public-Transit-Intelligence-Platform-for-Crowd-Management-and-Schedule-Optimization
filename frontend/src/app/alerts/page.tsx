"use client";

import { useEffect, useState } from "react";
import { Bell, Megaphone, CheckCircle, ShieldAlert, Radio, Send } from "lucide-react";
import { api } from "@/lib/api";
import { AlertItem } from "@/types";

export default function AlertsPage() {
  const [alerts, setAlerts] = useState<AlertItem[]>([]);
  const [paModalOpen, setPaModalOpen] = useState(false);
  const [paMessage, setPaMessage] = useState("Attention passengers: Platform 2 crowd management protocols are active. Please allow outgoing passengers to exit first.");
  const [paTargetStation, setPaTargetStation] = useState<number>(1);
  const [paStatus, setPaStatus] = useState<string>("");
  const [loading, setLoading] = useState(true);

  const loadAlerts = async () => {
    try {
      const data = await api.getAlerts();
      setAlerts(data);
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
            Alerts & Emergency Operations Center
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Real-time threshold alert feed, incident resolution logging, and multi-channel Public Address (PA) broadcast triggers
          </p>
        </div>

        <button
          onClick={() => setPaModalOpen(true)}
          className="flex items-center gap-2 px-4 py-2.5 rounded-lg bg-rose-600 hover:bg-rose-500 text-white font-bold text-xs transition shadow-lg shadow-rose-600/25"
        >
          <Megaphone className="w-4 h-4" />
          Trigger Public Address (PA) Broadcast
        </button>
      </div>

      {/* Active Alerts List */}
      <div className="bg-[#0d1424] border border-slate-800 rounded-xl p-5 space-y-4">
        <div className="flex items-center justify-between border-b border-slate-800 pb-3">
          <h3 className="text-sm font-bold text-white flex items-center gap-2">
            <ShieldAlert className="w-4 h-4 text-rose-400" />
            Operational Incident Feed ({alerts.filter((a) => !a.is_resolved).length} Active)
          </h3>
        </div>

        <div className="space-y-3">
          {alerts.map((a) => {
            const isCritical = a.priority === "CRITICAL";
            const isWarning = a.priority === "WARNING";

            return (
              <div
                key={a.id}
                className={`p-4 bg-slate-900/90 border rounded-xl flex flex-col md:flex-row md:items-center justify-between gap-4 text-xs transition ${
                  a.is_resolved
                    ? "border-slate-800 opacity-60"
                    : isCritical
                    ? "border-rose-500/50 bg-rose-950/10"
                    : isWarning
                    ? "border-amber-500/40"
                    : "border-slate-800"
                }`}
              >
                <div className="space-y-1">
                  <div className="flex items-center gap-2 font-bold text-white text-sm">
                    <span
                      className={`text-[10px] px-2 py-0.5 rounded font-bold uppercase ${
                        isCritical
                          ? "bg-rose-500/20 text-rose-400 border border-rose-500/30"
                          : isWarning
                          ? "bg-amber-500/20 text-amber-400 border border-amber-500/30"
                          : "bg-blue-500/20 text-blue-400 border border-blue-500/30"
                      }`}
                    >
                      {a.priority}
                    </span>
                    <span className="text-slate-300 font-mono">[{a.category}]</span>
                    {a.station_name && (
                      <span className="text-slate-400 text-xs">@ {a.station_name}</span>
                    )}
                  </div>
                  <p className="text-slate-300 font-medium leading-relaxed">{a.message}</p>
                </div>

                <div className="flex items-center gap-4">
                  {!a.is_resolved ? (
                    <button
                      onClick={() => handleResolve(a.id)}
                      className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-emerald-400 font-semibold transition flex items-center gap-1.5 text-xs border border-slate-700"
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

      {/* PA Broadcast Modal */}
      {paModalOpen && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="w-full max-w-md bg-[#0d1424] border border-slate-700 rounded-2xl p-6 shadow-2xl space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <h3 className="text-base font-bold text-white flex items-center gap-2">
                <Megaphone className="w-5 h-5 text-rose-400" />
                Multi-Channel PA & SMS Broadcast
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
                  Target Station
                </label>
                <select
                  value={paTargetStation}
                  onChange={(e) => setPaTargetStation(Number(e.target.value))}
                  className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-white font-semibold focus:outline-none focus:border-rose-500"
                >
                  <option value={1}>Central Terminal (Red Line)</option>
                  <option value={4}>University Square</option>
                  <option value={15}>Stadium Arena (Blue Line)</option>
                  <option value={999}>ALL STATIONS (SYSTEM-WIDE)</option>
                </select>
              </div>

              <div>
                <label className="block font-semibold text-slate-300 uppercase mb-1">
                  PA Message Text / Voice Announcement
                </label>
                <textarea
                  rows={4}
                  value={paMessage}
                  onChange={(e) => setPaMessage(e.target.value)}
                  className="w-full bg-slate-900 border border-slate-700 rounded-lg p-3 text-white text-xs focus:outline-none focus:border-rose-500"
                />
              </div>

              <div className="p-3 bg-slate-900/80 border border-slate-800 rounded-lg space-y-1 text-[11px] text-slate-400">
                <div className="font-semibold text-slate-300">Channels Triggered:</div>
                <div>• Station Public Address (PA) Audio Speakers</div>
                <div>• Twilio SMS Gateway for Station Supervisors</div>
                <div>• Control Room Audit Log</div>
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
                  Dispatch Broadcast
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
