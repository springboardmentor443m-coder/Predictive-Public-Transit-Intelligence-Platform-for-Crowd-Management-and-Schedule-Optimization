import React, { useState } from 'react';
import {
  Sparkles,
  MapPin,
  Clock,
  Calendar,
  Building,
  Zap,
  CheckCircle,
  AlertCircle,
  Send,
  ArrowRight,
  RotateCcw,
} from 'lucide-react';
import StatusBadge from '../components/StatusBadge';
import { api } from '../api/client';

export default function RealTimePrediction({
  stations = [],
  onDispatchAlert,
  onNavigate,
}) {
  // Default values
  const defaultStation = stations.find((s) => s.name.includes('Grand Central')) || stations[0] || {
    name: 'Grand Central - 42 St',
    latitude: 40.7527,
    longitude: -73.9772,
    borough: 'Manhattan',
    structure: 'Subway',
  };

  const [selectedStationName, setSelectedStationName] = useState(defaultStation.name);
  const [latitude, setLatitude] = useState(defaultStation.latitude || 40.7527);
  const [longitude, setLongitude] = useState(defaultStation.longitude || -73.9772);
  const [borough, setBorough] = useState(defaultStation.borough || 'Manhattan');
  const [structure, setStructure] = useState(defaultStation.structure || 'Subway');

  const [hour, setHour] = useState(8);
  const [day, setDay] = useState(15);
  const [month, setMonth] = useState(9);
  const [year, setYear] = useState(2021);
  const [dayOfWeek, setDayOfWeek] = useState(2); // Wednesday
  const [isWeekend, setIsWeekend] = useState(0);
  const [isPeakHour, setIsPeakHour] = useState(1);

  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  // When station changes, auto-fill coordinates, borough, and structure
  const handleStationChange = (stationName) => {
    setSelectedStationName(stationName);
    const found = stations.find((s) => s.name === stationName);
    if (found) {
      setLatitude(found.latitude);
      setLongitude(found.longitude);
      setBorough(found.borough);
      setStructure(found.structure || 'Subway');
    }
  };

  // When hour changes, auto-update peak hour flag
  const handleHourChange = (newHour) => {
    setHour(newHour);
    const peak = [7, 8, 9, 16, 17, 18, 19].includes(newHour) ? 1 : 0;
    setIsPeakHour(peak);
  };

  // When day of week changes, auto-update weekend flag
  const handleDayOfWeekChange = (dow) => {
    setDayOfWeek(dow);
    setIsWeekend(dow >= 5 ? 1 : 0);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    const payload = {
      hour: Number(hour),
      day: Number(day),
      month: Number(month),
      year: Number(year),
      day_of_week: Number(dayOfWeek),
      is_weekend: Number(isWeekend),
      is_peak_hour: Number(isPeakHour),
      Latitude: parseFloat(latitude),
      Longitude: parseFloat(longitude),
      Borough: borough,
      Structure: structure,
      'Stop Name': selectedStationName,
    };

    try {
      const response = await api.predictCongestion(payload);
      setResult(response);
    } catch (err) {
      setError(err.message || 'Inference request failed. Please check backend connection.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Top Banner */}
      <div className="ops-panel p-5 bg-gradient-to-r from-[#111827] via-slate-900 to-[#1F293D] flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="text-xs font-mono font-bold px-2 py-0.5 rounded bg-teal-500/10 text-[#00D4AA] border border-teal-500/20">
              FASTAPI ML INFERENCE
            </span>
            <span className="text-xs text-slate-400 font-mono">
              REAL-TIME MODEL SERVING
            </span>
          </div>
          <h2 className="text-xl font-bold text-white flex items-center gap-2">
            <Sparkles size={20} className="text-[#00D4AA]" />
            <span>Real-Time Crowd Congestion Inference Console</span>
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Accepts transit coordinates and temporal features to output class probabilities and dispatch actions via <code className="text-sky-300">POST /predict</code>.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <span className="text-xs font-mono px-3 py-1.5 rounded bg-slate-900 border border-slate-800 text-slate-300">
            Model: <strong className="text-[#00D4AA]">Random Forest Classifier</strong>
          </span>
        </div>
      </div>

      {/* Main Grid: Input Form + Result Card */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Form (7 cols) */}
        <div className="lg:col-span-7 ops-panel p-6 space-y-5">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <h3 className="text-sm font-bold text-white flex items-center gap-2">
              <Zap size={16} className="text-[#00D4AA]" />
              <span>Transit Telemetry Parameters (Pydantic Schema)</span>
            </h3>
            <span className="text-[10px] font-mono text-slate-500">
              Payload Validation Active
            </span>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            {/* Station Preset Picker */}
            <div>
              <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1.5">
                Subway Station (Preset Coordinates & Borough)
              </label>
              <select
                value={selectedStationName}
                onChange={(e) => handleStationChange(e.target.value)}
                className="ops-select text-xs py-2"
              >
                {stations.map((s) => (
                  <option key={s.id || s.name} value={s.name}>
                    {s.name} ({s.borough} - {s.structure})
                  </option>
                ))}
              </select>
            </div>

            {/* Coordinates & Borough row */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
              <div>
                <label className="block text-[11px] font-semibold text-slate-400 uppercase mb-1">
                  Latitude
                </label>
                <input
                  type="number"
                  step="0.0001"
                  value={latitude}
                  onChange={(e) => setLatitude(parseFloat(e.target.value))}
                  className="ops-input text-xs font-mono"
                  required
                />
              </div>

              <div>
                <label className="block text-[11px] font-semibold text-slate-400 uppercase mb-1">
                  Longitude
                </label>
                <input
                  type="number"
                  step="0.0001"
                  value={longitude}
                  onChange={(e) => setLongitude(parseFloat(e.target.value))}
                  className="ops-input text-xs font-mono"
                  required
                />
              </div>

              <div>
                <label className="block text-[11px] font-semibold text-slate-400 uppercase mb-1">
                  Borough
                </label>
                <select
                  value={borough}
                  onChange={(e) => setBorough(e.target.value)}
                  className="ops-select text-xs"
                >
                  <option value="Manhattan">Manhattan</option>
                  <option value="Brooklyn">Brooklyn</option>
                  <option value="Queens">Queens</option>
                  <option value="Bronx">Bronx</option>
                </select>
              </div>

              <div>
                <label className="block text-[11px] font-semibold text-slate-400 uppercase mb-1">
                  Structure
                </label>
                <select
                  value={structure}
                  onChange={(e) => setStructure(e.target.value)}
                  className="ops-select text-xs"
                >
                  <option value="Subway">Subway</option>
                  <option value="Elevated">Elevated</option>
                  <option value="Open Cut">Open Cut</option>
                  <option value="At Grade">At Grade</option>
                </select>
              </div>
            </div>

            {/* Temporal Parameters */}
            <div className="p-4 rounded-lg bg-slate-900/80 border border-slate-800 space-y-3">
              <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider block">
                Temporal Peak Cycles & Timestamp
              </span>

              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                <div>
                  <label className="block text-[11px] font-semibold text-slate-400 mb-1">
                    Clock Hour (0-23)
                  </label>
                  <input
                    type="number"
                    min="0"
                    max="23"
                    value={hour}
                    onChange={(e) => handleHourChange(parseInt(e.target.value))}
                    className="ops-input text-xs font-mono"
                    required
                  />
                </div>

                <div>
                  <label className="block text-[11px] font-semibold text-slate-400 mb-1">
                    Day of Week
                  </label>
                  <select
                    value={dayOfWeek}
                    onChange={(e) => handleDayOfWeekChange(parseInt(e.target.value))}
                    className="ops-select text-xs"
                  >
                    <option value={0}>Monday (0)</option>
                    <option value={1}>Tuesday (1)</option>
                    <option value={2}>Wednesday (2)</option>
                    <option value={3}>Thursday (3)</option>
                    <option value={4}>Friday (4)</option>
                    <option value={5}>Saturday (5)</option>
                    <option value={6}>Sunday (6)</option>
                  </select>
                </div>

                <div>
                  <label className="block text-[11px] font-semibold text-slate-400 mb-1">
                    Month (1-12)
                  </label>
                  <input
                    type="number"
                    min="1"
                    max="12"
                    value={month}
                    onChange={(e) => setMonth(parseInt(e.target.value))}
                    className="ops-input text-xs font-mono"
                    required
                  />
                </div>

                <div>
                  <label className="block text-[11px] font-semibold text-slate-400 mb-1">
                    Year
                  </label>
                  <input
                    type="number"
                    min="2015"
                    max="2030"
                    value={year}
                    onChange={(e) => setYear(parseInt(e.target.value))}
                    className="ops-input text-xs font-mono"
                    required
                  />
                </div>
              </div>

              {/* Peak & Weekend Flags */}
              <div className="grid grid-cols-2 gap-3 pt-2">
                <div className="flex items-center justify-between p-2.5 rounded bg-slate-950 border border-slate-800">
                  <span className="text-xs text-slate-300 font-medium">
                    Peak Commute Hour:
                  </span>
                  <span
                    className={`font-mono text-xs font-bold px-2 py-0.5 rounded ${
                      isPeakHour
                        ? 'bg-amber-500/10 text-amber-400 border border-amber-500/30'
                        : 'bg-slate-800 text-slate-400'
                    }`}
                  >
                    {isPeakHour ? 'YES (Rush)' : 'NO (Off-Peak)'}
                  </span>
                </div>

                <div className="flex items-center justify-between p-2.5 rounded bg-slate-950 border border-slate-800">
                  <span className="text-xs text-slate-300 font-medium">
                    Weekend Schedule:
                  </span>
                  <span
                    className={`font-mono text-xs font-bold px-2 py-0.5 rounded ${
                      isWeekend
                        ? 'bg-purple-500/10 text-purple-400 border border-purple-500/30'
                        : 'bg-slate-800 text-slate-400'
                    }`}
                  >
                    {isWeekend ? 'YES (Weekend)' : 'NO (Weekday)'}
                  </span>
                </div>
              </div>
            </div>

            {error && (
              <div className="p-3 rounded bg-rose-500/10 border border-rose-500/30 text-rose-300 text-xs flex items-start gap-2">
                <AlertCircle size={16} className="shrink-0 mt-0.5" />
                <span>{error}</span>
              </div>
            )}

            <button
              type="submit"
              disabled={loading}
              className="btn-primary w-full justify-center py-2.5 text-sm font-bold shadow-lg shadow-teal-500/20 disabled:opacity-50"
            >
              <Sparkles size={16} className={loading ? 'animate-spin' : ''} />
              <span>{loading ? 'Running Random Forest Inference...' : 'Predict Subway Congestion Level'}</span>
            </button>
          </form>
        </div>

        {/* Right Output Panel (5 cols) */}
        <div className="lg:col-span-5 ops-panel p-6 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between border-b border-slate-800 pb-3 mb-4">
              <h3 className="text-sm font-bold text-white flex items-center gap-2">
                <CheckCircle size={16} className="text-[#38BDF8]" />
                <span>Model Output & Operational Recommendation</span>
              </h3>
              <span className="text-[10px] font-mono text-slate-500">
                JSON Response
              </span>
            </div>

            {result ? (
              <div className="space-y-4 animate-in fade-in zoom-in duration-200">
                {/* Result Hero Badge */}
                <div
                  className={`p-5 rounded-lg border-2 text-center space-y-2 ${
                    result.congestion_level === 'High'
                      ? 'bg-rose-500/10 border-rose-500 text-rose-400'
                      : result.congestion_level === 'Medium'
                      ? 'bg-amber-500/10 border-amber-500 text-amber-400'
                      : 'bg-emerald-500/10 border-emerald-500 text-emerald-400'
                  }`}
                >
                  <div className="text-xs uppercase font-bold tracking-widest text-slate-300">
                    Predicted Congestion Level
                  </div>
                  <div className="text-3xl font-black font-mono tracking-tight text-white">
                    {result.congestion_level.toUpperCase()} CONGESTION
                  </div>
                  <div className="inline-block px-3 py-1 rounded-full bg-slate-900 border border-slate-700 font-mono text-xs font-bold text-white">
                    Confidence: {(result.confidence * 100).toFixed(1)}%
                  </div>
                </div>

                {/* Directive & Alert Message */}
                <div className="p-4 rounded-lg bg-slate-900 border border-slate-800 space-y-2 text-xs">
                  <div>
                    <span className="text-slate-400 uppercase font-semibold text-[10px]">
                      Operational Notice:
                    </span>
                    <p className="text-white font-medium mt-0.5">
                      {result.alert_message}
                    </p>
                  </div>
                  <div className="pt-2 border-t border-slate-800">
                    <span className="text-slate-400 uppercase font-semibold text-[10px]">
                      Recommended Transit Action:
                    </span>
                    <p className="text-[#00D4AA] font-bold text-sm mt-0.5">
                      {result.recommendation}
                    </p>
                  </div>
                </div>

                {/* Class Probabilities Distribution */}
                {result.probabilities && (
                  <div className="p-4 rounded-lg bg-slate-900/80 border border-slate-800 space-y-2.5">
                    <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block">
                      Class Probabilities Distribution
                    </span>

                    {Object.entries(result.probabilities).map(([tier, prob]) => {
                      const pct = Math.round(Number(prob) * 100);
                      const barColor =
                        tier === 'High'
                          ? '#EF4444'
                          : tier === 'Medium'
                          ? '#F59E0B'
                          : '#10B981';

                      return (
                        <div key={tier} className="space-y-1">
                          <div className="flex justify-between text-xs font-mono">
                            <span className="text-slate-300 font-medium">{tier}</span>
                            <span className="text-white font-bold">{pct}%</span>
                          </div>
                          <div className="h-2 w-full bg-slate-800 rounded-full overflow-hidden">
                            <div
                              className="h-full rounded-full transition-all duration-500"
                              style={{ width: `${pct}%`, backgroundColor: barColor }}
                            />
                          </div>
                        </div>
                      );
                    })}
                  </div>
                )}
              </div>
            ) : (
              <div className="py-16 text-center space-y-3">
                <div className="w-12 h-12 rounded-full bg-slate-800/80 mx-auto flex items-center justify-center text-slate-400">
                  <Sparkles size={22} className="text-[#00D4AA]" />
                </div>
                <div className="text-slate-300 font-medium text-sm">
                  Ready for Real-Time Inference
                </div>
                <p className="text-xs text-slate-500 max-w-xs mx-auto">
                  Select transit parameters and click "Predict Subway Congestion Level" to execute model inference.
                </p>
              </div>
            )}
          </div>

          {result && (
            <div className="pt-4 border-t border-slate-800 flex gap-2">
              <button
                onClick={() => {
                  if (onDispatchAlert) {
                    onDispatchAlert({
                      id: `ALT-${Date.now().toString().slice(-4)}`,
                      station: selectedStationName,
                      borough: borough,
                      severity: result.congestion_level,
                      message: result.alert_message,
                      recommendation: result.recommendation,
                      timestamp: new Date().toLocaleTimeString(),
                      status: 'Active',
                    });
                  }
                  if (onNavigate) onNavigate('alerts-center');
                }}
                className="btn-primary w-full justify-center text-xs"
              >
                <Send size={13} />
                <span>Dispatch to Alert Center</span>
              </button>

              <button
                onClick={() => {
                  if (onNavigate) onNavigate('schedule-management');
                }}
                className="btn-secondary w-full justify-center text-xs"
              >
                <span>Adjust Headway &rarr;</span>
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
