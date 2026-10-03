"use client";

import { useEffect, useState } from "react";
import { CalendarClock, Sliders, AlertOctagon, CheckCircle2, Clock, Train, ShieldCheck, Info } from "lucide-react";
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
    setNewHeadway(Math.max(3, sch.headway_minutes));
    setFeedbackMsg(null);
    setModalOpen(true);
  };

  const handleApplyOverride = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedSchedule) return;

    if (newHeadway < 3) {
      setFeedbackMsg({
        applied: false,
        text: "Safety Violation: Minimum headway cannot be lower than 3 minutes.",
      });
      return;
    }

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
            <CalendarClock className="w-6 h-6 text-purple-400" />
            BMRCL Train Schedules & Frequency Decision Support
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Timetable-based train schedules, corridor headways, and dispatcher decision support.
          </p>
        </div>

        {/* Operational Status Badges */}
        <div className="flex flex-wrap items-center gap-2">
          <span className="px-2.5 py-1 rounded-lg bg-slate-900 border border-slate-800 text-[11px] font-mono text-purple-300 font-bold">
            SCHEDULED / HISTORICAL REPLAY
          </span>
          <span className="px-2.5 py-1 rounded-lg bg-slate-900 border border-slate-800 text-[11px] font-mono text-amber-300 font-bold">
            LIVE DELAY FEED: NOT CONNECTED
          </span>
          <span className="px-2.5 py-1 rounded-lg bg-slate-900 border border-slate-800 text-[11px] font-mono text-blue-300 font-bold">
            DECISION SUPPORT ONLY
          </span>
        </div>
      </div>

      {/* Safety Notice Banner */}
      <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-4 flex items-start gap-3">
        <Info className="w-5 h-5 text-blue-400 shrink-0 mt-0.5" />
        <div className="space-y-1 text-xs text-slate-300">
          <div className="font-bold text-white flex items-center gap-2">
            <span>Operational Constraints & Railway Safety Limits</span>
            <span className="text-[10px] px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-300 font-mono font-bold">
              MINIMUM HEADWAY = 3 MINUTES
            </span>
          </div>
          <p className="text-[11px] text-slate-400 leading-relaxed">
            Train positions and departure timestamps reflect scheduled timetable progression derived from community GTFS and published BMRCL schedules. Because live BMRCL GPS telemetry is not publicly connected, all headway recommendations function strictly as <strong>Decision Support Only</strong> for control-room operators and never override physical signaling interlocking.
          </p>
        </div>
      </div>

      {/* Timetable Schedule Cards / List */}
      <div className="bg-[#0d1424] border border-slate-800 rounded-xl p-5 space-y-4">
        <div className="flex items-center justify-between border-b border-slate-800 pb-3">
          <h3 className="text-sm font-bold text-white flex items-center gap-2">
            <Train className="w-4 h-4 text-purple-400" />
            Active Scheduled Corridors (BMRCL Namma Metro)
          </h3>
          <span className="text-xs text-slate-400 font-mono">Published Timetable Runs</span>
        </div>

        <div className="space-y-3">
          {schedules.map((sch) => (
            <div
              key={sch.id}
              className="p-4 bg-slate-900/90 border border-slate-800 rounded-xl flex flex-col md:flex-row md:items-center justify-between gap-4 text-xs hover:border-slate-700 transition"
            >
              <div className="space-y-1.5">
                <div className="flex items-center gap-2 font-bold text-white text-sm">
                  <span className="font-mono">{sch.train_code}</span>
                  <span className={`text-[10px] px-2 py-0.5 rounded font-semibold ${
                    sch.line_name.includes("Purple")
                      ? "bg-purple-500/20 text-purple-300 border border-purple-500/30"
                      : "bg-emerald-500/20 text-emerald-300 border border-emerald-500/30"
                  }`}>
                    {sch.line_name}
                  </span>
                  <span className="text-[10px] px-2 py-0.5 rounded bg-slate-800 text-slate-300 font-mono">
                    SCHEDULED RUN
                  </span>
                  {sch.conflict_detected && (
                    <span className="text-[10px] px-2 py-0.5 rounded bg-rose-500/20 text-rose-400 border border-rose-500/30 font-semibold flex items-center gap-1">
                      <AlertOctagon className="w-3 h-3" />
                      Advisory Conflict
                    </span>
                  )}
                </div>
                <div className="text-slate-300">
                  {sch.origin_station_name} → {sch.destination_station_name}
                </div>
                {sch.conflict_reason && (
                  <div className="text-[11px] text-amber-400 font-medium">
                    ⚠️ {sch.conflict_reason}
                  </div>
                )}
              </div>

              <div className="flex items-center gap-6">
                <div className="text-right space-y-0.5">
                  <div className="text-slate-400 text-[11px]">Headway Interval</div>
                  <div className="font-bold text-white font-mono text-sm">
                    {sch.headway_minutes} mins
                    {sch.recommended_headway !== sch.headway_minutes && (
                      <span className="text-purple-300 text-xs font-normal ml-1.5 font-mono">
                        (Rec: {Math.max(3, sch.recommended_headway)}m)
                      </span>
                    )}
                  </div>
                </div>

                <div className="text-right space-y-0.5">
                  <div className="text-slate-400 text-[11px]">Delay Feed Status</div>
                  <div className="font-mono text-emerald-400 text-xs font-semibold">
                    Live Feed Not Connected (On Timetable)
                  </div>
                </div>

                <button
                  onClick={() => handleOpenOverride(sch)}
                  className="px-3 py-2 rounded-lg bg-purple-600 hover:bg-purple-500 text-white font-bold transition flex items-center gap-1.5 shadow-md shadow-purple-600/20"
                >
                  <Sliders className="w-3.5 h-3.5" />
                  Headway Decision Support
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Headway Override Modal */}
      {modalOpen && selectedSchedule && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="w-full max-w-md bg-[#0d1424] border border-slate-700 rounded-2xl p-6 shadow-2xl space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <h3 className="text-base font-bold text-white flex items-center gap-2">
                <Sliders className="w-5 h-5 text-purple-400" />
                Dispatch Headway Decision Support
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
                  Target BMRCL Train Run
                </label>
                <div className="p-2.5 bg-slate-900 border border-slate-800 rounded-lg text-white font-mono">
                  {selectedSchedule.train_code} ({selectedSchedule.line_name})
                </div>
              </div>

              <div>
                <label className="block font-semibold text-slate-300 uppercase mb-1">
                  Recommended Headway Interval (Minutes)
                </label>
                <input
                  type="number"
                  min="3"
                  max="30"
                  value={newHeadway}
                  onChange={(e) => setNewHeadway(Number(e.target.value))}
                  className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-white font-mono text-sm focus:outline-none focus:border-purple-500"
                />
                <p className="text-[11px] text-amber-400 mt-1 font-semibold">
                  Safety Limit: Headway must be ≥ 3 minutes to maintain minimum safe headway.
                </p>
              </div>

              <div>
                <label className="block font-semibold text-slate-300 uppercase mb-1">
                  Decision Support Rationale
                </label>
                <input
                  type="text"
                  value={overrideReason}
                  onChange={(e) => setOverrideReason(e.target.value)}
                  className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-white text-xs focus:outline-none focus:border-purple-500"
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
                  className="w-1/2 py-2.5 bg-purple-600 hover:bg-purple-500 text-white font-bold rounded-lg transition shadow-lg shadow-purple-600/25"
                >
                  Apply Recommendation
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
