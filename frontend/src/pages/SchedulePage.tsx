import React, { useState, useEffect } from 'react';
import { api } from '../api/client';
import { Station, ScheduleRecommendation, DelayImpact } from '../types';
import { MetricCard } from '../components/MetricCard';
import { StatusBadge } from '../components/StatusBadge';
import {
  Calendar,
  Clock,
  Train,
  CheckCircle2,
  AlertTriangle,
  ArrowRight,
  TrendingUp,
  Zap,
} from 'lucide-react';
import { Link } from 'react-router-dom';

interface LineScheduleInfo {
  line: string;
  representativeStation: Station;
  currentHeadwayMinutes: number;
  recommendedHeadwayMinutes: number;
  currentFrequency: number;
  recommendedFrequency: number;
  recommendation: ScheduleRecommendation;
}

export const SchedulePage: React.FC = () => {
  const [lineSchedules, setLineSchedules] = useState<LineScheduleInfo[]>([]);
  const [loading, setLoading] = useState(true);

  const loadSchedules = async () => {
    try {
      setLoading(true);
      const stations = await api.getStations();

      // Get representative hubs for each line
      const lines = Array.from(new Set(stations.map((s) => s.line))).sort();
      const schedules: LineScheduleInfo[] = [];

      for (const line of lines) {
        const lineStations = stations.filter((s) => s.line === line);
        // Pick prominent hub or first station
        const rep =
          lineStations.find((s) => ['222', '150', '318', '411', '514', '916'].includes(s.station_code)) ||
          lineStations[0];

        try {
          const rec = await api.getScheduleRecommendation(rep.station_code);
          const currentFreq = 12; // 12 trains/hour base
          let recFreq = currentFreq;
          let currentHeadway = 5.0;
          let recHeadway = 5.0;

          if (rec.congestion_label === 'critical') {
            recFreq = currentFreq + 4;
            recHeadway = 3.5;
          } else if (rec.congestion_label === 'high') {
            recFreq = currentFreq + 2;
            recHeadway = 4.0;
          } else if (rec.congestion_label === 'medium') {
            recFreq = currentFreq;
            recHeadway = 5.0;
          } else {
            recFreq = currentFreq - 2;
            recHeadway = 6.0;
          }

          schedules.push({
            line,
            representativeStation: rep,
            currentHeadwayMinutes: currentHeadway,
            recommendedHeadwayMinutes: recHeadway,
            currentFrequency: currentFreq,
            recommendedFrequency: recFreq,
            recommendation: rec,
          });
        } catch (e) {
          console.error(`Failed rec for ${rep.name_en}:`, e);
        }
      }

      setLineSchedules(schedules);
    } catch (err) {
      console.error('Failed to load line schedules:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadSchedules();
  }, []);

  return (
    <div className="p-6 space-y-6 max-w-7xl mx-auto">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-extrabold text-slate-100 tracking-tight font-sans">
            AI Train Scheduling & Dispatch Optimization
          </h1>
          <p className="text-xs text-slate-400 font-mono mt-1">
            Real-time headway comparison and automated train frequency recommendations per Seoul Metro Line
          </p>
        </div>

        <button
          onClick={loadSchedules}
          className="px-3.5 py-2 rounded-lg bg-bg-card hover:bg-slate-800 text-metro-cyan border border-border-dark font-mono text-xs font-semibold transition-colors"
        >
          Recalculate Headways
        </button>
      </div>

      {/* High-level KPIs */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <MetricCard
          title="Monitored Lines"
          value={lineSchedules.length || 9}
          subtitle="Seoul Metro Network"
          icon={Train}
          accentColor="cyan"
        />
        <MetricCard
          title="Frequency Boost Active"
          value={lineSchedules.filter((l) => l.recommendedFrequency > l.currentFrequency).length}
          subtitle="Lines requiring headway compression"
          icon={Zap}
          accentColor="amber"
        />
        <MetricCard
          title="Normal Schedule Lines"
          value={lineSchedules.filter((l) => l.recommendedFrequency <= l.currentFrequency).length}
          subtitle="Operating on standard off-peak timetable"
          icon={CheckCircle2}
          accentColor="emerald"
        />
      </div>

      {/* Lines Scheduling Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {lineSchedules.map((item) => {
          const freqDelta = item.recommendedFrequency - item.currentFrequency;

          return (
            <div
              key={item.line}
              className="bg-bg-surface border border-border-dark rounded-2xl p-5 shadow-card hover:border-border-glow transition-all space-y-4"
            >
              {/* Card Header */}
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="px-3 py-1.5 rounded-lg bg-bg-card border border-border-dark font-mono font-bold text-sm text-metro-cyan">
                    {item.line}
                  </div>
                  <div>
                    <h3 className="font-bold text-slate-100 text-sm">
                      {item.representativeStation.name_en}
                    </h3>
                    <p className="text-[11px] text-slate-400 font-mono">Representative Hub</p>
                  </div>
                </div>

                <StatusBadge status={item.recommendation.congestion_label} size="sm" />
              </div>

              {/* Headway & Frequency Comparison Box */}
              <div className="grid grid-cols-2 gap-3 bg-bg-card/70 border border-border-dark/60 rounded-xl p-3.5 font-mono text-xs">
                {/* Current */}
                <div className="space-y-1">
                  <span className="text-[10px] uppercase text-slate-400">Current Schedule</span>
                  <p className="text-base font-bold text-slate-200">
                    {item.currentFrequency} trains/hr
                  </p>
                  <p className="text-[11px] text-slate-400">
                    Headway: <span className="text-slate-200">{item.currentHeadwayMinutes}m</span>
                  </p>
                </div>

                {/* Recommended */}
                <div className="space-y-1 border-l border-border-dark pl-3">
                  <span className="text-[10px] uppercase text-slate-400">AI Recommended</span>
                  <p
                    className={`text-base font-bold ${
                      freqDelta > 0
                        ? 'text-metro-amber'
                        : freqDelta < 0
                        ? 'text-slate-300'
                        : 'text-emerald-400'
                    }`}
                  >
                    {item.recommendedFrequency} trains/hr
                  </p>
                  <p className="text-[11px] text-slate-400">
                    Headway:{' '}
                    <span
                      className={`font-semibold ${
                        freqDelta > 0 ? 'text-metro-amber' : 'text-slate-200'
                      }`}
                    >
                      {item.recommendedHeadwayMinutes}m
                    </span>
                  </p>
                </div>
              </div>

              {/* Explainable AI Action & Reason */}
              <div className="space-y-1.5 text-xs font-mono">
                <div className="flex items-start gap-2 text-slate-300">
                  <span className="text-metro-cyan font-bold">&bull;</span>
                  <span>{item.recommendation.recommended_action}</span>
                </div>
                <p className="text-[11px] text-slate-400 bg-bg-surface/50 border border-border-dark/40 rounded p-2">
                  <span className="text-slate-300 font-semibold">Reason: </span>
                  {item.recommendation.reason}
                </p>
              </div>

              {/* Action Link */}
              <div className="pt-2 border-t border-border-subtle flex justify-end">
                <Link
                  to={`/stations/${item.representativeStation.station_code}`}
                  className="inline-flex items-center gap-1.5 text-xs font-mono font-semibold text-metro-cyan hover:underline"
                >
                  <span>Inspect Station Telemetry</span>
                  <ArrowRight className="w-3.5 h-3.5" />
                </Link>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
