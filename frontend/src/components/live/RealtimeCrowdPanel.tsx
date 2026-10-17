import React, { useState, useEffect, useCallback, useRef } from 'react';
import { mlService, RealtimeCrowdPredictionResponse, RealtimeStationPrediction } from '../../services/mlService';
import { Card } from '../common/Card';
import { Badge } from '../common/Badge';
import {
  Brain, AlertTriangle, TrendingUp, Activity,
  Clock, Zap, RefreshCw, Users, Train, ChevronDown, ChevronUp
} from 'lucide-react';
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer,
  Cell, CartesianGrid
} from 'recharts';

const RISK_CONFIG = {
  CRITICAL: { color: '#ef4444', bg: 'bg-red-50', border: 'border-red-200', text: 'text-red-700', badge: 'rose' as const, icon: '🔴' },
  HIGH:     { color: '#f97316', bg: 'bg-orange-50', border: 'border-orange-200', text: 'text-orange-700', badge: 'amber' as const, icon: '🟠' },
  MODERATE: { color: '#eab308', bg: 'bg-yellow-50', border: 'border-yellow-200', text: 'text-yellow-700', badge: 'amber' as const, icon: '🟡' },
  LOW:      { color: '#22c55e', bg: 'bg-green-50', border: 'border-green-200', text: 'text-green-700', badge: 'emerald' as const, icon: '🟢' },
};

function getRiskConfig(risk: string) {
  return RISK_CONFIG[risk as keyof typeof RISK_CONFIG] || RISK_CONFIG.LOW;
}

function ConfidenceBar({ value }: { value: number }) {
  const pct = Math.round(value * 100);
  const color = pct >= 90 ? '#22c55e' : pct >= 75 ? '#eab308' : '#f97316';
  return (
    <div className="flex items-center gap-2">
      <div className="flex-1 h-1.5 bg-[#E8E4D8] rounded-full overflow-hidden">
        <div className="h-full rounded-full transition-all" style={{ width: `${pct}%`, backgroundColor: color }} />
      </div>
      <span className="text-[10px] font-bold text-[#29322F]" style={{ color }}>{pct}%</span>
    </div>
  );
}

interface StationCardProps {
  station: RealtimeStationPrediction;
}

