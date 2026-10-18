import React from 'react';
import { MapContainer, TileLayer, CircleMarker, Marker, Popup, Polyline, Tooltip } from 'react-leaflet';
import L from 'leaflet';
import { Station, Train, HorizonPrediction } from '../types';

interface LiveMapProps {
  stations: Station[];
  trains: Train[];
  predictedStations?: HorizonPrediction[] | null;
  activeHorizon: number; // 0 for live, 15, 30, 60, 120
  onSelectStation: (stationId: string) => void;
}

// NYC Subway Line Route Coordinates for visual track polylines
const SUBWAY_TRACK_LINES: { [key: string]: { color: string; coords: [number, number][] } } = {
  "Line 1 (Broadway)": {
    color: "#EE352E",
    coords: [
      [40.7784, -73.9819], // 72 St
      [40.7682, -73.9819], // 59 St
      [40.7552, -73.9871], // Times Sq
      [40.7505, -73.9911], // 34 Penn
      [40.7126, -74.0099], // WTC
    ]
  },
  "Line 4/5/6 (Lexington)": {
    color: "#00933C",
    coords: [
      [40.8041, -73.9376], // Harlem 125
      [40.7794, -73.9556], // 86 St
      [40.7517, -73.9768], // Grand Central
      [40.7358, -73.9906], // Union Sq
      [40.7195, -74.0017], // Canal St
      [40.7103, -74.0076], // Fulton
      [40.7075, -74.0112], // Wall St
      [40.6836, -73.9788], // Atlantic Av
    ]
  },
  "Line 7 (Flushing)": {
    color: "#B933AD",
    coords: [
      [40.7596, -73.8300], // Flushing
      [40.7466, -73.8913], // Roosevelt Av
      [40.7471, -73.9453], // Court Sq
      [40.7517, -73.9768], // Grand Central
      [40.7552, -73.9871], // Times Sq
    ]
  },
  "Line A/C (8th Av)": {
    color: "#0039A6",
    coords: [
      [40.7682, -73.9819], // 59 St
      [40.7505, -73.9911], // 34 Penn
      [40.7103, -74.0076], // Fulton
      [40.6923, -73.9873], // Jay St
    ]
  },
  "Line N/Q/R (Broadway Exp)": {
    color: "#FCCC0A",
    coords: [
      [40.7552, -73.9871], // Times Sq
      [40.7497, -73.9878], // Herald Sq
      [40.7358, -73.9906], // Union Sq
      [40.7195, -74.0017], // Canal St
      [40.6836, -73.9788], // Atlantic Av
      [40.5772, -73.9812], // Coney Island
    ]
  },
  "Line L (Canarsie)": {
    color: "#A7A9AC",
    coords: [
      [40.7358, -73.9906], // Union Sq
      [40.7173, -73.9569], // Bedford Av
    ]
  }
};

const createTrainIcon = (train: Train) => {
  return L.divIcon({
    className: 'custom-train-marker',
    html: `
      <div style="
        background-color: ${train.line_color};
        color: white;
        width: 28px;
        height: 28px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: 800;
        font-size: 13px;
        border: 2px solid white;
        box-shadow: 0 0 10px ${train.line_color};
        cursor: pointer;
        transition: transform 0.3s ease;
      ">
        ${train.line}
      </div>
    `,
    iconSize: [28, 28],
    iconAnchor: [14, 14]
  });
};

