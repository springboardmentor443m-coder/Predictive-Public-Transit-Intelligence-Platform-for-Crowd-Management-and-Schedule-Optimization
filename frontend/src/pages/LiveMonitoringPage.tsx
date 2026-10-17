import React, { useState, useEffect, useRef, useCallback } from 'react';
import { liveService, FeedHealthSummary, TransitVehicleState, NormalizedTripUpdate, NormalizedServiceAlert } from '../services/liveService';
import { alertService, OperationalAlert, AlertSummary } from '../services/alertService';
import { cachedFetch } from '../services/cache';
import { FeedHealthBanner } from '../components/live/FeedHealthBanner';
import { RouteFilter } from '../components/live/RouteFilter';
import { Card } from '../components/common/Card';
import { Badge } from '../components/common/Badge';
import { Radio, AlertTriangle, ShieldAlert, Info } from 'lucide-react';

export const LiveMonitoringPage: React.FC = () => {
  const [health, setHealth] = useState<FeedHealthSummary | null>(null);
  const [vehicles, setVehicles] = useState<TransitVehicleState[]>([]);
  const [trips, setTrips] = useState<NormalizedTripUpdate[]>([]);
  const [alerts, setAlerts] = useState<NormalizedServiceAlert[]>([]);
  const [selectedRoute, setSelectedRoute] = useState<string>('');

  const [loading, setLoading] = useState<boolean>(true);
  const [syncing, setSyncing] = useState<boolean>(false);

  // Stable reference for fetchLiveData so intervals don't capture stale closures
  const selectedRouteRef = useRef(selectedRoute);
  useEffect(() => { selectedRouteRef.current = selectedRoute; }, [selectedRoute]);

  // Stable vehicle setter — only replaces the array reference when vehicle IDs change.
  // This prevents LiveTrainMap's useMemo from recomputing (and all markers from
  // re-rendering) on every 30s poll when the same vehicles are returned.
  const setVehiclesStable = useCallback((next: TransitVehicleState[]) => {
    setVehicles(prev => {
      if (prev.length !== next.length) return next;
      const prevIds = prev.map(v => v.vehicle_id).join(',');
      const nextIds = next.map(v => v.vehicle_id).join(',');
      return prevIds === nextIds ? prev : next;
    });
  }, []);

  const [operationalAlerts, setOperationalAlerts] = useState<OperationalAlert[]>([]);
  const [operationalSummary, setOperationalSummary] = useState<AlertSummary | null>(null);

  const fetchLiveData = useCallback(async () => {
    const route = selectedRouteRef.current || undefined;
    const cacheKey = `live:${route ?? 'all'}`;
    try {
      const [hData, vData, tData, aData, opAlerts, opSum] = await Promise.all([
        cachedFetch(`${cacheKey}:health`,    () => liveService.getHealth(),              30_000, setHealth),
        cachedFetch(`${cacheKey}:vehicles`,  () => liveService.getVehicles(route),       30_000, setVehiclesStable),
        cachedFetch(`${cacheKey}:trips`,     () => liveService.getTrips(route),          30_000, setTrips),
        cachedFetch(`${cacheKey}:alerts`,    () => liveService.getAlerts(route),         30_000, setAlerts),
        cachedFetch('alerts:active',         () => alertService.getActiveAlerts(),       30_000, setOperationalAlerts),
        cachedFetch('alerts:summary',        () => alertService.getAlertSummary(),       60_000, setOperationalSummary),
      ]);
      setHealth(hData);
      setVehiclesStable(vData);
      setTrips(tData);
      setAlerts(aData);
      setOperationalAlerts(opAlerts);
      setOperationalSummary(opSum);
    } catch (e) {
      console.error('Failed to fetch live MTA data:', e);
    } finally {
      setLoading(false);
    }
  }, [setVehiclesStable]);

  // Initial load + 30s polling — do NOT trigger on every WS event
  // (WS events update positions directly via LiveTrainMap's own socket)
  useEffect(() => {
    fetchLiveData();
    const interval = setInterval(fetchLiveData, 30_000);
    return () => clearInterval(interval);
  }, [fetchLiveData]);

  // Re-fetch when route filter changes
  useEffect(() => {
    if (!loading) fetchLiveData();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedRoute]);


  const handleManualSync = async () => {
    setSyncing(true);
    try {
      await liveService.triggerSync();
      await fetchLiveData();
    } catch (e) {
      console.error('Manual sync failed:', e);
    } finally {
      setSyncing(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="space-y-4">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-2">
          <div>
            <h1 className="text-xl font-bold text-[#29322F] font-sans flex items-center gap-2">
              <Radio className="w-5 h-5 text-[#2F6F68]" />
              Live Operations Monitoring
            </h1>
            <p className="text-sm text-[#6F8F87] font-sans">
              Real-Time NYC MTA Subway Telemetry & Operational State.
            </p>
          </div>

          <Badge variant={health?.is_live ? "cyan" : "amber"} size="md">
            Data State: {health?.is_live ? "LIVE" : "STALE"}
          </Badge>
        </div>

        <FeedHealthBanner
          health={health}
          onRefresh={handleManualSync}
          isSyncing={syncing}
        />
      </div>

      <div className="space-y-2">
        <div className="text-xs font-sans uppercase tracking-wider text-[#6F8F87] font-semibold">
          Filter Line:
        </div>
        <RouteFilter
          selectedRoute={selectedRoute}
          onSelectRoute={(r) => setSelectedRoute(r)}
        />
      </div>

      {(operationalSummary?.total_active ?? alerts.length) > 0 && (
        <Card className="border-[#C58A3A] bg-[#C58A3A]/10 space-y-3 shadow-sm">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2 text-[#C58A3A] font-sans text-xs font-semibold uppercase">
              <AlertTriangle className="w-4 h-4" />
              <span>Active Network Alerts ({operationalSummary ? operationalSummary.total_active : alerts.length})</span>
            </div>
            {operationalSummary && (
              <div className="flex gap-2 text-[10px] font-sans">
                <span className="text-[#B9574B] font-bold">{operationalSummary.critical_count} Critical</span>
                <span className="text-[#C58A3A] font-bold">{operationalSummary.high_count} High</span>
                <span className="text-[#6F8F87] font-semibold">{operationalSummary.overcrowding_count} Crowd • {operationalSummary.live_delays_count} Delay</span>
              </div>
            )}
          </div>
          <div className="space-y-2">
            {operationalAlerts.length > 0 ? (
              operationalAlerts.slice(0, 3).map((alert) => (
                <div key={alert.id} className="p-3 rounded-lg bg-white border border-[#C58A3A]/30 text-xs space-y-1 shadow-sm">
                  <div className="flex justify-between items-start">
                    <div className="font-semibold text-[#29322F]">{alert.title}</div>
                    <Badge variant={alert.severity === 'CRITICAL' ? 'rose' : alert.severity === 'HIGH' ? 'amber' : 'slate'} size="sm">
                      {alert.severity}
                    </Badge>
                  </div>
                  {alert.description && (
                    <p className="text-[#6F8F87] text-[11px] line-clamp-2">{alert.description}</p>
                  )}
                  {alert.entity_name && (
                    <div className="flex gap-1 pt-1 font-sans text-[10px]">
                      <span className="text-[#6F8F87]">Station / Line:</span>
                      <span className="px-1.5 py-0.5 rounded bg-[#F7F5EF] text-[#29322F] border border-[#DDD9CF]">
                        {alert.entity_name}
                      </span>
                    </div>
                  )}
                </div>
              ))
            ) : (
              alerts.slice(0, 3).map((alert) => (
                <div key={alert.alert_id} className="p-3 rounded-lg bg-white border border-[#C58A3A]/30 text-xs space-y-1 shadow-sm">
                  <div className="font-semibold text-[#29322F]">{alert.header_text}</div>
                  {alert.description_text && (
                    <p className="text-[#6F8F87] text-[11px] line-clamp-2">{alert.description_text}</p>
                  )}
                  {alert.affected_routes.length > 0 && (
                    <div className="flex gap-1 pt-1 font-sans text-[10px]">
                      <span className="text-[#6F8F87]">Lines:</span>
                      {alert.affected_routes.map((r, i) => (
                        <span key={i} className="px-1.5 py-0.5 rounded bg-[#F7F5EF] text-[#29322F] border border-[#DDD9CF]">
                          {r}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              ))
            )}
          </div>
        </Card>
      )}


      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-3">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-semibold font-sans text-[#29322F]">
              Active Vehicles in Operation ({vehicles.length})
            </h3>
            <span className="text-[11px] font-sans text-[#6F8F87]">
              Source: MTA GTFS-RT
            </span>
          </div>

          <Card className="p-0 overflow-hidden border-[#DDD9CF] shadow-sm bg-white">
            <div className="overflow-x-auto max-h-[420px]">
              <table className="w-full text-left border-collapse">
                <thead className="sticky top-0 bg-[#F7F5EF] border-b border-[#DDD9CF] text-[11px] font-sans uppercase text-[#6F8F87] z-10">
                  <tr>
                    <th className="p-3 font-semibold">Route</th>
                    <th className="p-3 font-semibold">Train / Trip ID</th>
                    <th className="p-3 font-semibold">Current Stop</th>
                    <th className="p-3 font-semibold">Status</th>
                    <th className="p-3 text-right font-semibold">Timestamp</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#DDD9CF] text-xs">
                  {loading ? (
                    <tr>
                      <td colSpan={5} className="p-6 text-center text-[#6F8F87] font-sans">
                        Loading live MTA trains...
                      </td>
                    </tr>
                  ) : vehicles.length === 0 ? (
                    <tr>
                      <td colSpan={5} className="p-6 text-center text-[#6F8F87] font-sans">
                        No active live trains for selected route.
                      </td>
                    </tr>
                  ) : (
                    vehicles.map((v) => (
                      <tr key={v.vehicle_id} className="hover:bg-[#F7F5EF] font-sans transition-colors">
                        <td className="p-3">
                          <span className="px-2 py-0.5 rounded bg-[#2F6F68]/10 text-[#2F6F68] font-bold border border-[#2F6F68]/20">
                            {v.route_id}
                          </span>
                        </td>
                        <td className="p-3 text-[#29322F] font-semibold">{v.vehicle_id}</td>
                        <td className="p-3 text-[#6F8F87]">{v.current_stop_id || 'In Transit'}</td>
                        <td className="p-3 text-[#6F8F87]">{v.current_status || 'IN_TRANSIT'}</td>
                        <td className="p-3 text-right text-[#6F8F87]">
                          {new Date(v.timestamp).toLocaleTimeString()}
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </Card>
        </div>

        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-semibold font-sans text-[#29322F]">
              Trip Estimates & Delays ({trips.length})
            </h3>
            <span className="text-[11px] font-sans text-[#6F8F87]">Live Adherence</span>
          </div>

          <Card className="p-4 space-y-3 max-h-[420px] overflow-y-auto border-[#DDD9CF] shadow-sm bg-white">
            {loading ? (
              <div className="text-[#6F8F87] font-sans text-xs text-center py-4">
                Loading trip updates...
              </div>
            ) : trips.length === 0 ? (
              <div className="text-[#6F8F87] font-sans text-xs text-center py-4">
                No active trip updates recorded.
              </div>
            ) : (
              trips.slice(0, 15).map((tu, idx) => (
                <div key={idx} className="p-3 rounded-lg bg-[#F7F5EF] border border-[#DDD9CF] space-y-1 font-sans text-xs shadow-sm">
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-[#29322F]">Line {tu.route_id}</span>
                    <Badge variant={tu.delay_seconds > 0 ? 'rose' : 'emerald'} size="sm">
                      {tu.delay_seconds > 0 ? `+${Math.round(tu.delay_seconds / 60)}m delay` : 'On Time'}
                    </Badge>
                  </div>
                  <div className="text-[#6F8F87] text-[11px]">Stop ID: {tu.stop_id}</div>
                  <div className="text-[#6F8F87] text-[10px] flex items-center justify-between pt-1">
                    <span>Trip: {tu.trip_id}</span>
                    <span>{new Date(tu.timestamp).toLocaleTimeString()}</span>
                  </div>
                </div>
              ))
            )}
          </Card>
        </div>
      </div>
    </div>
  );
};
