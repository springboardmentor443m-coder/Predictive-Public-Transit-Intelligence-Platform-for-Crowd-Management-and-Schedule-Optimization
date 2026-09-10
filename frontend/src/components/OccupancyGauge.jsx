import React from 'react';
import { Gauge, AlertTriangle, CheckCircle, Clock, Users, ShieldAlert } from 'lucide-react';

export default function OccupancyGauge({ prediction, capacity = 2400 }) {
  const pax = prediction?.predicted_occupancy_int || prediction?.predicted_occupancy || 0;
  const maxCap = prediction?.train_capacity || capacity || 2400;
  const pct = Math.min(100, Math.max(0, Math.round((pax / maxCap) * 100)));

  // Determine tier & theme
  let tierInfo = {
    label: "OFF-PEAK",
    color: "emerald",
    bgBadge: "bg-emerald-500/20 text-emerald-300 border-emerald-500/30",
    strokeColor: "#10b981",
    glowColor: "rgba(16, 185, 129, 0.4)",
    icon: CheckCircle,
    desc: "Plentiful seating available. Low platform crowding."
  };

  if (pax >= 1500) {
    tierInfo = {
      label: "SEVERE RUSH HOUR",
      color: "red",
      bgBadge: "bg-red-500/20 text-red-300 border-red-500/30",
      strokeColor: "#ef4444",
      glowColor: "rgba(239, 68, 68, 0.6)",
      icon: ShieldAlert,
      desc: "Critical overcrowding. Platform danger threshold reached!"
    };
  } else if (pax >= 800) {
    tierInfo = {
      label: "MODERATE TRAFFIC",
      color: "yellow",
      bgBadge: "bg-amber-500/20 text-amber-300 border-amber-500/30",
      strokeColor: "#eab308",
      glowColor: "rgba(234, 179, 8, 0.5)",
      icon: AlertTriangle,
      desc: "Standard standing capacity. Normal commute volume."
    };
  }

  const TierIcon = tierInfo.icon;
  const strokeDashoffset = 251.2 - (251.2 * pct) / 100;

  return (
    <div className="flex flex-col items-center justify-center p-6 rounded-2xl bg-slate-900/80 border border-slate-800 shadow-inner relative overflow-hidden">
      {/* Background glow radial */}
      <div 
        className="absolute w-44 h-44 rounded-full blur-3xl opacity-20 pointer-events-none"
        style={{ backgroundColor: tierInfo.strokeColor }}
      ></div>

      {/* Header Tier Pill */}
      <div className="flex items-center justify-between w-full mb-3">
        <div className="flex items-center space-x-2">
          <Gauge className="w-4 h-4 text-cyan-400" />
          <span className="text-xs font-bold text-slate-300 tracking-wider uppercase font-mono">
            AI Occupancy Meter
          </span>
        </div>
        <span className={`px-2.5 py-1 text-xs font-bold uppercase rounded-lg border flex items-center gap-1.5 ${tierInfo.bgBadge}`}>
          <TierIcon className="w-3.5 h-3.5" />
          {tierInfo.label}
        </span>
      </div>

      {/* SVG Radial Gauge Meter */}
      <div className="relative flex items-center justify-center my-3">
        <svg className="w-48 h-48 transform -rotate-90">
          {/* Background circle track */}
          <circle
            cx="96"
            cy="96"
            r="80"
            stroke="currentColor"
            strokeWidth="14"
            className="text-slate-800/80"
            fill="transparent"
          />
          {/* Critical Threshold Benchmark Indicator Marker */}
          <circle
            cx="96"
            cy="96"
            r="80"
            stroke="#ef4444"
            strokeWidth="14"
            strokeDasharray="4 247"
            strokeDashoffset={251.2 - (251.2 * (1500 / maxCap))}
            className="opacity-80"
            fill="transparent"
          />
          {/* Active progress arc */}
          <circle
            cx="96"
            cy="96"
            r="80"
            stroke={tierInfo.strokeColor}
            strokeWidth="14"
            strokeDasharray="502.6"
            strokeDashoffset={502.6 - (502.6 * (pct / 100) * 0.75)}
            strokeLinecap="round"
            fill="transparent"
            style={{
              filter: `drop-shadow(0 0 8px ${tierInfo.glowColor})`,
              transition: 'stroke-dashoffset 0.8s ease-in-out, stroke 0.5s ease'
            }}
          />
        </svg>

        {/* Center Display Value */}
        <div className="absolute inset-0 flex flex-col items-center justify-center text-center">
          <div className="flex items-baseline justify-center">
            <span className="text-4xl font-black text-white font-display tracking-tight">
              {pax}
            </span>
          </div>
          <span className="text-[11px] font-mono text-slate-400 uppercase tracking-widest mt-0.5">
            Passengers
          </span>
          <span className={`text-xs font-bold font-mono mt-1 ${
            pct >= 75 ? 'text-red-400' : (pct >= 40 ? 'text-amber-400' : 'text-emerald-400')
          }`}>
            {pct}% Capacity
          </span>
        </div>
      </div>

      {/* Gauge Capacity Legend */}
      <div className="grid grid-cols-3 w-full text-center gap-2 pt-3 border-t border-slate-800 text-xs">
        <div className="bg-slate-800/40 p-2 rounded-xl border border-slate-700/40">
          <p className="text-[10px] text-slate-400 font-mono">TRAIN CAP</p>
          <p className="font-bold text-white font-mono mt-0.5">{maxCap}</p>
        </div>
        <div className="bg-slate-800/40 p-2 rounded-xl border border-slate-700/40">
          <p className="text-[10px] text-slate-400 font-mono">HEADWAY</p>
          <p className={`font-bold font-mono mt-0.5 ${
            tierInfo.label === 'SEVERE RUSH HOUR' ? 'text-red-400' : (tierInfo.label === 'MODERATE TRAFFIC' ? 'text-amber-400' : 'text-emerald-400')
          }`}>
            {prediction?.recommended_headway_min ? `${prediction.recommended_headway_min} Min` : '3 Min'}
          </p>
        </div>
        <div className="bg-slate-800/40 p-2 rounded-xl border border-slate-700/40">
          <p className="text-[10px] text-slate-400 font-mono">PEAK FLAG</p>
          <p className="font-bold text-cyan-400 font-mono mt-0.5">
            {prediction?.is_peak_hour ? 'YES (1)' : 'NO (0)'}
          </p>
        </div>
      </div>

      <p className="text-xs text-slate-400 text-center mt-3 italic">
        {tierInfo.desc}
      </p>
    </div>
  );
}
