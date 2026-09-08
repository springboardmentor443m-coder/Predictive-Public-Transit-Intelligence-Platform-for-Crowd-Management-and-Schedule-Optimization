import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { api } from '../api/client';
import { Station, StationHistory, ScheduleRecommendation, DelayImpact } from '../types';
import { StatusBadge } from '../components/StatusBadge';
import { MetricCard } from '../components/MetricCard';
import {
  ResponsiveContainer,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  Legend,
} from 'recharts';
import {
  ArrowLeft,
  Calendar,
  Clock,
  Radio,
  Train,
  AlertCircle,
  TrendingUp,
  MapPin,
  Send,
  Zap,
} from 'lucide-react';

export const StationDetailPage: React.FC = () => {
  const { stationCode } = useParams<{ stationCode: string }>();
  const [station, setStation] = useState<Station | null>(null);
  const [history, setHistory] = useState<StationHistory | null>(null);
  const [scheduleRec, setScheduleRec] = useState<ScheduleRecommendation | null>(null);
  const [delayInput, setDelayInput] = useState(5);
  const [delayImpact, setDelayImpact] = useState<DelayImpact | null>(null);
  const [historyDays, setHistoryDays] = useState(7);
  const [loading, setLoading] = useState(true);
  const [reportingDelay, setReportingDelay] = useState(false);

  useEffect(() => {
    if (!stationCode) return;

    const loadStationData = async () => {
      try {
        setLoading(true);
        const [stData, histData, recData] = await Promise.all([
          api.getStation(stationCode),
          api.getStationHistory(stationCode, historyDays),
          api.getScheduleRecommendation(stationCode),
        ]);

        setStation(stData);
        setHistory(histData);
        setScheduleRec(recData);
      } catch (err) {
        console.error('Error loading station detail:', err);
      } finally {
        setLoading(false);
      }
    };

    loadStationData();
  }, [stationCode, historyDays]);

  const handleReportDelay = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!station || !stationCode) return;

    try {
      setReportingDelay(true);
      const result = await api.reportDelay(station.line, stationCode, delayInput);
      setDelayImpact(result);
    } catch (err) {
      alert(`Delay simulation error: ${err}`);
    } finally {
      setReportingDelay(false);
    }
  };

  if (loading || !station) {
    return (
      <div className="p-8 text-center text-slate-400 font-mono">
        <div className="inline-block animate-spin mb-3">
          <Train className="w-8 h-8 text-metro-cyan" />
        </div>
        <p>Retrieving real-time station telemetry and ridership history...</p>
      </div>
    );
  }

  // Format Recharts data
  const chartData = (history?.history || []).map((item) => {
    const dt = new Date(item.timestamp);
    return {
      time: `${dt.getMonth() + 1}/${dt.getDate()} ${String(item.hour).padStart(2, '0')}:00`,
      inflow: item.inflow,
      outflow: item.outflow,
      total: item.total_ridership,
    };
  });

  return (
    <div className="p-6 space-y-6 max-w-7xl mx-auto">
      {/* Top Back Nav & Header Banner */}
      <div>
        <Link
          to="/"
          className="inline-flex items-center gap-2 text-xs font-mono text-slate-400 hover:text-metro-cyan transition-colors mb-3"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Back to Live Network Map</span>
        </Link>

        <div className="bg-bg-surface border border-border-dark rounded-2xl p-6 flex flex-col md:flex-row md:items-center md:justify-between gap-4 shadow-card">
          <div className="space-y-1">
            <div className="flex items-center gap-3">
              <h1 className="text-3xl font-extrabold text-slate-100 font-sans tracking-tight">
                {station.name_en}
              </h1>
              {station.name_kr && (
                <span className="text-xl text-slate-400 font-sans font-medium">
                  {station.name_kr}
                </span>
              )}
              <span className="text-xs font-mono px-2.5 py-1 rounded-md bg-bg-card border border-border-dark text-metro-cyan font-bold">
                {station.line}
              </span>
            </div>
            <div className="flex flex-wrap items-center gap-4 text-xs font-mono text-slate-400 pt-1">
              <span className="flex items-center gap-1.5">
                <MapPin className="w-3.5 h-3.5 text-slate-500" />
                <span>{station.district || 'Seoul Metropolitan'}</span>
              </span>
              <span>&bull;</span>
              <span>Station Code: {station.station_code}</span>
              <span>&bull;</span>
              <span>
                Coordinates: {station.latitude.toFixed(4)}°N, {station.longitude.toFixed(4)}°E
              </span>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <StatusBadge status={scheduleRec?.congestion_label || 'low'} size="lg" />
          </div>
        </div>
      </div>

      {/* Real-time AI Schedule Recommendation Card */}
      {scheduleRec && (
        <div className="bg-gradient-to-r from-bg-surface via-bg-card to-bg-surface border border-metro-cyan/30 rounded-2xl p-6 shadow-glow">
          <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
            <div className="space-y-2 max-w-3xl">
              <div className="flex items-center gap-2">
                <Zap className="w-4 h-4 text-metro-cyan" />
                <h3 className="text-xs font-mono font-bold uppercase tracking-wider text-metro-cyan">
                  AI Headway Dispatch Recommendation
                </h3>
              </div>
              <p className="text-lg font-bold text-slate-100 leading-snug">
                {scheduleRec.recommended_action}
              </p>
              <p className="text-xs font-mono text-slate-300 bg-bg-surface/60 border border-border-dark/60 rounded-lg p-3">
                <span className="text-metro-amber font-semibold">XAI Reasoning: </span>
                {scheduleRec.reason}
              </p>
            </div>

            <div className="bg-bg-surface/80 border border-border-dark rounded-xl p-4 text-center shrink-0 min-w-[180px]">
              <p className="text-xs font-mono text-slate-400 uppercase">Platform Density</p>
              <p className="text-3xl font-extrabold font-mono text-slate-100 mt-1">
                {scheduleRec.current_density.toFixed(1)}%
              </p>
              <p className="text-[11px] text-slate-400 font-mono mt-1 capitalize">
                Urgency: <span className="font-bold text-metro-cyan">{scheduleRec.urgency}</span>
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Historical Ridership Time-Series Chart */}
      <div className="bg-bg-surface border border-border-dark rounded-2xl p-6 shadow-card space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
          <div>
            <h3 className="text-base font-bold text-slate-100">
              Passenger Flow History (Hourly Inflow / Outflow)
            </h3>
            <p className="text-xs font-mono text-slate-400 mt-0.5">
              Empirical and simulated Seoul Metro ridership distributions over the past {historyDays} days
            </p>
          </div>

          {/* Time range selector */}
          <div className="flex items-center gap-1.5 bg-bg-card border border-border-dark p-1 rounded-lg text-xs font-mono">
            {[3, 7, 14].map((d) => (
              <button
                key={d}
                onClick={() => setHistoryDays(d)}
                className={`px-3 py-1 rounded transition-colors ${
                  historyDays === d
                    ? 'bg-metro-cyan text-bg-main font-bold'
                    : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                {d} Days
              </button>
            ))}
          </div>
        </div>

        {/* Recharts Area Container */}
        <div className="h-[340px] w-full pt-2">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={chartData} margin={{ top: 10, right: 10, left: -15, bottom: 0 }}>
              <defs>
                <linearGradient id="inflowGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#00F0FF" stopOpacity={0.4} />
                  <stop offset="95%" stopColor="#00F0FF" stopOpacity={0.0} />
                </linearGradient>
                <linearGradient id="outflowGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#6366F1" stopOpacity={0.4} />
                  <stop offset="95%" stopColor="#6366F1" stopOpacity={0.0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#1F2B44" vertical={false} />
              <XAxis
                dataKey="time"
                stroke="#64748B"
                fontSize={11}
                tickLine={false}
                minTickGap={40}
                fontFamily="JetBrains Mono"
              />
              <YAxis
                stroke="#64748B"
                fontSize={11}
                tickLine={false}
                fontFamily="JetBrains Mono"
              />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#121A2D',
                  borderColor: '#25334D',
                  borderRadius: '10px',
                  color: '#F1F5F9',
                  fontFamily: 'JetBrains Mono',
                  fontSize: '12px',
                }}
              />
              <Legend
                wrapperStyle={{
                  paddingTop: '10px',
                  fontFamily: 'JetBrains Mono',
                  fontSize: '12px',
                }}
              />
              <Area
                type="monotone"
                dataKey="inflow"
                name="Passenger Inflow"
                stroke="#00F0FF"
                strokeWidth={2}
                fillOpacity={1}
                fill="url(#inflowGrad)"
              />
              <Area
                type="monotone"
                dataKey="outflow"
                name="Passenger Outflow"
                stroke="#6366F1"
                strokeWidth={2}
                fillOpacity={1}
                fill="url(#outflowGrad)"
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Downstream Delay Simulation Section */}
      <div className="bg-bg-surface border border-border-dark rounded-2xl p-6 shadow-card space-y-4">
        <div className="flex items-center gap-2">
          <Clock className="w-5 h-5 text-metro-amber" />
          <h3 className="text-base font-bold text-slate-100">
            Downstream Delay Propagation Simulator
          </h3>
        </div>
        <p className="text-xs font-mono text-slate-400">
          Simulate an operational delay incident at {station.name_en} and calculate schedule buffer decay across downstream stations along {station.line}.
        </p>

        <form onSubmit={handleReportDelay} className="flex flex-wrap items-center gap-4 pt-2">
          <div className="flex items-center gap-2">
            <label className="text-xs font-mono text-slate-300">Delay Duration (mins):</label>
            <input
              type="number"
              min={1}
              max={60}
              value={delayInput}
              onChange={(e) => setDelayInput(Number(e.target.value))}
              className="w-24 px-3 py-1.5 bg-bg-card border border-border-dark rounded-lg text-sm font-mono text-slate-100 focus:outline-none focus:border-metro-cyan"
            />
          </div>

          <button
            type="submit"
            disabled={reportingDelay}
            className="flex items-center gap-2 px-4 py-2 rounded-lg bg-metro-amber text-bg-main font-mono text-xs font-bold hover:bg-amber-400 transition-colors disabled:opacity-50"
          >
            <Send className="w-3.5 h-3.5" />
            <span>{reportingDelay ? 'Computing...' : 'Simulate Delay Propagation'}</span>
          </button>
        </form>

        {/* Delay Propagation Results */}
        {delayImpact && (
          <div className="mt-4 pt-4 border-t border-border-dark/60 space-y-3">
            <h4 className="text-xs font-mono font-semibold uppercase text-slate-300">
              Downstream Schedule Impact ({delayImpact.initial_delay_minutes} min initial incident):
            </h4>
            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-3">
              {delayImpact.affected_stations.map((aff) => (
                <div
                  key={aff.station_code}
                  className="bg-bg-card border border-border-dark rounded-xl p-3 text-xs font-mono space-y-1"
                >
                  <div className="flex justify-between items-center text-slate-400">
                    <span>Hop +{aff.station_order}</span>
                    <span className="text-[10px] px-1.5 py-0.5 rounded bg-bg-surface text-slate-300">
                      {aff.station_code}
                    </span>
                  </div>
                  <p className="font-bold text-slate-100 text-sm truncate">{aff.name_en}</p>
                  <p className="text-metro-amber font-semibold">
                    +{aff.estimated_delay_minutes} min ({aff.estimated_eta_delay_seconds}s)
                  </p>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
