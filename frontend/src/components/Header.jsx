import React, { useState, useEffect } from 'react';
import { Activity, ShieldCheck, Clock, ExternalLink, RefreshCw, Zap } from 'lucide-react';

export default function Header({ apiHealth, onRefresh, isRefreshing, activeModuleTitle }) {
  const [currentTime, setCurrentTime] = useState(new Date());

  useEffect(() => {
    const timer = setInterval(() => setCurrentTime(new Date()), 1000);
    return () => clearInterval(timer);
  }, []);

  const formattedTime = currentTime.toLocaleTimeString('en-US', {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: false,
  });

  const formattedDate = currentTime.toLocaleDateString('en-US', {
    weekday: 'short',
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  });

  const isHealthy = apiHealth?.status === 'healthy';

  return (
    <header className="h-16 border-b border-slate-800 bg-[#111827] px-6 flex items-center justify-between sticky top-0 z-30 shadow-md">
      {/* Left: Module Title & Breadcrumb */}
      <div className="flex items-center gap-3">
        <div className="flex items-center gap-2">
          <span className="text-xs font-mono font-bold px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
            SYSTEM ACTIVE
          </span>
          <span className="text-slate-500 text-sm">/</span>
          <h1 className="text-base font-semibold text-slate-100 tracking-wide">
            {activeModuleTitle || 'Operations Console'}
          </h1>
        </div>
      </div>

      {/* Right: Telemetry & Controls */}
      <div className="flex items-center gap-4 text-xs">
        {/* Backend Status */}
        <div className="hidden sm:flex items-center gap-2 px-3 py-1.5 rounded-md bg-slate-900 border border-slate-800">
          <Activity
            size={14}
            className={isHealthy ? 'text-emerald-400 animate-pulse' : 'text-rose-400'}
          />
          <span className="text-slate-400">FastAPI Backend:</span>
          <span className={`font-mono font-semibold ${isHealthy ? 'text-emerald-400' : 'text-rose-400'}`}>
            {isHealthy ? 'ONLINE (Port 8000)' : 'CONNECTING...'}
          </span>
        </div>

        {/* Model Status */}
        <div className="hidden md:flex items-center gap-2 px-3 py-1.5 rounded-md bg-slate-900 border border-slate-800">
          <ShieldCheck size={14} className="text-[#00D4AA]" />
          <span className="text-slate-400">Champion Model:</span>
          <span className="font-mono font-semibold text-slate-200">
            {apiHealth?.model_name || 'Random Forest'}
          </span>
        </div>

        {/* Clock */}
        <div className="flex items-center gap-2 px-3 py-1.5 rounded-md bg-slate-900 border border-slate-800">
          <Clock size={14} className="text-sky-400" />
          <span className="font-mono text-slate-200 font-medium">
            {formattedTime}
          </span>
          <span className="hidden lg:inline text-slate-500">({formattedDate})</span>
        </div>

        {/* Refresh Button */}
        {onRefresh && (
          <button
            onClick={onRefresh}
            disabled={isRefreshing}
            className="p-1.5 rounded-md bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white transition border border-slate-700 disabled:opacity-50"
            title="Refresh active telemetry"
          >
            <RefreshCw size={14} className={isRefreshing ? 'animate-spin text-[#00D4AA]' : ''} />
          </button>
        )}

        {/* API Docs Link */}
        <a
          href="http://127.0.0.1:8000/docs"
          target="_blank"
          rel="noopener noreferrer"
          className="hidden xl:inline-flex items-center gap-1.5 px-2.5 py-1.5 rounded-md bg-slate-800/80 hover:bg-slate-700 text-slate-300 hover:text-white border border-slate-700 transition"
        >
          <ExternalLink size={12} />
          <span>Swagger Docs</span>
        </a>
      </div>
    </header>
  );
}
