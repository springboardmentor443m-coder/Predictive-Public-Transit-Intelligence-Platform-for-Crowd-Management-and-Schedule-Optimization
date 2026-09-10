import React, { useState, useEffect } from 'react';
import { 
  STATIONS, 
  LINES, 
  DAYS_OF_WEEK, 
  CAPACITIES 
} from '../data/constants';
import { predictOccupancy } from '../services/api';
import OccupancyGauge from './OccupancyGauge';
import AlertBanner from './AlertBanner';
import QuickPresets from './QuickPresets';
import { 
  ArrowLeftRight, 
  Sliders, 
  Clock, 
  Calendar, 
  Train, 
  Layers, 
  Cpu, 
  Sparkles, 
  CheckCircle2, 
  AlertOctagon,
  RefreshCw
} from 'lucide-react';

export default function PredictionCalculator() {
  const [formData, setFormData] = useState({
    from_station: 4, // Rajiv Chowk
    to_station: 2,   // Hauz Khas
    line_color: 3,   // Yellow Line
    day_of_week: 1,  // Monday
    entry_hour: 9,   // 9 AM Peak
    train_capacity: 2400
  });

  const [loading, setLoading] = useState(false);
  const [prediction, setPrediction] = useState(null);
  const [activePresetIndex, setActivePresetIndex] = useState(null);
  const [autoCalculate, setAutoCalculate] = useState(true);

  // Compute cyclical mathematical values on the fly for transparency
  const hourSin = Math.sin(2 * Math.PI * formData.entry_hour / 24.0).toFixed(4);
  const hourCos = Math.cos(2 * Math.PI * formData.entry_hour / 24.0).toFixed(4);
  const isPeak = (formData.entry_hour >= 8 && formData.entry_hour <= 11) || 
                 (formData.entry_hour >= 17 && formData.entry_hour <= 20);

  const handlePredict = async (overrideData) => {
    setLoading(true);
    try {
      const dataToSend = overrideData || formData;
      const res = await predictOccupancy(dataToSend);
      setPrediction(res);
    } catch (err) {
      console.error("Calculation failed:", err);
    } finally {
      setLoading(false);
    }
  };

  // Initial calculation on mount or when inputs change if auto-calculate enabled
  useEffect(() => {
    if (autoCalculate) {
      const timer = setTimeout(() => {
        handlePredict();
      }, 150);
      return () => clearTimeout(timer);
    }
  }, [formData, autoCalculate]);

  const handleStationSwap = () => {
    setFormData(prev => ({
      ...prev,
      from_station: prev.to_station,
      to_station: prev.from_station
    }));
    setActivePresetIndex(null);
  };

  const handlePresetSelect = (preset, idx) => {
    const updated = {
      from_station: preset.from_station,
      to_station: preset.to_station,
      line_color: preset.line_color,
      day_of_week: preset.day_of_week,
      entry_hour: preset.hour,
      train_capacity: preset.train_capacity
    };
    setFormData(updated);
    setActivePresetIndex(idx);
    handlePredict(updated);
  };

  const selectedFromStation = STATIONS.find(s => s.id === Number(formData.from_station));
  const selectedToStation = STATIONS.find(s => s.id === Number(formData.to_station));
  const selectedLine = LINES.find(l => l.id === Number(formData.line_color));
  const selectedDay = DAYS_OF_WEEK.find(d => d.id === Number(formData.day_of_week));

  return (
    <div className="space-y-8">
      
      {/* Top Banner / Title */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 glass-panel rounded-2xl p-6 border border-cyan-500/20">
        <div>
          <div className="flex items-center space-x-2">
            <span className="p-2 rounded-xl bg-cyan-500/10 text-cyan-400 border border-cyan-500/30">
              <Cpu className="w-5 h-5" />
            </span>
            <h2 className="text-xl font-bold text-white font-display">
              Live Passenger Crowd Density Calculator
            </h2>
          </div>
          <p className="text-sm text-slate-400 mt-1">
            Real-time inference using XGBoost Regressor (<span className="text-cyan-400 font-mono">metroflow_xgboost_model.json</span>) with cyclical time encodings.
          </p>
        </div>

        <div className="flex items-center space-x-3">
          <label className="flex items-center space-x-2 text-xs font-mono text-slate-300 cursor-pointer bg-slate-900/90 px-3 py-2 rounded-xl border border-slate-800">
            <input
              type="checkbox"
              checked={autoCalculate}
              onChange={(e) => setAutoCalculate(e.target.checked)}
              className="rounded border-slate-700 text-cyan-500 focus:ring-cyan-500 bg-slate-800"
            />
            <span>Auto-Infer on Change</span>
          </label>

          <button
            onClick={() => handlePredict()}
            disabled={loading}
            className="flex items-center space-x-2 px-5 py-2.5 rounded-xl bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-white font-semibold text-xs transition-all shadow-lg shadow-cyan-500/25 border border-cyan-400/40 active:scale-95 disabled:opacity-50"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
            <span>{loading ? 'Inferencing...' : 'Run Prediction'}</span>
          </button>
        </div>
      </div>

      {/* 1-Click Simulation Presets */}
      <QuickPresets 
        onSelectPreset={handlePresetSelect} 
        activePresetIndex={activePresetIndex} 
      />

      {/* Main Grid: Form Inputs & Result Visualizer */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        
        {/* LEFT FORM COLUMN (7 cols) */}
        <div className="lg:col-span-7 glass-panel rounded-2xl p-6 border border-slate-800 space-y-6">
          
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <div className="flex items-center space-x-2">
              <Sliders className="w-4 h-4 text-cyan-400" />
              <h3 className="text-sm font-bold uppercase tracking-wider text-slate-200 font-mono">
                Simulation Parameters
              </h3>
            </div>
            <span className="text-[11px] font-mono text-slate-500">
              Station & Temporal Matrix
            </span>
          </div>

          {/* Station Origin & Destination Selectors */}
          <div className="grid grid-cols-1 sm:grid-cols-11 gap-3 items-center">
            {/* Origin Station */}
            <div className="sm:col-span-5 space-y-1.5">
              <label className="text-xs font-semibold text-slate-300 flex items-center gap-1.5">
                <span className="w-2 h-2 rounded-full bg-cyan-400"></span>
                Origin Station (From)
              </label>
              <select
                value={formData.from_station}
                onChange={(e) => {
                  setFormData({ ...formData, from_station: Number(e.target.value) });
                  setActivePresetIndex(null);
                }}
                className="w-full bg-slate-900/90 text-white border border-slate-700/80 rounded-xl px-3.5 py-2.5 text-sm focus:border-cyan-400 focus:outline-none transition-colors"
              >
                {STATIONS.map((s) => (
                  <option key={s.id} value={s.id}>
                    {s.name} ({s.code})
                  </option>
                ))}
              </select>
            </div>

            {/* Swap Button */}
            <div className="sm:col-span-1 flex justify-center pt-5 sm:pt-4">
              <button
                type="button"
                onClick={handleStationSwap}
                title="Swap Origin and Destination"
                className="p-2.5 rounded-xl bg-slate-800/80 hover:bg-slate-700 text-slate-300 hover:text-cyan-400 border border-slate-700 transition-all hover:scale-105 active:scale-95"
              >
                <ArrowLeftRight className="w-4 h-4" />
              </button>
            </div>

            {/* Destination Station */}
            <div className="sm:col-span-5 space-y-1.5">
              <label className="text-xs font-semibold text-slate-300 flex items-center gap-1.5">
                <span className="w-2 h-2 rounded-full bg-pink-400"></span>
                Destination Station (To)
              </label>
              <select
                value={formData.to_station}
                onChange={(e) => {
                  setFormData({ ...formData, to_station: Number(e.target.value) });
                  setActivePresetIndex(null);
                }}
                className="w-full bg-slate-900/90 text-white border border-slate-700/80 rounded-xl px-3.5 py-2.5 text-sm focus:border-cyan-400 focus:outline-none transition-colors"
              >
                {STATIONS.map((s) => (
                  <option key={s.id} value={s.id}>
                    {s.name} ({s.code})
                  </option>
                ))}
              </select>
            </div>
          </div>

          {/* Line Color Selector */}
          <div className="space-y-2">
            <label className="text-xs font-semibold text-slate-300 flex items-center gap-1.5">
              <Layers className="w-3.5 h-3.5 text-cyan-400" />
              Metro Corridor (Line Color)
            </label>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5">
              {LINES.map((line) => {
                const isSelected = Number(formData.line_color) === line.id;
                return (
                  <button
                    key={line.id}
                    type="button"
                    onClick={() => {
                      setFormData({ ...formData, line_color: line.id });
                      setActivePresetIndex(null);
                    }}
                    className={`flex items-center space-x-2 p-2.5 rounded-xl border text-xs font-semibold transition-all ${
                      isSelected
                        ? `${line.bg} ${line.border} ${line.text} ring-1 ring-offset-0 shadow-sm`
                        : 'bg-slate-900/60 border-slate-800 text-slate-400 hover:border-slate-700 hover:text-slate-200'
                    }`}
                  >
                    <span 
                      className="w-3 h-3 rounded-full flex-shrink-0"
                      style={{ backgroundColor: line.color }}
                    ></span>
                    <span className="truncate">{line.name}</span>
                  </button>
                );
              })}
            </div>
          </div>

          {/* Day of Week Picker */}
          <div className="space-y-2">
            <label className="text-xs font-semibold text-slate-300 flex items-center gap-1.5">
              <Calendar className="w-3.5 h-3.5 text-cyan-400" />
              Day of Week
            </label>
            <div className="grid grid-cols-4 sm:grid-cols-7 gap-1.5">
              {DAYS_OF_WEEK.map((day) => {
                const isSelected = Number(formData.day_of_week) === day.id;
                const isWeekend = day.name === 'Saturday' || day.name === 'Sunday';
                return (
                  <button
                    key={day.id}
                    type="button"
                    onClick={() => {
                      setFormData({ ...formData, day_of_week: day.id });
                      setActivePresetIndex(null);
                    }}
                    className={`py-2 px-1 rounded-xl text-xs font-mono font-medium border text-center transition-all ${
                      isSelected
                        ? 'bg-cyan-500/20 text-cyan-300 border-cyan-400/80 shadow-sm'
                        : isWeekend
                          ? 'bg-slate-900/40 border-slate-800 text-slate-500 hover:text-slate-300'
                          : 'bg-slate-900/60 border-slate-800 text-slate-400 hover:border-slate-700 hover:text-slate-200'
                    }`}
                  >
                    <div className="font-bold">{day.short}</div>
                  </button>
                );
              })}
            </div>
          </div>

          {/* 24-Hour Interactive Slider */}
          <div className="space-y-3 p-4 rounded-xl bg-slate-900/70 border border-slate-800">
            <div className="flex items-center justify-between">
              <label className="text-xs font-semibold text-slate-300 flex items-center gap-1.5">
                <Clock className="w-3.5 h-3.5 text-cyan-400" />
                Transit Entry Time (24-Hour Clock)
              </label>
              
              <div className="flex items-center space-x-2">
                {isPeak ? (
                  <span className="px-2 py-0.5 text-[10px] font-bold uppercase rounded bg-red-500/20 text-red-400 border border-red-500/30 flex items-center gap-1 animate-pulse">
                    <AlertOctagon className="w-3 h-3" />
                    Rush Hour (Peak Flag = 1)
                  </span>
                ) : (
                  <span className="px-2 py-0.5 text-[10px] font-bold uppercase rounded bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">
                    Off-Peak (Peak Flag = 0)
                  </span>
                )}
                
                <span className="px-2.5 py-1 text-sm font-bold font-mono text-cyan-300 bg-slate-800 rounded-lg border border-slate-700">
                  {formData.entry_hour.toString().padStart(2, '0')}:00
                </span>
              </div>
            </div>

            <input
              type="range"
              min="0"
              max="23"
              step="1"
              value={formData.entry_hour}
              onChange={(e) => {
                setFormData({ ...formData, entry_hour: Number(e.target.value) });
                setActivePresetIndex(null);
              }}
              className="w-full h-2 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-cyan-400 focus:outline-none"
            />

            {/* Time markers bar */}
            <div className="flex justify-between text-[10px] font-mono text-slate-500 px-1">
              <span>00:00 (Night)</span>
              <span className="text-red-400 font-semibold">08-11 (Morning Peak)</span>
              <span>12:00</span>
              <span className="text-red-400 font-semibold">17-20 (Evening Peak)</span>
              <span>23:00</span>
            </div>
          </div>

          {/* Train Capacity Selector */}
          <div className="space-y-2">
            <label className="text-xs font-semibold text-slate-300 flex items-center gap-1.5">
              <Train className="w-3.5 h-3.5 text-cyan-400" />
              Train Formation / Capacity Rake
            </label>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-2.5">
              {CAPACITIES.map((cap) => {
                const isSelected = Number(formData.train_capacity) === cap.value;
                return (
                  <button
                    key={cap.value}
                    type="button"
                    onClick={() => {
                      setFormData({ ...formData, train_capacity: cap.value });
                      setActivePresetIndex(null);
                    }}
                    className={`p-3 rounded-xl border text-left transition-all ${
                      isSelected
                        ? 'bg-cyan-500/15 border-cyan-400 text-cyan-200 ring-1 ring-cyan-400'
                        : 'bg-slate-900/60 border-slate-800 text-slate-400 hover:border-slate-700 hover:text-slate-200'
                    }`}
                  >
                    <p className="text-xs font-bold text-white">{cap.label}</p>
                    <p className="text-[10px] text-slate-400 mt-0.5">{cap.desc}</p>
                  </button>
                );
              })}
            </div>
          </div>

        </div>

        {/* RIGHT PREDICTION DISPLAY COLUMN (5 cols) */}
        <div className="lg:col-span-5 space-y-6">
          
          {/* Visual Occupancy Gauge */}
          <OccupancyGauge 
            prediction={prediction} 
            capacity={formData.train_capacity} 
          />

          {/* Real-Time Operational Alert Directive */}
          <AlertBanner 
            alertStatus={prediction?.alert_status}
            fleetAction={prediction?.fleet_action}
            headway={prediction?.recommended_headway_min}
          />

          {/* Feature Matrix Inspector (AI Transparency) */}
          <div className="p-4 rounded-2xl bg-slate-900/70 border border-slate-800 space-y-2.5 text-xs font-mono">
            <div className="flex items-center justify-between text-slate-400 border-b border-slate-800 pb-2">
              <span className="font-bold uppercase tracking-wider text-[11px] text-slate-300 flex items-center gap-1.5">
                <Cpu className="w-3.5 h-3.5 text-cyan-400" />
                XGBoost Feature Vector
              </span>
              <span className="text-[10px] text-cyan-400">9 Feature Inputs</span>
            </div>

            <div className="grid grid-cols-2 gap-2 text-[11px] text-slate-300 pt-1">
              <div><span className="text-slate-500">Entry_Hour:</span> {formData.entry_hour}</div>
              <div><span className="text-slate-500">Day_of_Week:</span> {formData.day_of_week} ({selectedDay?.name})</div>
              <div><span className="text-slate-500">Is_Peak_Hour:</span> {isPeak ? 1 : 0}</div>
              <div><span className="text-slate-500">Hour_Sin:</span> {hourSin}</div>
              <div><span className="text-slate-500">Hour_Cos:</span> {hourCos}</div>
              <div><span className="text-slate-500">From_Station:</span> {formData.from_station} ({selectedFromStation?.code})</div>
              <div><span className="text-slate-500">To_Station:</span> {formData.to_station} ({selectedToStation?.code})</div>
              <div><span className="text-slate-500">Line_Color:</span> {formData.line_color} ({selectedLine?.name})</div>
              <div className="col-span-2"><span className="text-slate-500">Train_Capacity:</span> {formData.train_capacity} pax</div>
            </div>
          </div>

        </div>

      </div>

    </div>
  );
}
