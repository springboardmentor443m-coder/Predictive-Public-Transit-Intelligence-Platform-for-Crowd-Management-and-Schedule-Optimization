import React, { useMemo } from 'react';
import { MapContainer, TileLayer, Marker, Popup, CircleMarker } from 'react-leaflet';
import L from 'leaflet';
import { Link } from 'react-router-dom';
import { Station, CongestionLabel } from '../types';
import { StatusBadge } from './StatusBadge';
import { Users, ArrowRight, Activity, Flame } from 'lucide-react';

interface StationMapProps {
  stations: Station[];
  predictions?: Record<string, { density: number; label: CongestionLabel }>;
  selectedStationCode?: string;
  onStationSelect?: (station: Station) => void;
  showHeatmapMode?: boolean;
}

// Custom Leaflet DivIcon generator
const createCustomMarkerIcon = (label: CongestionLabel = 'low', isSelected = false) => {
  const colors: Record<CongestionLabel, { fill: string; border: string; glow: string }> = {
    critical: { fill: '#FF0055', border: '#4A0018', glow: 'rgba(255, 0, 85, 0.75)' },
    high: { fill: '#FF9E00', border: '#4D2C00', glow: 'rgba(255, 158, 0, 0.65)' },
    medium: { fill: '#00E5FF', border: '#003A4D', glow: 'rgba(0, 229, 255, 0.55)' },
    low: { fill: '#05FFA1', border: '#003D24', glow: 'rgba(5, 255, 161, 0.45)' },
  };

  const c = colors[label] || colors.low;
  const size = isSelected ? 22 : 16;
  const stroke = isSelected ? 3 : 2;

  const svgHtml = `
    <div style="
      position: relative;
      width: ${size}px;
      height: ${size}px;
      border-radius: 50%;
      background: ${c.fill};
      border: ${stroke}px solid #FFFFFF;
      box-shadow: 0 0 10px ${c.glow}, 0 2px 5px rgba(0,0,0,0.6);
      transition: all 0.3s ease;
      cursor: pointer;
    ">
      ${label === 'critical' ? `<div style="position: absolute; inset: -4px; border-radius: 50%; border: 2px solid ${c.fill}; animation: ping 1.5s cubic-bezier(0, 0, 0.2, 1) infinite; opacity: 0.7;"></div>` : ''}
    </div>
  `;

  return L.divIcon({
    html: svgHtml,
    className: 'custom-station-pin',
    iconSize: [size, size],
    iconAnchor: [size / 2, size / 2],
  });
};