export const LiveMap: React.FC<LiveMapProps> = ({
  stations,
  trains,
  predictedStations,
  activeHorizon,
  onSelectStation
}) => {
  // If activeHorizon > 0 and predictions exist, use predicted density
  const getStationMetrics = (s: Station) => {
    if (activeHorizon > 0 && predictedStations) {
      const pred = predictedStations.find(p => p.station_id === s.id);
      if (pred) {
        return {
          density: pred.predicted_density_percent,
          level: pred.congestion_level,
          isPredicted: true,
          headway: pred.recommended_headway_mins
        };
      }
    }
    return {
      density: s.density_percent,
      level: s.congestion_level,
      isPredicted: false,
      headway: null
    };
  };

  const getMarkerColor = (density: number) => {
    if (density >= 85) return '#EF4444'; // Red
    if (density >= 70) return '#F97316'; // Orange
    if (density >= 45) return '#F59E0B'; // Yellow
    return '#10B981'; // Green
  };

  return (
    <div className="relative w-full h-[620px] rounded-2xl overflow-hidden border border-slate-800 shadow-2xl bg-slate-950">
      {/* Real-time / Prediction Horizon Overlay Pill */}
      <div className="absolute top-4 left-4 z-[1000] flex items-center space-x-3 bg-slate-900/90 backdrop-blur-md px-4 py-2 rounded-xl border border-slate-700/80 shadow-lg text-xs font-medium">
        <span className="relative flex h-2.5 w-2.5">
          <span className={`animate-ping absolute inline-flex h-full w-full rounded-full opacity-75 ${activeHorizon === 0 ? 'bg-emerald-400' : 'bg-cyan-400'}`}></span>
          <span className={`relative inline-flex rounded-full h-2.5 w-2.5 ${activeHorizon === 0 ? 'bg-emerald-500' : 'bg-cyan-500'}`}></span>
        </span>
        <span className="text-slate-200">
          {activeHorizon === 0 ? (
            <span className="flex items-center space-x-1.5">
              <strong className="text-emerald-400 font-semibold">LIVE STREAMING</strong>
              <span className="text-slate-400">| NYC Transit Real-Time Feeds</span>
            </span>
          ) : (
            <span className="flex items-center space-x-1.5">
              <strong className="text-cyan-400 font-semibold">AI FORECAST HORIZON:</strong>
              <span className="text-slate-100 font-bold">+{activeHorizon} Minutes</span>
            </span>
          )}
        </span>
      </div>

      {/* Map Legend */}
      <div className="absolute bottom-4 right-4 z-[1000] bg-slate-900/90 backdrop-blur-md p-3 rounded-xl border border-slate-700/80 text-[11px] text-slate-300 shadow-xl space-y-1.5">
        <div className="font-semibold text-slate-400 uppercase tracking-wider mb-1 text-[10px]">
          {activeHorizon === 0 ? 'Live Density' : `Predicted Density (+${activeHorizon}m)`}
        </div>
        <div className="flex items-center space-x-2">
          <span className="w-3 h-3 rounded-full bg-emerald-500 shadow-[0_0_8px_#10B981]"></span>
          <span>Normal (&lt;45%)</span>
        </div>
        <div className="flex items-center space-x-2">
          <span className="w-3 h-3 rounded-full bg-amber-500 shadow-[0_0_8px_#F59E0B]"></span>
          <span>Moderate (45-70%)</span>
        </div>
        <div className="flex items-center space-x-2">
          <span className="w-3 h-3 rounded-full bg-orange-500 shadow-[0_0_8px_#F97316]"></span>
          <span>High Demand (70-85%)</span>
        </div>
        <div className="flex items-center space-x-2">
          <span className="w-3 h-3 rounded-full bg-red-500 shadow-[0_0_8px_#EF4444] animate-pulse"></span>
          <span>Severe / Critical (&gt;85%)</span>
        </div>
      </div>

      <MapContainer
        center={[40.742, -73.965]}
        zoom={12}
        scrollWheelZoom={true}
        style={{ height: '100%', width: '100%', background: '#090d16' }}
      >
        {/* CartoDB Dark Matter Tiles */}
        <TileLayer
          attribution='&copy; <a href="https://carto.com/">CARTO</a>'
          url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
          maxZoom={18}
        />

        {/* Subway Line Route Polylines */}
        {Object.entries(SUBWAY_TRACK_LINES).map(([name, line]) => (
          <Polyline
            key={name}
            positions={line.coords}
            pathOptions={{
              color: line.color,
              weight: 4,
              opacity: 0.65,
              dashArray: '1, 6'
            }}
          />
        ))}

        {/* Station Markers */}
        {stations.map(station => {
          const { density, level, isPredicted, headway } = getStationMetrics(station);
          const color = getMarkerColor(density);
          const radius = Math.max(10, Math.min(22, 10 + (density / 7)));

          return (
            <CircleMarker
              key={station.id}
              center={[station.lat, station.lon]}
              radius={radius}
              pathOptions={{
                color: color,
                fillColor: color,
                fillOpacity: density >= 85 ? 0.9 : 0.7,
                weight: density >= 85 ? 4 : 2,
              }}
              eventHandlers={{
                click: () => onSelectStation(station.id),
              }}
            >
              <Tooltip direction="top" offset={[0, -10]} opacity={0.95}>
                <div className="text-xs font-semibold">
                  {station.name} ({density}%)
                </div>
              </Tooltip>

              <Popup>
                <div className="p-2 min-w-[210px] space-y-2 text-slate-100">
                  <div className="flex items-center justify-between border-b border-slate-700 pb-1.5">
                    <span className="font-bold text-sm text-white">{station.name}</span>
                    <span
                      className="px-2 py-0.5 rounded text-[10px] font-bold uppercase"
                      style={{ backgroundColor: `${color}30`, color: color }}
                    >
                      {level}
                    </span>
                  </div>

                  <div className="text-xs space-y-1 text-slate-300">
                    <div className="flex justify-between">
                      <span className="text-slate-400">Lines:</span>
                      <span className="font-semibold text-slate-200">{station.lines.join(', ')}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-400">{isPredicted ? 'Forecast Density:' : 'Live Density:'}</span>
                      <span className="font-bold" style={{ color: color }}>{density}%</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-400">Current Occupancy:</span>
                      <span className="font-semibold text-slate-200">{station.current_occupancy.toLocaleString()} / {station.capacity.toLocaleString()}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-400">Turnstile Inflow:</span>
                      <span className="font-semibold text-emerald-400">{station.inflow_rate} pass/min</span>
                    </div>
                    {headway && (
                      <div className="flex justify-between pt-1 border-t border-slate-800 text-cyan-400">
                        <span>Rec. Headway:</span>
                        <span className="font-bold">{headway} min</span>
                      </div>
                    )}
                  </div>

                  <button
                    onClick={() => onSelectStation(station.id)}
                    className="w-full mt-2 py-1.5 bg-blue-600 hover:bg-blue-500 text-white rounded-lg text-xs font-semibold transition cursor-pointer shadow-md text-center"
                  >
                    Open Station AI Analytics &rarr;
                  </button>
                </div>
              </Popup>
            </CircleMarker>
          );
        })}

        {/* Live Moving Trains */}
        {trains.map(train => (
          <Marker
            key={train.id}
            position={[train.lat, train.lon]}
            icon={createTrainIcon(train)}
          >
            <Popup>
              <div className="p-2 text-xs space-y-1.5 text-slate-100 min-w-[190px]">
                <div className="flex items-center space-x-2 border-b border-slate-700 pb-1">
                  <span
                    className="w-5 h-5 rounded-full flex items-center justify-center font-bold text-white text-[11px]"
                    style={{ backgroundColor: train.line_color }}
                  >
                    {train.line}
                  </span>
                  <span className="font-bold text-white text-sm">{train.id}</span>
                  <span className={`ml-auto text-[10px] px-1.5 py-0.5 rounded font-semibold ${train.delay_seconds > 0 ? 'bg-amber-500/20 text-amber-400' : 'bg-emerald-500/20 text-emerald-400'}`}>
                    {train.delay_seconds > 0 ? `+${Math.round(train.delay_seconds / 60)}m Delay` : 'On-Time'}
                  </span>
                </div>
                <div className="text-slate-300 space-y-1">
                  <div><strong>From:</strong> {train.from_station_name}</div>
                  <div><strong>To:</strong> {train.to_station_name}</div>
                  <div className="flex justify-between pt-1 border-t border-slate-800">
                    <span className="text-slate-400">Speed: {train.speed_mph} mph</span>
                    <span className="text-slate-400">Occupancy: {train.occupancy_percent}%</span>
                  </div>
                </div>
              </div>
            </Popup>
          </Marker>
        ))}
      </MapContainer>
    </div>
  );
};
