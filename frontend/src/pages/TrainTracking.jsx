import React, { useState, useEffect } from 'react';
import { MapContainer, TileLayer, Polyline, CircleMarker, Popup } from 'react-leaflet';
import {
  Train,
  Clock,
  Gauge,
  AlertTriangle,
  Play,
  Pause,
  RefreshCw,
  Zap,
  Radio,
  ArrowRight,
  Layers,
} from 'lucide-react';
import StatusBadge from '../components/StatusBadge';
import MetricCard from '../components/MetricCard';

export default function TrainTracking({
  trainsData,
  onRefresh,
  isRefreshing,
  onInjectDelay,
}) {
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [selectedRouteFilter, setSelectedRouteFilter] = useState('All');
  const [injectTrainId, setInjectTrainId] = useState('');
  const [injectMinutes, setInjectMinutes] = useState(5);
  const [isInjecting, setIsInjecting] = useState(false);
  const [injectMessage, setInjectMessage] = useState(null);
  const [basemapKey, setBasemapKey] = useState('esri');
  const [basemapError, setBasemapError] = useState(false);

  const handleTileError = () => {
    if (basemapKey === 'esri') {
      console.warn('Esri dark tiles encountered an issue; falling back to OpenStreetMap.');
      setBasemapError(true);
      setBasemapKey('osm');
    }
  };

  const trains = trainsData?.trains || [];
  const routes = trainsData?.routes || {};
  const kpis = trainsData?.kpis || {
    active_trains: trains.length || 29,
    delayed_trains: trains.filter((t) => t.Status === 'Delayed').length || 6,
    ontime_trains: trains.filter((t) => t.Status !== 'Delayed').length || 23,
    avg_speed: 27.1,
    on_time_pct: 79.3,
  };

  // Auto-refresh interval (every 3s)
  useEffect(() => {
    if (!autoRefresh) return;
    const timer = setInterval(() => {
      if (onRefresh) onRefresh();
    }, 3000);
    return () => clearInterval(timer);
  }, [autoRefresh, onRefresh]);

  const filteredTrains = trains.filter(
    (t) => selectedRouteFilter === 'All' || t.Route === selectedRouteFilter
  );

  const handleInjectDelay = async (e) => {
    e.preventDefault();
    if (!injectTrainId || !onInjectDelay) return;
    setIsInjecting(true);
    setInjectMessage(null);
    try {
      const res = await onInjectDelay(injectTrainId, Number(injectMinutes));
      setInjectMessage({
        type: 'success',
        text: `Injected ${injectMinutes}m delay into ${injectTrainId}! Telemetry updated.`,
      });
      if (onRefresh) onRefresh();
    } catch (err) {
      setInjectMessage({
        type: 'error',
        text: `Failed to inject delay: ${err.message}`,
      });
    } finally {
      setIsInjecting(false);
    }
  };

  return (
    <div className="space-y-5">
      {/* Top Banner: Disclaimer & Controls */}
      <div className="ops-panel p-4 flex flex-col md:flex-row md:items-center justify-between gap-4 bg-gradient-to-r from-[#111827] via-slate-900 to-[#1F293D]">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="badge-simulated px-2 py-0.5 text-xs font-bold font-mono">
              SIMULATED NYC TRANSIT TELEMETRY
            </span>
            <span className="text-xs text-slate-400 font-mono">
              24-32 TRAINS IN FLIGHT
            </span>
          </div>
          <h2 className="text-lg font-bold text-white flex items-center gap-2">
            <Train size={18} className="text-[#00D4AA]" />
            <span>Live Subway Train Tracking & Kinematics Engine</span>
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Synthetic multi-route subway simulator demonstrating dynamic headway transitions, speed curves, and stochastic delays.
          </p>
        </div>

        {/* Live Controls */}
        <div className="flex items-center gap-3">
          <button
            onClick={() => setAutoRefresh(!autoRefresh)}
            className={`btn-secondary text-xs ${
              autoRefresh ? 'border-emerald-500/40 text-emerald-400' : 'text-slate-400'
            }`}
          >
            {autoRefresh ? <Pause size={14} /> : <Play size={14} />}
            <span>{autoRefresh ? 'Live Stepping: ON (3s)' : 'Stepping: PAUSED'}</span>
          </button>

          <button
            onClick={onRefresh}
            disabled={isRefreshing}
            className="btn-primary text-xs"
          >
            <RefreshCw size={14} className={isRefreshing ? 'animate-spin' : ''} />
            <span>Step Kinematics</span>
          </button>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard
          title="Active Trains in Corridor"
          value={kpis.active_trains}
          delta="100% Active"
          deltaType="positive"
          subtext="across 8 MTA lines"
          icon={Train}
          accentColor="#00D4AA"
        />

        <MetricCard
          title="On-Time Performance"
          value={`${kpis.on_time_pct}%`}
          delta={`${kpis.ontime_trains} On-Time / Arriving`}
          deltaType="positive"
          subtext="tolerance < 3.0 min"
          icon={Clock}
          accentColor="#38BDF8"
        />

        <MetricCard
          title="Delayed Trains"
          value={kpis.delayed_trains}
          delta={kpis.delayed_trains > 8 ? 'High Delay Surge' : 'Manageable'}
          deltaType={kpis.delayed_trains > 8 ? 'negative' : 'warning'}
          subtext="requiring dispatch regulation"
          icon={AlertTriangle}
          accentColor="#EF4444"
        />

        <MetricCard
          title="Mean Corridor Speed"
          value={`${kpis.avg_speed} mph`}
          delta="Kinematic Model"
          deltaType="neutral"
          subtext="acceleration + cruising"
          icon={Gauge}
          accentColor="#818CF8"
        />
      </div>

      {/* Interactive Map & Route Filter */}
      <div className="ops-panel p-4 space-y-3">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center gap-2">
            <Radio size={14} className="text-[#00D4AA] animate-pulse" />
            <h3 className="text-sm font-bold text-white">
              NYC Rail Network Map & Live Telemetry Points
            </h3>
          </div>

          {/* Route filter selector */}
          <div className="flex items-center gap-2 text-xs">
            <span className="text-slate-400">Filter Line:</span>
            {['All', '1', '4', '6', '7', 'A', 'E', 'L', 'N'].map((r) => (
              <button
                key={r}
                onClick={() => setSelectedRouteFilter(r)}
                className={`px-2.5 py-1 rounded font-mono font-bold transition text-xs ${
                  selectedRouteFilter === r
                    ? 'bg-[#00D4AA] text-[#0B1220] shadow-sm'
                    : 'bg-slate-800 text-slate-300 hover:bg-slate-700'
                }`}
              >
                {r === 'All' ? 'ALL LINES' : `LINE ${r}`}
              </button>
            ))}
          </div>
        </div>

        {/* Leaflet Map */}
        <div className="h-[480px] w-full rounded-lg overflow-hidden border border-slate-800 relative">
          {/* Basemap Switcher Overlay */}
          <div className="absolute top-3 right-3 z-[1000] flex items-center gap-1.5 bg-slate-900/90 backdrop-blur-sm p-1 rounded-md border border-slate-700 shadow-lg text-xs">
            <Layers size={13} className="text-[#00D4AA] ml-1.5" />
            <button
              type="button"
              onClick={() => {
                setBasemapError(false);
                setBasemapKey('esri');
              }}
              className={`px-2 py-0.5 rounded text-[11px] font-medium transition ${
                basemapKey === 'esri'
                  ? 'bg-[#00D4AA] text-[#0B1220] font-bold shadow-sm'
                  : 'text-slate-300 hover:text-white hover:bg-slate-800'
              }`}
              title="Esri World Dark Gray Basemap (No API key required)"
            >
              🌙 Dark Ops
            </button>
            <button
              type="button"
              onClick={() => setBasemapKey('osm')}
              className={`px-2 py-0.5 rounded text-[11px] font-medium transition ${
                basemapKey === 'osm'
                  ? 'bg-[#00D4AA] text-[#0B1220] font-bold shadow-sm'
                  : 'text-slate-300 hover:text-white hover:bg-slate-800'
              }`}
              title="OpenStreetMap Standard Basemap (Public fallback)"
            >
              🗺️ OpenStreetMap
            </button>
          </div>

          {basemapError && (
            <div className="absolute top-12 right-3 z-[1000] bg-amber-950/90 border border-amber-600 text-amber-200 text-[11px] px-2.5 py-1 rounded flex items-center gap-1.5 shadow">
              <AlertTriangle size={12} className="text-amber-400" />
              <span>Network fallback: switched to OpenStreetMap</span>
            </div>
          )}

          <MapContainer
            center={[40.7580, -73.9855]}
            zoom={12}
            scrollWheelZoom={true}
            style={{ height: '100%', width: '100%', background: '#0B1220' }}
          >
            {basemapKey === 'esri' ? (
              <>
                <TileLayer
                  attribution='Tiles &copy; Esri &mdash; Esri, DeLorme, NAVTEQ'
                  url="https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Base/MapServer/tile/{z}/{y}/{x}"
                  maxNativeZoom={16}
                  maxZoom={18}
                  eventHandlers={{
                    tileerror: handleTileError,
                  }}
                />
                <TileLayer
                  url="https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Reference/MapServer/tile/{z}/{y}/{x}"
                  maxNativeZoom={16}
                  maxZoom={18}
                />
              </>
            ) : (
              <TileLayer
                attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                maxZoom={19}
              />
            )}

            {/* Render Route Corridors (PolyLines) */}
            {Object.values(routes).map((route) => {
              if (selectedRouteFilter !== 'All' && route.route !== selectedRouteFilter) {
                return null;
              }
              const positions = route.lats.map((lat, idx) => [lat, route.lons[idx]]);
              return (
                <Polyline
                  key={route.route}
                  positions={positions}
                  pathOptions={{
                    color: route.color || '#38BDF8',
                    weight: 3.5,
                    opacity: 0.65,
                    dashArray: '4, 8',
                  }}
                />
              );
            })}

            {/* Render Active Train Markers */}
            {filteredTrains.map((train) => {
              const isDelayed = train.Status === 'Delayed';
              const markerColor = train['Route Color'] || '#00D4AA';

              return (
                <CircleMarker
                  key={train['Train ID']}
                  center={[train['Current Latitude'], train['Current Longitude']]}
                  radius={isDelayed ? 8 : 7}
                  pathOptions={{
                    fillColor: isDelayed ? '#EF4444' : markerColor,
                    fillOpacity: 0.95,
                    color: '#FFFFFF',
                    weight: 2,
                  }}
                >
                  <Popup>
                    <div className="p-1 space-y-1 text-xs text-white">
                      <div className="flex items-center justify-between gap-2 border-b border-slate-700 pb-1">
                        <span className="font-bold font-mono text-sm">
                          {train['Train ID']} ({train['Route']})
                        </span>
                        <StatusBadge status={train.Status} size="sm" />
                      </div>
                      <div className="text-[11px] text-slate-300">
                        <strong>Line:</strong> {train['Route Name']}
                      </div>
                      <div className="text-[11px] text-slate-300">
                        <strong>Current Station:</strong> {train['Current Station']}
                      </div>
                      <div className="text-[11px] text-slate-300">
                        <strong>Next Station:</strong> {train['Next Station']}
                      </div>
                      <div className="flex justify-between text-[11px] pt-1 text-slate-400">
                        <span>Speed: <strong className="text-white">{train['Speed (mph)']} mph</strong></span>
                        <span>Delay: <strong className="text-white">{train['Delay (min)']}m</strong></span>
                      </div>
                    </div>
                  </Popup>
                </CircleMarker>
              );
            })}
          </MapContainer>

          {/* Map Overlay Badge */}
          <div className="absolute top-3 right-3 z-[1000] bg-slate-900/90 backdrop-blur-md p-2.5 rounded border border-slate-700 text-xs font-mono space-y-1 shadow-lg">
            <div className="text-[10px] text-slate-400 uppercase font-bold">
              Corridor Telemetry
            </div>
            <div className="text-slate-200">
              Active Trains: <strong className="text-[#00D4AA]">{filteredTrains.length}</strong>
            </div>
            <div className="text-slate-200">
              Speed: <strong className="text-sky-400">{kpis.avg_speed} mph</strong>
            </div>
          </div>
        </div>
      </div>

      {/* Fleet Telemetry Table & Delay Injection Simulator */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left 2 Cols: Real-time Trains Table */}
        <div className="lg:col-span-2 ops-panel p-5">
          <div className="flex items-center justify-between mb-3">
            <div>
              <h3 className="text-sm font-bold text-white flex items-center gap-2">
                <Train size={16} className="text-[#00D4AA]" />
                <span>Simulated Train Fleet Telemetry Manifest</span>
              </h3>
              <p className="text-xs text-slate-400 mt-0.5">
                Real-time interpolated GPS kinematics, block progression, and headway status.
              </p>
            </div>
            <span className="text-xs font-mono text-slate-500">
              Showing {filteredTrains.length} Trains
            </span>
          </div>

          <div className="overflow-x-auto max-h-96">
            <table className="ops-table">
              <thead>
                <tr>
                  <th>Train ID</th>
                  <th>Route</th>
                  <th>Current Station</th>
                  <th>Next Station</th>
                  <th>Speed</th>
                  <th>Progress</th>
                  <th>Status</th>
                  <th>Delay</th>
                </tr>
              </thead>
              <tbody>
                {filteredTrains.map((t) => (
                  <tr key={t['Train ID']} className="hover:bg-slate-800/40">
                    <td className="font-mono font-bold text-[#00D4AA]">
                      {t['Train ID']}
                    </td>
                    <td>
                      <span
                        className="px-2 py-0.5 rounded text-[11px] font-bold font-mono text-white"
                        style={{ backgroundColor: t['Route Color'] || '#2563EB' }}
                      >
                        {t['Route']}
                      </span>
                    </td>
                    <td className="font-medium text-white max-w-[130px] truncate">
                      {t['Current Station']}
                    </td>
                    <td className="text-slate-300 max-w-[130px] truncate">
                      {t['Next Station']}
                    </td>
                    <td className="font-mono text-xs">{t['Speed (mph)']} mph</td>
                    <td className="w-24">
                      <div className="h-1.5 w-full bg-slate-800 rounded-full overflow-hidden">
                        <div
                          className="h-full bg-sky-400 rounded-full"
                          style={{ width: `${Math.round((t['Segment Progress'] || 0) * 100)}%` }}
                        />
                      </div>
                    </td>
                    <td>
                      <StatusBadge status={t['Status']} size="sm" />
                    </td>
                    <td className="font-mono text-xs text-slate-300">
                      {t['Delay (min)'] > 0 ? (
                        <span className="text-amber-400 font-bold">+{t['Delay (min)']}m</span>
                      ) : (
                        <span className="text-emerald-400">0.0m</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Right Col: Incident & Delay Injection Console */}
        <div className="ops-panel p-5 flex flex-col justify-between">
          <div>
            <div className="flex items-center gap-2 mb-2">
              <Zap size={16} className="text-[#F59E0B]" />
              <h3 className="text-sm font-bold text-white">
                Live Incident & Delay Injector
              </h3>
            </div>
            <p className="text-xs text-slate-400 mb-4 leading-relaxed">
              Inject synthetic track switch, door hold, or signal delays to evaluate downstream headway cascade reactions.
            </p>

            <form onSubmit={handleInjectDelay} className="space-y-3">
              <div>
                <label className="block text-[11px] font-semibold text-slate-300 uppercase mb-1">
                  Target Train
                </label>
                <select
                  value={injectTrainId}
                  onChange={(e) => setInjectTrainId(e.target.value)}
                  className="ops-select text-xs py-2"
                  required
                >
                  <option value="">Select a train from fleet...</option>
                  {trains.map((t) => (
                    <option key={t['Train ID']} value={t['Train ID']}>
                      {t['Train ID']} (Line {t['Route']} - {t['Current Station']})
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-[11px] font-semibold text-slate-300 uppercase mb-1">
                  Delay Duration (Minutes)
                </label>
                <input
                  type="number"
                  min="1"
                  max="30"
                  step="0.5"
                  value={injectMinutes}
                  onChange={(e) => setInjectMinutes(e.target.value)}
                  className="ops-input text-xs py-2"
                  required
                />
              </div>

              {injectMessage && (
                <div
                  className={`p-2.5 rounded text-xs border ${
                    injectMessage.type === 'success'
                      ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-300'
                      : 'bg-rose-500/10 border-rose-500/30 text-rose-300'
                  }`}
                >
                  {injectMessage.text}
                </div>
              )}

              <button
                type="submit"
                disabled={isInjecting || !injectTrainId}
                className="btn-primary w-full justify-center py-2 text-xs disabled:opacity-50"
              >
                <Zap size={14} />
                <span>{isInjecting ? 'Injecting Delay...' : 'Trigger Train Delay Incident'}</span>
              </button>
            </form>
          </div>

          <div className="mt-4 pt-3 border-t border-slate-800 text-[10px] text-slate-500">
            <strong>System Notice:</strong> Injected delays propagate across the kinematics loop until resolved by simulated dispatch regulation.
          </div>
        </div>
      </div>
    </div>
  );
}
