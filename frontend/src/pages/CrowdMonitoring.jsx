import React, { useState, useMemo } from 'react';
import { MapContainer, TileLayer, CircleMarker, Popup, useMap } from 'react-leaflet';
import {
  MapPin,
  Filter,
  Search,
  Layers,
  Clock,
  Building,
  AlertTriangle,
  Info,
} from 'lucide-react';
import StatusBadge from '../components/StatusBadge';

// Helper component to center map when selected station changes
function MapRecenter({ center }) {
  const map = useMap();
  React.useEffect(() => {
    if (center) {
      map.setView(center, 14, { animate: true });
    }
  }, [center, map]);
  return null;
}

export default function CrowdMonitoring({
  stationsData,
  onInspectStation,
  onHourChange,
  activeHour = 8,
}) {
  const stations = stationsData?.stations || [];

  const [searchQuery, setSearchQuery] = useState('');
  const [selectedBorough, setSelectedBorough] = useState('All');
  const [selectedCongestion, setSelectedCongestion] = useState('All');
  const [selectedStructure, setSelectedStructure] = useState('All');
  const [mapCenter, setMapCenter] = useState(null);
  const [basemapKey, setBasemapKey] = useState('esri');
  const [basemapError, setBasemapError] = useState(false);

  const handleTileError = () => {
    if (basemapKey === 'esri') {
      console.warn('Esri dark tiles encountered an issue; falling back to OpenStreetMap.');
      setBasemapError(true);
      setBasemapKey('osm');
    }
  };

  // Available boroughs & structures
  const boroughs = ['All', 'Manhattan', 'Brooklyn', 'Queens', 'Bronx'];
  const structures = ['All', 'Subway', 'Elevated', 'Open Cut'];

  // Filtered stations
  const filteredStations = useMemo(() => {
    return stations.filter((s) => {
      const matchSearch =
        !searchQuery ||
        s.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        s.borough.toLowerCase().includes(searchQuery.toLowerCase());

      const matchBorough =
        selectedBorough === 'All' ||
        s.borough.toLowerCase() === selectedBorough.toLowerCase();

      const matchCongestion =
        selectedCongestion === 'All' || s.congestion_level === selectedCongestion;

      const matchStructure =
        selectedStructure === 'All' ||
        s.structure.toLowerCase() === selectedStructure.toLowerCase();

      return matchSearch && matchBorough && matchCongestion && matchStructure;
    });
  }, [stations, searchQuery, selectedBorough, selectedCongestion, selectedStructure]);

  const counts = useMemo(() => {
    let high = 0;
    let med = 0;
    let low = 0;
    filteredStations.forEach((st) => {
      if (st.congestion_level === 'High') high++;
      else if (st.congestion_level === 'Medium') med++;
      else if (st.congestion_level === 'Low') low++;
    });
    return { high, med, low };
  }, [filteredStations]);

  return (
    <div className="space-y-4">
      {/* Top Filter Bar */}
      <div className="ops-panel p-4 space-y-3">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <div className="flex items-center gap-2">
              <span className="text-xs font-mono font-bold px-2 py-0.5 rounded bg-teal-500/10 text-[#00D4AA] border border-teal-500/20">
                GEOSPATIAL HEATMAP
              </span>
              <h2 className="text-base font-bold text-white">
                Subway Crowd Monitoring & Station Heatmap
              </h2>
            </div>
            <p className="text-xs text-slate-400 mt-0.5">
              Live predicted station passenger density across NYC transit corridors (Model: Random Forest).
            </p>
          </div>

          {/* Quick Metrics Pills */}
          <div className="flex items-center gap-2 text-xs font-mono">
            <span className="px-2.5 py-1 rounded bg-slate-900 border border-slate-800 text-slate-300">
              Showing: <strong className="text-white">{filteredStations.length}</strong> / {stations.length}
            </span>
            <span className="px-2.5 py-1 rounded bg-rose-500/10 border border-rose-500/30 text-rose-400">
              High: {counts.high}
            </span>
            <span className="px-2.5 py-1 rounded bg-amber-500/10 border border-amber-500/30 text-amber-400">
              Med: {counts.med}
            </span>
            <span className="px-2.5 py-1 rounded bg-emerald-500/10 border border-emerald-500/30 text-emerald-400">
              Low: {counts.low}
            </span>
          </div>
        </div>

        {/* Filters Controls Row */}
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-5 gap-3 pt-2 border-t border-slate-800/80">
          {/* Search */}
          <div className="relative">
            <Search
              size={14}
              className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400"
            />
            <input
              type="text"
              placeholder="Search station or street..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="ops-input pl-8 text-xs py-1.5"
            />
          </div>

          {/* Borough Filter */}
          <div>
            <select
              value={selectedBorough}
              onChange={(e) => setSelectedBorough(e.target.value)}
              className="ops-select text-xs py-1.5"
            >
              {boroughs.map((b) => (
                <option key={b} value={b}>
                  {b === 'All' ? 'All Boroughs' : b}
                </option>
              ))}
            </select>
          </div>

          {/* Congestion Tier Filter */}
          <div>
            <select
              value={selectedCongestion}
              onChange={(e) => setSelectedCongestion(e.target.value)}
              className="ops-select text-xs py-1.5"
            >
              <option value="All">All Congestion Tiers</option>
              <option value="High">🚨 High Congestion Only</option>
              <option value="Medium">⚠️ Medium Congestion Only</option>
              <option value="Low">✅ Low Congestion Only</option>
            </select>
          </div>

          {/* Structure Filter */}
          <div>
            <select
              value={selectedStructure}
              onChange={(e) => setSelectedStructure(e.target.value)}
              className="ops-select text-xs py-1.5"
            >
              {structures.map((s) => (
                <option key={s} value={s}>
                  {s === 'All' ? 'All Structures' : s}
                </option>
              ))}
            </select>
          </div>

          {/* Temporal Hour Slider */}
          <div className="flex items-center gap-2 px-3 py-1 rounded bg-slate-900 border border-slate-800">
            <Clock size={14} className="text-[#00D4AA] shrink-0" />
            <div className="flex-1">
              <div className="flex justify-between text-[10px] text-slate-400">
                <span>Hour</span>
                <span className="font-mono text-white font-bold">{activeHour}:00</span>
              </div>
              <input
                type="range"
                min="0"
                max="23"
                value={activeHour}
                onChange={(e) => onHourChange && onHourChange(Number(e.target.value))}
                className="w-full h-1 bg-slate-700 rounded-lg appearance-none cursor-pointer accent-[#00D4AA]"
              />
            </div>
          </div>
        </div>
      </div>

      {/* Main Map & Station List Panel */}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-4">
        {/* Interactive Leaflet Map (3 cols) */}
        <div className="lg:col-span-3 ops-panel overflow-hidden relative" style={{ height: '580px' }}>
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
            center={[40.7580, -73.9855]} // Times Square / Manhattan Center
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

            {mapCenter && <MapRecenter center={mapCenter} />}

            {filteredStations.map((station) => {
              const isHigh = station.congestion_level === 'High';
              const isMed = station.congestion_level === 'Medium';
              const color = isHigh ? '#EF4444' : isMed ? '#F59E0B' : '#10B981';
              const radius = isHigh ? 8 : isMed ? 6 : 5;

              return (
                <CircleMarker
                  key={station.id}
                  center={[station.latitude, station.longitude]}
                  radius={radius}
                  pathOptions={{
                    fillColor: color,
                    fillOpacity: 0.85,
                    color: isHigh ? '#FFFFFF' : color,
                    weight: isHigh ? 2 : 1,
                  }}
                  eventHandlers={{
                    click: () => onInspectStation(station),
                  }}
                >
                  <Popup>
                    <div className="space-y-1.5 text-xs text-slate-100">
                      <div className="font-bold text-sm text-white">
                        {station.name}
                      </div>
                      <div className="text-[11px] text-slate-400">
                        {station.borough} • {station.structure}
                      </div>
                      <div className="pt-1 flex items-center justify-between gap-3">
                        <StatusBadge status={station.congestion_level} size="sm" />
                        <span className="font-mono text-[11px] text-[#00D4AA]">
                          {Math.round((station.confidence || 0.85) * 100)}% Conf
                        </span>
                      </div>
                      <div className="text-[11px] text-slate-300 pt-1 border-t border-slate-700">
                        {station.recommendation}
                      </div>
                      <button
                        onClick={() => onInspectStation(station)}
                        className="mt-2 w-full py-1 text-center bg-[#00D4AA] text-[#0B1220] font-bold rounded text-[11px] hover:brightness-110"
                      >
                        Inspect Full Telemetry
                      </button>
                    </div>
                  </Popup>
                </CircleMarker>
              );
            })}
          </MapContainer>

          {/* Map Overlay Legend */}
          <div className="absolute bottom-4 left-4 z-[1000] bg-slate-900/90 backdrop-blur-md p-3 rounded-lg border border-slate-700/80 text-xs space-y-1.5 shadow-xl">
            <div className="text-[10px] font-bold uppercase tracking-wider text-slate-400 mb-1">
              Congestion Density
            </div>
            <div className="flex items-center gap-2 text-slate-200">
              <span className="w-3 h-3 rounded-full bg-rose-500 inline-block border border-white" />
              <span>High (Overcrowding Directive)</span>
            </div>
            <div className="flex items-center gap-2 text-slate-200">
              <span className="w-3 h-3 rounded-full bg-amber-500 inline-block" />
              <span>Medium (Platform Watch)</span>
            </div>
            <div className="flex items-center gap-2 text-slate-200">
              <span className="w-3 h-3 rounded-full bg-emerald-500 inline-block" />
              <span>Low (Normal Headway)</span>
            </div>
          </div>
        </div>

        {/* Station Scroll List (1 col) */}
        <div className="ops-panel p-4 flex flex-col justify-between" style={{ height: '580px' }}>
          <div>
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-xs font-bold uppercase tracking-wider text-slate-300">
                Filtered Stations ({filteredStations.length})
              </h3>
              <span className="text-[10px] text-slate-500 font-mono">Click to Center</span>
            </div>

            <div className="overflow-y-auto space-y-2 pr-1" style={{ maxHeight: '480px' }}>
              {filteredStations.length > 0 ? (
                filteredStations.map((st) => (
                  <div
                    key={st.id}
                    onClick={() => {
                      setMapCenter([st.latitude, st.longitude]);
                    }}
                    onDoubleClick={() => onInspectStation(st)}
                    className="p-2.5 rounded bg-slate-900/70 hover:bg-slate-800 border border-slate-800 cursor-pointer transition space-y-1"
                  >
                    <div className="flex items-start justify-between gap-1">
                      <span className="font-semibold text-xs text-slate-200 truncate">
                        {st.name}
                      </span>
                      <StatusBadge status={st.congestion_level} size="sm" />
                    </div>
                    <div className="flex items-center justify-between text-[11px] text-slate-400">
                      <span>{st.borough}</span>
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          onInspectStation(st);
                        }}
                        className="text-[#00D4AA] hover:underline"
                      >
                        Inspect &rarr;
                      </button>
                    </div>
                  </div>
                ))
              ) : (
                <div className="text-center py-10 text-slate-500 text-xs">
                  No stations match selected filters.
                </div>
              )}
            </div>
          </div>

          <div className="pt-2 border-t border-slate-800 text-[10px] text-slate-500">
            Source: 361 Audited NYC Subway Stations. Double click station to open operational modal.
          </div>
        </div>
      </div>
    </div>
  );
}