export const StationMap: React.FC<StationMapProps> = ({
  stations,
  predictions = {},
  selectedStationCode,
  onStationSelect,
  showHeatmapMode = false,
}) => {
  // Center of Seoul Metropolitan Area
  const defaultCenter: [number, number] = [37.5512, 126.9882];

  const markerIcons = useMemo(() => {
    return {
      low: createCustomMarkerIcon('low'),
      medium: createCustomMarkerIcon('medium'),
      high: createCustomMarkerIcon('high'),
      critical: createCustomMarkerIcon('critical'),
      low_sel: createCustomMarkerIcon('low', true),
      medium_sel: createCustomMarkerIcon('medium', true),
      high_sel: createCustomMarkerIcon('high', true),
      critical_sel: createCustomMarkerIcon('critical', true),
    };
  }, []);

  return (
    <div className="relative w-full h-full rounded-2xl overflow-hidden border border-border-dark shadow-card bg-bg-surface">
      <MapContainer
        center={defaultCenter}
        zoom={12}
        className="w-full h-full z-10"
        scrollWheelZoom={true}
      >
        {/* Modern Dark Minimalist CartoDB Tiles */}
        <TileLayer
          attribution='&copy; <a href="https://carto.com/attributions">CARTO</a>'
          url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
          maxZoom={19}
        />

        {/* Heatmap density circles when enabled */}
        {showHeatmapMode &&
          stations.map((st) => {
            const pred = predictions[st.station_code];
            const density = pred?.density || 35;
            const radius = Math.max(12, Math.min(36, (density / 100) * 36));
            const color =
              density >= 86
                ? '#EF4444'
                : density >= 68
                ? '#F59E0B'
                : density >= 40
                ? '#06B6D4'
                : '#10B981';

            return (
              <CircleMarker
                key={`heat-${st.station_code}`}
                center={[st.latitude, st.longitude]}
                radius={radius}
                pathOptions={{
                  fillColor: color,
                  fillOpacity: 0.35,
                  color: color,
                  weight: 1,
                  opacity: 0.6,
                }}
              />
            );
          })}

        {/* Station Markers */}
        {stations.map((station) => {
          const pred = predictions[station.station_code];
          const label = pred?.label || 'low';
          const isSelected = selectedStationCode === station.station_code;

          return (
            <React.Fragment key={station.station_code}>
              {showHeatmapMode && (
                <CircleMarker
                  center={[station.latitude, station.longitude]}
                  radius={label === 'critical' ? 26 : label === 'high' ? 20 : label === 'medium' ? 15 : 10}
                  pathOptions={{
                    fillColor: label === 'critical' ? '#FF0055' : label === 'high' ? '#FF9E00' : label === 'medium' ? '#00E5FF' : '#05FFA1',
                    fillOpacity: label === 'critical' ? 0.45 : 0.28,
                    color: label === 'critical' ? '#FF0055' : label === 'high' ? '#FF9E00' : label === 'medium' ? '#00E5FF' : '#05FFA1',
                    weight: 1,
                  }}
                />
              )}

              <Marker
                position={[station.latitude, station.longitude]}
                icon={createCustomMarkerIcon(label, isSelected)}
                eventHandlers={{
                  click: () => onStationSelect?.(station),
                }}
              >
                <Popup className="station-popup">
                  <div className="p-2.5 min-w-[220px]">
                    {/* Header */}
                    <div className="flex items-start justify-between gap-2 mb-2">
                      <div>
                        <h4 className="font-bold text-slate-100 text-sm leading-snug">
                          {station.name_en}
                        </h4>
                        {station.name_kr && (
                          <p className="text-xs text-slate-400 font-sans">{station.name_kr}</p>
                        )}
                      </div>
                      <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-bg-card border border-border-dark text-slate-300">
                        {station.line}
                      </span>
                    </div>

                    {/* Status & Density */}
                    <div className="bg-bg-card/80 border border-border-dark/60 rounded-lg p-2.5 mb-3 flex items-center justify-between">
                      <div>
                        <p className="text-[10px] text-slate-400 font-mono uppercase">Congestion</p>
                        <div className="mt-1">
                          <StatusBadge status={label} size="sm" />
                        </div>
                      </div>
                      <div className="text-right font-mono">
                        <p className="text-[10px] text-slate-400 uppercase">Density</p>
                        <p className="text-sm font-bold text-slate-100">
                          {pred?.density ? `${pred.density.toFixed(1)}%` : '38.5%'}
                        </p>
                      </div>
                    </div>

                    {/* District & Action */}
                    <div className="flex items-center justify-between pt-1 border-t border-border-dark/50 text-xs">
                      <span className="text-slate-400 font-mono text-[11px]">
                        {station.district || 'Seoul'}
                      </span>
                      <Link
                        to={`/stations/${station.station_code}`}
                        className="inline-flex items-center gap-1 font-semibold text-metro-cyan hover:underline text-xs font-mono"
                      >
                        <span>Details</span>
                        <ArrowRight className="w-3.5 h-3.5" />
                      </Link>
                    </div>
                  </div>
                </Popup>
              </Marker>
            </React.Fragment>
          );
        })}
      </MapContainer>

      {/* Floating Map Legend */}
      <div className="absolute bottom-4 right-4 z-20 bg-bg-surface/95 backdrop-blur-md border border-border-dark rounded-xl p-3.5 shadow-card text-xs font-mono">
        <p className="text-[10px] font-semibold text-slate-400 uppercase mb-2">
          Congestion Status
        </p>
        <div className="space-y-1.5">
          <div className="flex items-center gap-2">
            <span className="w-2.5 h-2.5 rounded-full bg-[#05FFA1] shadow-[0_0_8px_rgba(5,255,161,0.5)]" />
            <span className="text-slate-300">Optimal (&lt;40%)</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="w-2.5 h-2.5 rounded-full bg-[#00E5FF] shadow-[0_0_8px_rgba(0,229,255,0.5)]" />
            <span className="text-slate-300">Moderate (40–67%)</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="w-2.5 h-2.5 rounded-full bg-[#FF9E00] shadow-[0_0_8px_rgba(255,158,0,0.5)]" />
            <span className="text-slate-300">Elevated (68–85%)</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="w-2.5 h-2.5 rounded-full bg-[#FF0055] shadow-[0_0_8px_rgba(255,0,85,0.6)]" />
            <span className="text-slate-300">Critical (&ge;86%)</span>
          </div>
        </div>
      </div>
    </div>
  );
};
