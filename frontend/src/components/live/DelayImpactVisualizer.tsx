import React from 'react';
import { Card } from '../common/Card';
import { Badge } from '../common/Badge';
import { DelayImpactRecord } from '../../services/mlService';
import { Clock } from 'lucide-react';

interface DelayImpactVisualizerProps {
  delays: DelayImpactRecord[];
}

export const DelayImpactVisualizer: React.FC<DelayImpactVisualizerProps> = ({ delays }) => {
  const getSeverityBadge = (tier: string) => {
    switch (tier?.toUpperCase()) {
      case 'CRITICAL_DELAY':
        return <Badge variant="rose">CRITICAL DELAY</Badge>;
      case 'MODERATE_DELAY':
        return <Badge variant="amber">MODERATE DELAY</Badge>;
      default:
        return <Badge variant="emerald">ON TIME</Badge>;
    }
  };

  const getStateBadge = (state: string) => {
    if (!state || state === 'UNAVAILABLE') return <Badge variant="slate">UNAVAILABLE</Badge>;
    if (state === 'STALE') return <Badge variant="amber">STALE</Badge>;
    if (state === 'LIVE (NO DELAY)') return <Badge variant="emerald">NO DELAY</Badge>;
    if (state.startsWith('LIVE')) return <Badge variant="cyan">LIVE</Badge>;
    return <Badge variant="slate">{state}</Badge>;
  };

  // Overall feed state from first record
  const overallState = delays.length > 0 ? delays[0].data_state : 'UNAVAILABLE';
  const isFeedLive = overallState !== 'UNAVAILABLE' && overallState !== 'STALE';

  // Show routes with actual delay data first, then routes with stop data
  const routesWithDelay = delays.filter(d => d.delay_seconds > 0);
  const routesNoDelay = delays.filter(d => d.delay_seconds === 0 && d.affected_stations_count > 0);
  const displayDelays = [...routesWithDelay, ...routesNoDelay].slice(0, 12);

  return (
    <Card className="space-y-4 border-[#DDD9CF] shadow-sm bg-white">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-2 pb-3 border-b border-[#DDD9CF]">
        <div className="flex items-center gap-2">
          <Clock className="w-5 h-5 text-[#2F6F68]" />
          <h3 className="text-sm font-bold font-sans text-[#29322F] tracking-wide">
            Line-Level Delay Impact & Route Disruption Analysis
          </h3>
        </div>
        <div className="flex items-center gap-2 font-sans text-[11px]">
          {isFeedLive
            ? <Badge variant="cyan">LIVE: MTA GTFS-RT</Badge>
            : <Badge variant="slate">{overallState}</Badge>
          }
        </div>
      </div>

      {!isFeedLive ? (
        <div className="py-8 text-center text-[#6F8F87] text-xs">
          <Clock className="w-8 h-8 mx-auto mb-2 opacity-40" />
          <p className="font-semibold">GTFS-RT delay feed is {overallState.toLowerCase()}</p>
          <p className="mt-1 opacity-70">Live delay data will appear here once the MTA feed reconnects.</p>
        </div>
      ) : displayDelays.length === 0 ? (
        <div className="py-8 text-center text-[#6F8F87] text-xs">
          <Clock className="w-8 h-8 mx-auto mb-2 opacity-40" />
          <p className="font-semibold">No active delays detected on monitored routes</p>
          <p className="mt-1 opacity-70">All lines reporting on-time status from live GTFS-RT feed.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-3 font-sans text-xs">
          {displayDelays.map((item, idx) => (
            <div
              key={idx}
              className="p-3 rounded-xl bg-[#F7F5EF] border border-[#DDD9CF] flex flex-col justify-between space-y-2 hover:border-[#2F6F68]/50 transition-colors shadow-sm"
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span className="w-7 h-7 rounded-full bg-white border border-[#DDD9CF] text-[#29322F] flex items-center justify-center font-bold text-xs shadow-sm">
                    {item.route_id}
                  </span>
                  <span className="text-[#29322F] font-semibold">Line {item.route_id}</span>
                </div>
                {getSeverityBadge(item.severity_tier)}
              </div>

              <div className="space-y-1">
                <div className="flex items-center justify-between text-[11px]">
                  <span className="text-[#6F8F87]">Avg Delay:</span>
                  <span className="text-[#29322F] font-bold">
                    {item.delay_seconds > 0
                      ? `${Math.round(item.delay_seconds)}s (${Math.round(item.delay_seconds / 60)} min)`
                      : 'On Time'}
                  </span>
                </div>
                <div className="flex items-center justify-between text-[11px]">
                  <span className="text-[#6F8F87]">Reporting Stops:</span>
                  <span className="text-[#2F6F68] font-semibold">{item.affected_stations_count}</span>
                </div>
              </div>

              <div className="pt-1 border-t border-[#DDD9CF] flex items-center justify-between">
                {getStateBadge(item.data_state)}
              </div>
            </div>
          ))}
        </div>
      )}

      {isFeedLive && routesWithDelay.length === 0 && displayDelays.length > 0 && (
        <div className="text-[11px] text-[#4F8A63] font-semibold text-center pb-2">
          ✓ All monitored lines reporting zero delay from live MTA GTFS-RT telemetry
        </div>
      )}
    </Card>
  );
};