function StationCard({ station }: StationCardProps) {
  const [expanded, setExpanded] = useState(false);
  const cfg = getRiskConfig(station.crowd_risk);

  return (
    <div className={`rounded-xl border p-4 transition-all ${cfg.bg} ${cfg.border}`}>
      <div className="flex items-start justify-between gap-3">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap mb-1.5">
            <span className="text-base">{cfg.icon}</span>
            <span className="text-sm font-bold text-[#29322F] truncate">{station.station_complex}</span>
            {station.is_live_model && (
              <span className="flex items-center gap-1 px-1.5 py-0.5 rounded text-[9px] font-bold bg-[#2F6F68]/10 text-[#2F6F68] border border-[#2F6F68]/20">
                <Brain className="w-2.5 h-2.5" /> LIVE MODEL
              </span>
            )}
          </div>

          {/* Route pills */}
          <div className="flex gap-1 flex-wrap mb-2">
            {station.routes.slice(0, 6).map(r => (
              <span key={r} className="px-1.5 py-0.5 rounded-full text-[9px] font-bold text-white bg-[#2F6F68]">{r}</span>
            ))}
          </div>

          {/* Confidence bar */}
          <div className="mb-2">
            <div className="text-[9px] font-semibold text-[#6F8F87] uppercase mb-1">Model Confidence</div>
            <ConfidenceBar value={station.confidence} />
          </div>
        </div>

        <div className="text-right shrink-0">
          <div className={`text-lg font-black ${cfg.text}`}>{station.crowd_risk}</div>
          <div className="text-[11px] text-[#6F8F87] mt-0.5">
            {Math.round(station.predicted_next_hour).toLocaleString()} pax/hr
          </div>
          {station.avg_live_delay_seconds > 0 && (
            <div className="text-[10px] text-orange-600 font-semibold mt-0.5">
              +{Math.round(station.avg_live_delay_seconds)}s delay
            </div>
          )}
        </div>
      </div>

      {/* Delay escalation note */}
      {station.delay_escalation_note && (
        <div className="mt-2 p-2 rounded-lg bg-orange-100 border border-orange-200 text-[10px] text-orange-700 font-medium flex items-start gap-1.5">
          <AlertTriangle className="w-3 h-3 shrink-0 mt-0.5" />
          <span>{station.delay_escalation_note}</span>
        </div>
      )}

      {/* Expand toggle */}
      <button
        onClick={() => setExpanded(e => !e)}
        className="mt-2 flex items-center gap-1 text-[10px] text-[#2F6F68] font-semibold hover:underline"
      >
        {expanded ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
        {expanded ? 'Hide' : 'Show'} recommendation
      </button>

      {expanded && (
        <div className="mt-2 p-2.5 rounded-lg bg-white border border-[#DDD9CF] text-[11px] text-[#29322F] leading-relaxed">
          {station.recommended_action}
        </div>
      )}
    </div>
  );
}

export const RealtimeCrowdPanel: React.FC = () => {
  const [data, setData] = useState<RealtimeCrowdPredictionResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastRefresh, setLastRefresh] = useState<Date>(new Date());
  const [lastSuccess, setLastSuccess] = useState<Date | null>(null);
  const [riskFilter, setRiskFilter] = useState<string>('ALL');

  const isInitialLoad = useRef(true);

  const fetchPredictions = useCallback(async () => {
    const firstLoad = isInitialLoad.current;
    // Always mark as no longer initial before the async work
    if (firstLoad) isInitialLoad.current = false;

    // Only show the blocking spinner on the very first call
    if (firstLoad) setLoading(true);
    setError(null);

    try {
      const result = await mlService.getRealtimeCrowdPrediction();
      setData(result);
      setLastRefresh(new Date());
      setLastSuccess(new Date());
    } catch (e: any) {
      setError(e?.response?.data?.detail || 'Failed to fetch crowd predictions. Showing last known data.');
    } finally {
      // Always clear spinner after the first load regardless of success/error
      if (firstLoad) setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchPredictions();
    const interval = setInterval(fetchPredictions, 30_000); // refresh every 30s for real-time
    return () => clearInterval(interval);
  }, [fetchPredictions]);

  const filtered = data?.predictions.filter(p =>
    riskFilter === 'ALL' || p.crowd_risk === riskFilter
  ) ?? [];

  // Bar chart data — risk distribution
  const barData = data
    ? ['LOW', 'MODERATE', 'HIGH', 'CRITICAL'].map(r => ({
        risk: r,
        count: data.risk_summary[r] || 0,
        color: getRiskConfig(r).color,
      }))
    : [];

  const isDataStale = lastSuccess
    ? (Date.now() - lastSuccess.getTime()) > 2 * 60 * 1000
    : false;

  return (
    <div className="space-y-5">
      {/* Fix 5: Visible error / stale-data warning banner */}
      {error && (
        <div className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-amber-50 border border-amber-200 text-amber-700 text-xs font-sans">
          <AlertTriangle className="w-3.5 h-3.5 shrink-0" />
          <span>{error}</span>
          <button onClick={fetchPredictions} className="ml-auto underline font-semibold hover:no-underline">
            Retry
          </button>
        </div>
      )}
      {!error && isDataStale && (
        <div className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-amber-50 border border-amber-200 text-amber-700 text-xs font-sans">
          <AlertTriangle className="w-3.5 h-3.5 shrink-0" />
          <span>Crowd predictions are stale — last successful update was over 2 minutes ago.</span>
        </div>
      )}
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-3">
        <div>
          <div className="flex items-center gap-2">
            <Brain className="w-5 h-5 text-[#2F6F68]" />
            <h2 className="text-sm font-bold text-[#29322F] uppercase tracking-wide">
              Real-Time Crowd Prediction Engine
            </h2>
            {data?.is_live_model && (
              <Badge variant="cyan" size="sm">LIVE RF MODEL</Badge>
            )}
            {data?.is_peak_hour && (
              <Badge variant="rose" size="sm">PEAK HOUR</Badge>
            )}
          </div>
          <p className="text-xs text-[#6F8F87] mt-1 font-sans">
            RandomForest predictions trained on MTA ridership · augmented with live GTFS-RT delays
            {data && <span> · Updated {lastRefresh.toLocaleTimeString()}</span>}
          </p>
        </div>
        <button
          onClick={fetchPredictions}
          disabled={loading}
          aria-label="Refresh crowd predictions"
          className="flex items-center gap-2 px-3 py-1.5 rounded-lg border border-[#DDD9CF] bg-white text-[#2F6F68] text-xs font-semibold hover:border-[#2F6F68] transition-colors disabled:opacity-50"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
          {loading ? 'Predicting...' : 'Refresh'}
        </button>
      </div>


      {data && (
        <>
          {/* KPI row */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            <Card className="flex items-center gap-3 border-[#DDD9CF] shadow-sm bg-white">
              <div className="p-2.5 rounded-xl bg-[#2F6F68]/10 border border-[#2F6F68]/20">
                <Users className="w-5 h-5 text-[#2F6F68]" />
              </div>
              <div>
                <div className="text-[10px] text-[#6F8F87] uppercase font-semibold">Predicted Demand</div>
                <div className="text-lg font-black text-[#29322F]">
                  {Math.round(data.total_predicted_demand_next_hour).toLocaleString()}
                </div>
                <div className="text-[9px] text-[#6F8F87]">passengers next hour</div>
              </div>
            </Card>

            <Card className="flex items-center gap-3 border-[#DDD9CF] shadow-sm bg-white">
              <div className="p-2.5 rounded-xl bg-red-100 border border-red-200">
                <AlertTriangle className="w-5 h-5 text-red-600" />
              </div>
              <div>
                <div className="text-[10px] text-[#6F8F87] uppercase font-semibold">High-Risk Stations</div>
                <div className="text-lg font-black text-red-600">{data.high_risk_count}</div>
                <div className="text-[9px] text-[#6F8F87]">require attention</div>
              </div>
            </Card>

            <Card className="flex items-center gap-3 border-[#DDD9CF] shadow-sm bg-white">
              <div className="p-2.5 rounded-xl bg-blue-100 border border-blue-200">
                <Train className="w-5 h-5 text-blue-600" />
              </div>
              <div>
                <div className="text-[10px] text-[#6F8F87] uppercase font-semibold">Active Delay Routes</div>
                <div className="text-lg font-black text-blue-600">{data.active_delay_routes}</div>
                <div className="text-[9px] text-[#6F8F87]">lines with live delays</div>
              </div>
            </Card>

            <Card className="flex items-center gap-3 border-[#DDD9CF] shadow-sm bg-white">
              <div className="p-2.5 rounded-xl bg-purple-100 border border-purple-200">
                <Activity className="w-5 h-5 text-purple-600" />
              </div>
              <div>
                <div className="text-[10px] text-[#6F8F87] uppercase font-semibold">Model Coverage</div>
                <div className="text-lg font-black text-purple-600">{data.live_model_stations}/{data.stations_predicted}</div>
                <div className="text-[9px] text-[#6F8F87]">live RF predictions</div>
              </div>
            </Card>
          </div>

          {/* Risk distribution chart */}
          <Card className="border-[#DDD9CF] shadow-sm bg-white">
            <div className="flex items-center gap-2 mb-4">
              <TrendingUp className="w-4 h-4 text-[#2F6F68]" />
              <h3 className="text-xs font-bold text-[#29322F] uppercase tracking-wide">Risk Distribution Across Stations</h3>
              <div className="ml-auto flex items-center gap-1.5 text-[10px] text-[#6F8F87]">
                <Clock className="w-3 h-3" />
                <span>Hour {data.system_hour}:00 · {data.is_peak_hour ? 'PEAK' : 'OFF-PEAK'}</span>
              </div>
            </div>
            <ResponsiveContainer width="100%" height={120}>
              <BarChart data={barData} margin={{ top: 0, right: 0, left: -20, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#E8E4D8" />
                <XAxis dataKey="risk" tick={{ fontSize: 10, fill: '#6F8F87', fontWeight: 600 }} />
                <YAxis tick={{ fontSize: 10, fill: '#6F8F87' }} />
                <Tooltip
                  contentStyle={{ fontSize: 11, borderRadius: 8, border: '1px solid #DDD9CF', background: '#fff' }}
                  formatter={(val: any) => [val, 'Stations']}
                />
                <Bar dataKey="count" radius={[4, 4, 0, 0]}>
                  {barData.map((entry, i) => (
                    <Cell key={i} fill={entry.color} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </Card>

          {/* Station predictions grid */}
          <Card className="border-[#DDD9CF] shadow-sm bg-white">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2">
                <Zap className="w-4 h-4 text-[#2F6F68]" />
                <h3 className="text-xs font-bold text-[#29322F] uppercase tracking-wide">Station-Level Predictions</h3>
                <Badge variant={data.is_live_model ? 'cyan' : 'amber'} size="sm">
                  {data.data_state}
                </Badge>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-[10px] text-[#6F8F87]">Filter:</span>
                {['ALL', 'CRITICAL', 'HIGH', 'MODERATE', 'LOW'].map(r => (
                  <button
                    key={r}
                    onClick={() => setRiskFilter(r)}
                    className={`px-2 py-0.5 rounded text-[10px] font-bold transition-all ${
                      riskFilter === r
                        ? 'bg-[#2F6F68] text-white'
                        : 'bg-[#F7F5EF] text-[#6F8F87] border border-[#DDD9CF] hover:border-[#2F6F68]'
                    }`}
                  >
                    {r}
                  </button>
                ))}
              </div>
            </div>

            {loading && !data ? (
              <div className="py-12 text-center text-[#6F8F87] text-xs">
                <Brain className="w-8 h-8 mx-auto mb-2 opacity-40 animate-pulse" />
                <p>Running RandomForest predictions…</p>
              </div>
            ) : filtered.length === 0 ? (
              <div className="py-8 text-center text-[#6F8F87] text-xs">
                No stations match the selected risk filter.
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-3">
                {filtered.map(station => (
                  <StationCard key={station.station_complex_id} station={station} />
                ))}
              </div>
            )}
          </Card>

          <div className="text-[10px] text-[#6F8F87] text-center font-sans">
            Predictions refresh every 60 seconds · Model: RandomForest trained on MTA turnstile data ·
            Delay escalation from live GTFS-RT · {data.prediction_time}
          </div>
        </>
      )}

      {loading && !data && (
        <Card className="border-[#DDD9CF] shadow-sm bg-white py-12 text-center">
          <Brain className="w-10 h-10 mx-auto mb-3 text-[#2F6F68] opacity-60 animate-pulse" />
          <p className="text-[#6F8F87] text-sm font-semibold">Loading ML crowd predictions…</p>
          <p className="text-[#6F8F87] text-xs mt-1">Running RandomForest model with live GTFS-RT data</p>
        </Card>
      )}
    </div>
  );
};
