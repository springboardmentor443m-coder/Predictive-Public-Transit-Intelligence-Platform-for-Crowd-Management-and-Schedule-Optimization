import React, { useEffect, useState } from 'react';
import { Train, Clock, Sliders, AlertCircle, CheckCircle2, Zap, ArrowRight, ShieldAlert } from 'lucide-react';
import { api } from '../services/api';
import { LineSchedule, User } from '../types';

interface SchedulingViewProps {
  currentUser: User | null;
}

export const SchedulingView: React.FC<SchedulingViewProps> = ({ currentUser }) => {
  const [lines, setLines] = useState<LineSchedule[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedLine, setSelectedLine] = useState<LineSchedule | null>(null);
  const [newHeadway, setNewHeadway] = useState<number>(5.0);
  const [adjustReason, setAdjustReason] = useState('Mitigating passenger platform overcrowding');
  const [adjustMsg, setAdjustMsg] = useState<string | null>(null);

  // Delay simulation form
  const [delayTrainId, setDelayTrainId] = useState('TR-101');
  const [delayMins, setDelayMins] = useState(4);
  const [delayCause, setDelayCause] = useState('signal_malfunction');
  const [delayMsg, setDelayMsg] = useState<string | null>(null);
  const [optimizing, setOptimizing] = useState(false);

  const fetchLines = async () => {
    try {
      const data = await api.getLineSchedules();
      setLines(data);
      if (!selectedLine && data.length > 0) {
        setSelectedLine(data[0]);
        setNewHeadway(data[0].current_headway);
      }
    } catch (err) {
      console.error('Failed to load lines', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchLines();
  }, []);

  const handleAdjustHeadway = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedLine) return;
    try {
      await api.adjustLineFrequency(selectedLine.line, newHeadway, adjustReason);
      setAdjustMsg(`Headway on Line ${selectedLine.line} successfully updated to ${newHeadway} minutes.`);
      fetchLines();
      setTimeout(() => setAdjustMsg(null), 4000);
    } catch (err: any) {
      setAdjustMsg(`Error: ${err.message}`);
    }
  };

  const handleOptimizePeak = async () => {
    setOptimizing(true);
    try {
      const res = await api.optimizePeakSchedules();
      setAdjustMsg(`Automated Peak Optimization applied across ${res.optimized_lines_count} active corridor lines.`);
      fetchLines();
      setTimeout(() => setAdjustMsg(null), 4000);
    } catch (err: any) {
      setAdjustMsg(`Optimization error: ${err.message}`);
    } finally {
      setOptimizing(false);
    }
  };

  const handleReportDelay = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await api.reportTrainDelay(delayTrainId, delayMins, delayCause);
      setDelayMsg(`Delay of ${delayMins} min recorded on Train ${delayTrainId}. Station alerts broadcasted.`);
      setTimeout(() => setDelayMsg(null), 4000);
    } catch (err: any) {
      setDelayMsg(`Error: ${err.message}`);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header and Automated Peak Action */}
      <div className="bg-slate-900 border border-slate-800 p-6 rounded-2xl flex flex-col md:flex-row items-start md:items-center justify-between gap-4 shadow-xl">
        <div className="flex items-center space-x-3.5">
          <div className="p-3 bg-emerald-600/20 text-emerald-400 rounded-2xl border border-emerald-500/30">
            <Train className="w-7 h-7" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <h2 className="text-xl font-black text-white">Train Scheduling & Headway Optimization</h2>
              <span className="text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
                Active Operations
              </span>
            </div>
            <p className="text-xs text-slate-400 mt-1">
              Configure line train frequencies, dispatch peak shuttles, and handle operational delays.
            </p>
          </div>
        </div>

        <button
          onClick={handleOptimizePeak}
          disabled={optimizing}
          className="px-5 py-2.5 bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-white rounded-xl text-xs font-bold transition shadow-lg shadow-emerald-600/20 flex items-center space-x-2 cursor-pointer disabled:opacity-50"
        >
          <Zap className="w-4 h-4" />
          <span>{optimizing ? 'Executing Algorithm...' : 'Auto-Optimize Peak Headways'}</span>
        </button>
      </div>

      {adjustMsg && (
        <div className="p-3.5 bg-emerald-500/20 border border-emerald-500/40 rounded-xl text-xs text-emerald-300 flex items-center space-x-2">
          <CheckCircle2 className="w-4 h-4 flex-shrink-0" />
          <span>{adjustMsg}</span>
        </div>
      )}

      {/* Main Grid: Schedules Table & Control Panels */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Lines Schedule Table (2 spans) */}
        <div className="lg:col-span-2 bg-slate-900 border border-slate-800 rounded-2xl overflow-hidden shadow-xl">
          <div className="p-5 border-b border-slate-800 flex items-center justify-between">
            <h3 className="text-sm font-bold text-white flex items-center space-x-2">
              <Clock className="w-4 h-4 text-blue-400" />
              <span>Subway Lines Headway Matrix</span>
            </h3>
            <span className="text-xs text-slate-400">{lines.length} Transit Corridors</span>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs text-slate-300">
              <thead className="bg-slate-950/70 text-slate-400 uppercase font-bold text-[10px] tracking-wider border-b border-slate-800">
                <tr>
                  <th className="py-3 px-4">Line</th>
                  <th className="py-3 px-4">Corridor Name</th>
                  <th className="py-3 px-4 text-center">Current Headway</th>
                  <th className="py-3 px-4 text-center">AI Rec. Headway</th>
                  <th className="py-3 px-4 text-center">Operating Trains</th>
                  <th className="py-3 px-4 text-center">Peak Mode</th>
                  <th className="py-3 px-4 text-right">Dispatch Control</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 font-medium">
                {lines.map(line => {
                  const isSelected = selectedLine?.line === line.line;
                  return (
                    <tr
                      key={line.line}
                      className={`hover:bg-slate-800/40 transition cursor-pointer ${
                        isSelected ? 'bg-slate-800/60 border-l-4 border-blue-500' : ''
                      }`}
                      onClick={() => {
                        setSelectedLine(line);
                        setNewHeadway(line.current_headway);
                      }}
                    >
                      <td className="py-3 px-4">
                        <span
                          className="w-7 h-7 rounded-full flex items-center justify-center font-bold text-white text-xs shadow-md"
                          style={{ backgroundColor: line.color }}
                        >
                          {line.line}
                        </span>
                      </td>
                      <td className="py-3 px-4 font-bold text-white">{line.name}</td>
                      <td className="py-3 px-4 text-center font-black text-sm text-cyan-400">
                        {line.current_headway}m
                      </td>
                      <td className="py-3 px-4 text-center font-bold text-emerald-400">
                        {line.recommended_headway}m
                      </td>
                      <td className="py-3 px-4 text-center text-slate-300">
                        {line.active_train_count}
                      </td>
                      <td className="py-3 px-4 text-center">
                        <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase ${
                          line.peak_status === 'Peak' ? 'bg-purple-500/20 text-purple-300 border border-purple-500/30' : 'bg-slate-800 text-slate-400'
                        }`}>
                          {line.peak_status}
                        </span>
                      </td>
                      <td className="py-3 px-4 text-right">
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            setSelectedLine(line);
                            setNewHeadway(line.current_headway);
                          }}
                          className="px-2.5 py-1 bg-slate-800 hover:bg-blue-600 text-slate-300 hover:text-white rounded-lg text-xs font-semibold transition"
                        >
                          Adjust Headway
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>

        {/* Right Side: Adjust Headway & Delay Simulator (1 span) */}
        <div className="space-y-6">
          {/* Headway Adjuster Card */}
          <div className="bg-slate-900 border border-slate-800 p-5 rounded-2xl shadow-xl space-y-4">
            <div className="flex items-center space-x-2 border-b border-slate-800 pb-3">
              <Sliders className="w-4 h-4 text-blue-400" />
              <h3 className="text-sm font-bold text-white">
                Dispatch Headway Editor: Line {selectedLine?.line || '1'}
              </h3>
            </div>

            {selectedLine ? (
              <form onSubmit={handleAdjustHeadway} className="space-y-4">
                <div>
                  <div className="flex justify-between text-xs mb-1">
                    <span className="text-slate-400">Target Headway:</span>
                    <span className="font-black text-cyan-400 text-sm">{newHeadway} minutes</span>
                  </div>
                  <input
                    type="range"
                    min="2.0"
                    max="10.0"
                    step="0.5"
                    value={newHeadway}
                    onChange={e => setNewHeadway(parseFloat(e.target.value))}
                    className="w-full accent-blue-500 cursor-pointer"
                  />
                  <div className="flex justify-between text-[10px] text-slate-400 mt-1">
                    <span>2.0m (High Frequency)</span>
                    <span>10.0m (Off-Peak)</span>
                  </div>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-1">Operational Justification</label>
                  <input
                    type="text"
                    value={adjustReason}
                    onChange={e => setAdjustReason(e.target.value)}
                    required
                    className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-xl text-xs text-white placeholder-slate-500 focus:outline-none focus:border-blue-500"
                  />
                </div>

                <button
                  type="submit"
                  className="w-full py-2.5 bg-blue-600 hover:bg-blue-500 text-white rounded-xl text-xs font-bold transition shadow-md shadow-blue-600/30 cursor-pointer flex items-center justify-center space-x-1.5"
                >
                  <span>Apply Headway Directive</span>
                  <ArrowRight className="w-3.5 h-3.5" />
                </button>
              </form>
            ) : (
              <div className="text-xs text-slate-400">Select a line to configure frequency.</div>
            )}
          </div>

          {/* Delay Incident Simulator */}
          <div className="bg-slate-900 border border-slate-800 p-5 rounded-2xl shadow-xl space-y-4">
            <div className="flex items-center space-x-2 border-b border-slate-800 pb-3">
              <ShieldAlert className="w-4 h-4 text-amber-400" />
              <h3 className="text-sm font-bold text-white">Live Delay & Incident Simulator</h3>
            </div>

            {delayMsg && (
              <div className="p-3 bg-amber-500/20 border border-amber-500/40 rounded-xl text-xs text-amber-300">
                {delayMsg}
              </div>
            )}

            <form onSubmit={handleReportDelay} className="space-y-3">
              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">Target Train ID</label>
                <select
                  value={delayTrainId}
                  onChange={e => setDelayTrainId(e.target.value)}
                  className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-xl text-xs text-white focus:outline-none focus:border-blue-500"
                >
                  <option value="TR-101">TR-101 (Line 1 - Broadway)</option>
                  <option value="TR-401">TR-401 (Line 4 - Lexington)</option>
                  <option value="TR-701">TR-701 (Line 7 - Flushing)</option>
                  <option value="TR-A01">TR-A01 (Line A - 8th Ave)</option>
                  <option value="TR-L01">TR-L01 (Line L - Canarsie)</option>
                  <option value="TR-N01">TR-N01 (Line N - Broadway)</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">Delay Duration (Minutes)</label>
                <input
                  type="number"
                  min="1"
                  max="45"
                  value={delayMins}
                  onChange={e => setDelayMins(parseInt(e.target.value))}
                  className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-xl text-xs text-white focus:outline-none focus:border-blue-500"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">Incident Category</label>
                <select
                  value={delayCause}
                  onChange={e => setDelayCause(e.target.value)}
                  className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-xl text-xs text-white focus:outline-none focus:border-blue-500"
                >
                  <option value="signal_malfunction">Signal Sequencing Malfunction</option>
                  <option value="passenger_medical">Passenger Medical Assistance</option>
                  <option value="track_obstruction">Track Debris / Obstruction</option>
                  <option value="door_hold">Interlocking Door Hold</option>
                </select>
              </div>

              <button
                type="submit"
                className="w-full py-2.5 bg-amber-600 hover:bg-amber-500 text-white rounded-xl text-xs font-bold transition shadow-md shadow-amber-600/30 cursor-pointer"
              >
                Simulate Incident & Cascade Alerts
              </button>
            </form>
          </div>
        </div>
      </div>
    </div>
  );
};
