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
  RefreshCw,
  Info,
  Check
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
  const [justCalculated, setJustCalculated] = useState(false);
  const [lastCalculatedAt, setLastCalculatedAt] = useState(null);

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
      setJustCalculated(true);
      setLastCalculatedAt(new Date().toLocaleTimeString());
      setTimeout(() => setJustCalculated(false), 2000);
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
    <div className="space-y-10">
      
      {/* Top Banner / Title with More Breathing Room */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-6 glass-panel rounded-3xl p-8 border border-cyan-500/20 shadow-2xl">
        <div className="space-y-2">
          <div className="flex items-center space-x-3">
            <span className="p-2.5 rounded-2xl bg-cyan-500/15 text-cyan-400 border border-cyan-500/30 shadow-inner">
              <Cpu className="w-6 h-6" />
            </span>
            <h2 className="text-2xl font-bold text-white font-display tracking-tight">
              Live Passenger Crowd Density Calculator
            </h2>
          </div>
          <p className="text-sm text-slate-300 leading-relaxed max-w-3xl">
            Select any station route or time below. The <span className="text-cyan-400 font-mono font-semibold">XGBoost Regressor</span> computes cyclical time features in real time to forecast passenger loads, platform crowd risks, and optimal train dispatch headways.
          </p>
        </div>

        <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-3">
          <label className="flex items-center space-x-2.5 text-xs font-mono text-slate-300 cursor-pointer bg-slate-900/90 px-4 py-3 rounded-2xl border border-slate-800 shadow-sm hover:border-slate-700 transition-colors">
            <input
              type="checkbox"
              checked={autoCalculate}
              onChange={(e) => setAutoCalculate(e.target.checked)}
              className="w-4 h-4 rounded border-slate-700 text-cyan-500 focus:ring-cyan-500 bg-slate-800 cursor-pointer"
            />
            <span className="select-none font-medium">Auto-Calculate on Change</span>
          </label>

          <button
            onClick={() => handlePredict()}
            disabled={loading}
            className={`flex items-center justify-center space-x-2 px-6 py-3 rounded-2xl font-semibold text-xs transition-all duration-300 shadow-xl border active:scale-95 ${
              justCalculated 
                ? 'bg-emerald-500 text-white border-emerald-400 shadow-emerald-500/25 ring-2 ring-emerald-400' 
                : 'bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-white border-cyan-400/40 shadow-cyan-500/25'
            }`}
          >
            {justCalculated ? (
              <>
                <Check className="w-4 h-4 animate-scale" />
                <span>Calculated!</span>
              </>
            ) : (
              <>
                <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
                <span>{loading ? 'Inferencing...' : 'Run Prediction'}</span>
              </>
            )}
          </button>
        </div>
      </div>

      {/* 1-Click Simulation Presets (5 Corridors Covering All 5 Master Stations) */}
      <div className="glass-panel rounded-3xl p-6 border border-slate-800/80">
        <QuickPresets 
          onSelectPreset={handlePresetSelect} 
          activePresetIndex={activePresetIndex} 
        />
      </div>

      {/* Main Grid: Form Inputs & Result Visualizer with Enhanced Spacing */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
        
        {/* LEFT FORM COLUMN: Custom Simulation Parameters (7 cols) */}
        <div className="lg:col-span-7 glass-panel rounded-3xl p-8 border border-slate-800 space-y-8 shadow-xl">
          
          <div className="flex items-center justify-between border-b border-slate-800/90 pb-4">
            <div className="space-y-1">
              <div className="flex items-center space-x-2.5">
                <Sliders className="w-5 h-5 text-cyan-400" />
                <h3 className="text-base font-bold uppercase tracking-wider text-slate-100 font-display">
                  Custom Simulation Parameters
                </h3>
              </div>
              <p className="text-xs text-slate-400">
                Configure any Origin/Destination station, line corridor, day, and time
              </p>
            </div>
            
            {lastCalculatedAt && (
              <span className="hidden sm:inline-block px-3 py-1 text-[11px] font-mono text-cyan-400 bg-cyan-950/60 rounded-xl border border-cyan-800/60">
                Updated: {lastCalculatedAt}
              </span>
            )}
          </div>

          {/* Station Origin & Destination Selectors */}
          <div className="space-y-2">
            <div className="grid grid-cols-1 sm:grid-cols-11 gap-4 items-center">
              {/* Origin Station */}
              <div className="sm:col-span-5 space-y-2">
                <label className="text-xs font-bold text-slate-300 flex items-center gap-2">
                  <span className="w-2.5 h-2.5 rounded-full bg-cyan-400 ring-2 ring-cyan-400/20"></span>
                  Origin Station (From)
                </label>
                <select
                  value={formData.from_station}
                  onChange={(e) => {
                    setFormData({ ...formData, from_station: Number(e.target.value) });
                    setActivePresetIndex(null);
                  }}
                  className="w-full bg-slate-900/90 text-white font-medium border border-slate-700/80 rounded-2xl px-4 py-3 text-sm focus:border-cyan-400 focus:ring-1 focus:ring-cyan-400 focus:outline-none transition-all cursor-pointer shadow-inner"
                >
                  {STATIONS.map((s) => (
                    <option key={s.id} value={s.id}>
                      {s.name} ({s.code})
                    </option>
                  ))}
                </select>
              </div>

              {/* Swap Button */}
              <div className="sm:col-span-1 flex justify-center pt-2 sm:pt-6">
                <button
                  type="button"
                  onClick={handleStationSwap}
                  title="Swap Origin and Destination"
                  className="p-3 rounded-2xl bg-slate-800/90 hover:bg-slate-700 text-slate-300 hover:text-cyan-400 border border-slate-700 transition-all hover:scale-110 active:scale-95 shadow-md"
                >
                  <ArrowLeftRight className="w-4 h-4" />
                </button>
              </div>

              {/* Destination Station */}
              <div className="sm:col-span-5 space-y-2">
                <label className="text-xs font-bold text-slate-300 flex items-center gap-2">
                  <span className="w-2.5 h-2.5 rounded-full bg-pink-400 ring-2 ring-pink-400/20"></span>
                  Destination Station (To)
                </label>
                <select
                  value={formData.to_station}
                  onChange={(e) => {
                    setFormData({ ...formData, to_station: Number(e.target.value) });
                    setActivePresetIndex(null);
                  }}
                  className="w-full bg-slate-900/90 text-white font-medium border border-slate-700/80 rounded-2xl px-4 py-3 text-sm focus:border-cyan-400 focus:ring-1 focus:ring-cyan-400 focus:outline-none transition-all cursor-pointer shadow-inner"
                >
                  {STATIONS.map((s) => (
                    <option key={s.id} value={s.id}>
                      {s.name} ({s.code})
                    </option>
                  ))}
                </select>
              </div>
            </div>

            <p className="text-[11px] text-slate-400 italic pt-1 flex items-center gap-1.5">
              <Info className="w-3.5 h-3.5 text-cyan-400" />
              Route: <span className="text-slate-200 font-semibold">{selectedFromStation?.name}</span> ➔ <span className="text-slate-200 font-semibold">{selectedToStation?.name}</span>
            </p>
          </div>

          {/* Line Color Selector */}
          <div className="space-y-3">
            <label className="text-xs font-bold text-slate-300 flex items-center gap-2">
              <Layers className="w-4 h-4 text-cyan-400" />
              Metro Corridor (Line Color)
            </label>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
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
                    className={`flex items-center space-x-2.5 p-3.5 rounded-2xl border text-xs font-semibold transition-all duration-200 ${
                      isSelected
                        ? `${line.bg} ${line.border} ${line.text} ring-2 ring-offset-0 shadow-lg scale-[1.02]`
                        : 'bg-slate-900/60 border-slate-800 text-slate-400 hover:border-slate-700 hover:text-slate-200 hover:bg-slate-800/40'
                    }`}
                  >
                    <span 
                      className="w-3.5 h-3.5 rounded-full flex-shrink-0 shadow-sm"
                      style={{ backgroundColor: line.color }}
                    ></span>
                    <span className="truncate">{line.name}</span>
                  </button>
                );
              })}
            </div>
          </div>

          {/* Day of Week Picker */}
          <div className="space-y-3">
            <label className="text-xs font-bold text-slate-300 flex items-center gap-2">
              <Calendar className="w-4 h-4 text-cyan-400" />
              Day of Week
            </label>
            <div className="grid grid-cols-4 sm:grid-cols-7 gap-2">
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
                    className={`py-3 px-2 rounded-2xl text-xs font-mono font-medium border text-center transition-all ${
                      isSelected
                        ? 'bg-cyan-500/20 text-cyan-300 border-cyan-400 shadow-md ring-1 ring-cyan-400 font-bold'
                        : isWeekend
                          ? 'bg-slate-900/40 border-slate-800 text-slate-500 hover:text-slate-300'
                          : 'bg-slate-900/60 border-slate-800 text-slate-400 hover:border-slate-700 hover:text-slate-200'
                    }`}
                  >
                    <div>{day.short}</div>
                  </button>
                );
              })}
            </div>
          </div>

          {/* 24-Hour Interactive Slider with Rich Feedback */}
          <div className="space-y-4 p-6 rounded-3xl bg-slate-900/80 border border-slate-800 shadow-inner">
            <div className="flex items-center justify-between flex-wrap gap-2">
              <label className="text-xs font-bold text-slate-200 flex items-center gap-2">
                <Clock className="w-4 h-4 text-cyan-400" />
                Transit Entry Time (24-Hour Format)
              </label>
              
              <div className="flex items-center space-x-2.5">
                {isPeak ? (
                  <span className="px-3 py-1 text-[11px] font-bold uppercase rounded-xl bg-red-500/20 text-red-300 border border-red-500/40 flex items-center gap-1.5 animate-pulse">
                    <AlertOctagon className="w-3.5 h-3.5 text-red-400" />
                    Rush Hour (Peak Flag = 1)
                  </span>
                ) : (
                  <span className="px-3 py-1 text-[11px] font-bold uppercase rounded-xl bg-emerald-500/20 text-emerald-300 border border-emerald-500/40">
                    Off-Peak (Peak Flag = 0)
                  </span>
                )}
                
                <span className="px-3.5 py-1.5 text-base font-bold font-mono text-cyan-300 bg-slate-950 rounded-xl border border-slate-700 shadow-inner">
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
              className="w-full h-2.5 bg-slate-950 rounded-lg appearance-none cursor-pointer accent-cyan-400 focus:outline-none"
            />

            {/* Time markers bar */}
            <div className="flex justify-between text-[11px] font-mono text-slate-400 px-1 pt-1">
              <span>00:00 (Night)</span>
              <span className="text-red-400 font-semibold">08:00–11:00 (AM Peak)</span>
              <span>12:00 (Midday)</span>
              <span className="text-red-400 font-semibold">17:00–20:00 (PM Peak)</span>
              <span>23:00 (Late Night)</span>
            </div>
          </div>

          {/* Train Capacity Selector */}
          <div className="space-y-3">
            <label className="text-xs font-bold text-slate-300 flex items-center gap-2">
              <Train className="w-4 h-4 text-cyan-400" />
              Train Formation / Capacity Rake
            </label>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
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
                    className={`p-4 rounded-2xl border text-left transition-all ${
                      isSelected
                        ? 'bg-cyan-500/15 border-cyan-400 text-cyan-200 ring-2 ring-cyan-400 shadow-md'
                        : 'bg-slate-900/60 border-slate-800 text-slate-400 hover:border-slate-700 hover:text-slate-200'
                    }`}
                  >
                    <p className="text-xs font-bold text-white">{cap.label}</p>
                    <p className="text-[11px] text-slate-400 mt-1">{cap.desc}</p>
                  </button>
                );
              })}
            </div>
          </div>

        </div>

        {/* RIGHT PREDICTION DISPLAY COLUMN: AI Outputs & Directives (5 cols) */}
        <div className="lg:col-span-5 space-y-8">
          
          {/* Visual Occupancy Gauge */}
          <div className={`transition-all duration-500 ${justCalculated ? 'ring-2 ring-cyan-400 rounded-3xl' : ''}`}>
            <OccupancyGauge 
              prediction={prediction} 
              capacity={formData.train_capacity} 
            />
          </div>

          {/* Real-Time Operational Alert Directive */}
          <AlertBanner 
            alertStatus={prediction?.alert_status}
            fleetAction={prediction?.fleet_action}
            headway={prediction?.recommended_headway_min}
          />

          {/* Feature Matrix Inspector (AI Transparency) */}
          <div className="p-6 rounded-3xl bg-slate-900/80 border border-slate-800 space-y-4 text-xs font-mono shadow-inner">
            <div className="flex items-center justify-between text-slate-400 border-b border-slate-800 pb-3">
              <span className="font-bold uppercase tracking-wider text-xs text-slate-200 flex items-center gap-2">
                <Cpu className="w-4 h-4 text-cyan-400" />
                XGBoost Feature Vector
              </span>
              <span className="text-[11px] text-cyan-400 font-bold">9 ML Features Sent</span>
            </div>

            <div className="grid grid-cols-2 gap-3 text-xs text-slate-300 pt-1">
              <div className="bg-slate-950/60 p-2.5 rounded-xl border border-slate-800/80">
                <span className="text-slate-500 block text-[10px]">Entry_Hour:</span>
                <span className="font-bold text-white">{formData.entry_hour}</span>
              </div>

              <div className="bg-slate-950/60 p-2.5 rounded-xl border border-slate-800/80">
                <span className="text-slate-500 block text-[10px]">Day_of_Week:</span>
                <span className="font-bold text-white">{formData.day_of_week} ({selectedDay?.short})</span>
              </div>

              <div className="bg-slate-950/60 p-2.5 rounded-xl border border-slate-800/80">
                <span className="text-slate-500 block text-[10px]">Is_Peak_Hour:</span>
                <span className={`font-bold ${isPeak ? 'text-red-400' : 'text-emerald-400'}`}>{isPeak ? '1 (Peak)' : '0 (Off-Peak)'}</span>
              </div>

              <div className="bg-slate-950/60 p-2.5 rounded-xl border border-slate-800/80">
                <span className="text-slate-500 block text-[10px]">Hour_Sin / Cos:</span>
                <span className="font-bold text-white">{hourSin} / {hourCos}</span>
              </div>

              <div className="bg-slate-950/60 p-2.5 rounded-xl border border-slate-800/80">
                <span className="text-slate-500 block text-[10px]">From_Station:</span>
                <span className="font-bold text-white">{formData.from_station} ({selectedFromStation?.code})</span>
              </div>

              <div className="bg-slate-950/60 p-2.5 rounded-xl border border-slate-800/80">
                <span className="text-slate-500 block text-[10px]">To_Station:</span>
                <span className="font-bold text-white">{formData.to_station} ({selectedToStation?.code})</span>
              </div>

              <div className="col-span-2 bg-slate-950/60 p-2.5 rounded-xl border border-slate-800/80 flex items-center justify-between">
                <div>
                  <span className="text-slate-500 block text-[10px]">Corridor & Capacity:</span>
                  <span className="font-bold text-white">{selectedLine?.name} • {formData.train_capacity} pax</span>
                </div>
                <span className="text-[10px] text-cyan-400">Native JSON IO</span>
              </div>
            </div>
          </div>

        </div>

      </div>

    </div>
  );
}
