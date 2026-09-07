"use client";

import { useEffect, useState } from "react";
import { CalendarClock, Sliders, AlertOctagon, CheckCircle2, Clock, Train } from "lucide-react";
import { api } from "@/lib/api";
import { TrainSchedule } from "@/types";

export default function SchedulesPage() {
  const [schedules, setSchedules] = useState<TrainSchedule[]>([]);
  const [selectedSchedule, setSelectedSchedule] = useState<TrainSchedule | null>(null);
  const [newHeadway, setNewHeadway] = useState<number>(5);
  const [overrideReason, setOverrideReason] = useState<string>("Crowd surge mitigation");
  const [modalOpen, setModalOpen] = useState<boolean>(false);
  const [feedbackMsg, setFeedbackMsg] = useState<{ applied: boolean; text: string } | null>(null);
  const [loading, setLoading] = useState<boolean>(true);

  const loadSchedules = async () => {
    try {
      const data = await api.getSchedules();
      setSchedules(data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadSchedules();
  }, []);

  const handleOpenOverride = (sch: TrainSchedule) => {
    setSelectedSchedule(sch);
    setNewHeadway(sch.headway_minutes);
    setFeedbackMsg(null);
    setModalOpen(true);
  };

  const handleApplyOverride = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedSchedule) return;

    try {
      const res = await api.overrideSchedule(selectedSchedule.id, newHeadway, overrideReason);
      setFeedbackMsg({ applied: res.applied, text: res.message });
      if (res.applied) {
        setTimeout(() => setModalOpen(false), 1500);
        loadSchedules();
      }
    } catch (err: any) {
      setFeedbackMsg({ applied: false, text: err.message || "Failed to override schedule" });
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800 pb-4">
        <div>
          <h1 className="text-2xl font-black text-white flex items-center gap-2">
            <CalendarClock className="w-6 h-6 text-blue-400" />
            Train Schedule & Dispatch Control Center
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Visual timetable runs, delay tracking, conflict detection, and manual headway override controls
          </p>
        </div>
      </div>

      {/* Timetable Schedule Cards / List */}
      <div className="bg-[#0d1424] border border-slate-800 rounded-xl p-5 space-y-4">
        <div className="flex items-center justify-between border-b border-slate-800 pb-3">
          <h3 className="text-sm font-bold text-white flex items-center gap-2">
            <Train className="w-4 h-4 text-blue-400" />
            Active Train Runs & Operational Timetables
          </h3>
          <span className="text-xs text-slate-400">4 Active Corridors</span>
        </div>

        <div className="space-y-3">
          {schedules.map((sch) => (
            <div
              key={sch.id}
              className="p-4 bg-slate-900/90 border border-slate-800 rounded-xl flex flex-col md:flex-row md:items-center justify-between gap-4 text-xs hover:border-slate-700 transition"
            >
              <div className="space-y-1">
                <div className="flex items-center gap-2 font-bold text-white text-sm">
                  <span>{sch.train_code}</span>
                  <span className="text-[10px] px-2 py-0.5 rounded bg-blue-500/20 text-blue-400 border border-blue-500/30">
                    {sch.line_name}
                  </span>
                  {sch.conflict_detected && (
                    <span className="text-[10px] px-2 py-0.5 rounded bg-rose-500/20 text-rose-400 border border-rose-500/30 font-semibold flex items-center gap-1">
                      <AlertOctagon className="w-3 h-3" />
                      Conflict Flag
                    </span>
                  )}
                </div>
                <div className="text-slate-400">
                  {sch.origin_station_name} → {sch.destination_station_name}
                </div>
                {sch.conflict_reason && (
                  <div className="text-[11px] text-rose-400 font-medium pt-0.5">
                    ⚠️ {sch.conflict_reason}
                  </div>
                )}
              </div>

              <div className="flex items-center gap-6">
                <div className="text-right space-y-0.5">
                  <div className="text-slate-400">Headway Interval</div>
                  <div className="font-bold text-white font-mono text-sm">
                    {sch.headway_minutes} mins
                    {sch.recommended_headway !== sch.headway_minutes && (
                      <span className="text-amber-400 text-xs font-normal ml-1">
                        (Rec: {sch.recommended_headway}m)
                      </span>
                    )}
                  </div>
                </div>

                <div className="text-right space-y-0.5">
                  <div className="text-slate-400">Run Status</div>
                  <div className={`font-bold font-mono ${
                    sch.status === "DELAYED" ? "text-rose-400" : "text-emerald-400"
                  }`}>
                    {sch.status} {sch.delay_minutes > 0 ? `(+${sch.delay_minutes}m)` : ""}
                  </div>
                </div>

                <button
                  onClick={() => handleOpenOverride(sch)}
                  className="px-3 py-2 rounded-lg bg-blue-600 hover:bg-blue-500 text-white font-bold transition flex items-center gap-1.5 shadow-md shadow-blue-600/20"
                >
                  <Sliders className="w-3.5 h-3.5" />
                  Override Headway
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Override Modal */}
      {modalOpen && selectedSchedule && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="w-full max-w-md bg-[#0d1424] border border-slate-700 rounded-2xl p-6 shadow-2xl space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <h3 className="text-base font-bold text-white flex items-center gap-2">
                <Sliders className="w-5 h-5 text-blue-400" />
                Dispatch Headway Override
              </h3>
              <button onClick={() => setModalOpen(false)} className="text-slate-400 hover:text-white">✕</button>
            </div>

            {feedbackMsg && (
              <div className={`p-3 rounded-lg text-xs font-semibold ${
                feedbackMsg.applied
                  ? "bg-emerald-500/20 text-emerald-400 border border-emerald-500/30"
                  : "bg-rose-500/20 text-rose-400 border border-rose-500/30"
              }`}>
                {feedbackMsg.text}
              </div>
            )}

            <form onSubmit={handleApplyOverride} className="space-y-4 text-xs">
              <div>
                <label className="block font-semibold text-slate-300 uppercase mb-1">
                  Target Train Run
                </label>
                <div className="p-2.5 bg-slate-900 border border-slate-800 rounded-lg text-white font-mono">
                  {selectedSchedule.train_code} ({selectedSchedule.line_name})
                </div>
              </div>

              <div>
                <label className="block font-semibold text-slate-300 uppercase mb-1">
                  New Headway Interval (Minutes)
                </label>
                <input
                  type="number"
                  min="1"
                  max="30"
                  value={newHeadway}
                  onChange={(e) => setNewHeadway(Number(e.target.value))}
                  className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-white font-mono text-sm focus:outline-none focus:border-blue-500"
                />
                <p className="text-[11px] text-slate-400 mt-1">
                  Note: Safety minimum headway requirement is 3 minutes.
                </p>
              </div>

              <div>
                <label className="block font-semibold text-slate-300 uppercase mb-1">
                  Override Rationale / Log Reason
                </label>
                <input
                  type="text"
                  value={overrideReason}
                  onChange={(e) => setOverrideReason(e.target.value)}
                  className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-white text-xs focus:outline-none focus:border-blue-500"
                />
              </div>

              <div className="flex gap-3 pt-2">
                <button
                  type="button"
                  onClick={() => setModalOpen(false)}
                  className="w-1/2 py-2.5 bg-slate-800 hover:bg-slate-700 text-slate-300 font-bold rounded-lg transition"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="w-1/2 py-2.5 bg-blue-600 hover:bg-blue-500 text-white font-bold rounded-lg transition shadow-lg shadow-blue-600/25"
                >
                  Confirm Override
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
