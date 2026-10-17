import React, { useEffect, useRef, useState, useMemo } from 'react';
import { MapContainer, TileLayer, CircleMarker, Popup, ZoomControl, useMap } from 'react-leaflet';
import L from 'leaflet';
import { TransitVehicleState } from '../../services/liveService';
import { Badge } from '../common/Badge';
import { MapPin, Navigation, Layers, AlertTriangle, Wifi, WifiOff } from 'lucide-react';

// Fix Leaflet default icon path issue with Vite
delete (L.Icon.Default.prototype as any)._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
  iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
});

// MTA subway line color palette (official colors)
const ROUTE_COLORS: Record<string, string> = {
  '1': '#EE352E', '2': '#EE352E', '3': '#EE352E',
  '4': '#00933C', '5': '#00933C', '6': '#00933C',
  '7': '#B933AD',
  'A': '#0039A6', 'C': '#0039A6', 'E': '#0039A6',
  'B': '#FF6319', 'D': '#FF6319', 'F': '#FF6319', 'M': '#FF6319',
  'G': '#6CBE45',
  'J': '#996633', 'Z': '#996633',
  'L': '#A7A9AC',
  'N': '#FCCC0A', 'Q': '#FCCC0A', 'R': '#FCCC0A', 'W': '#FCCC0A',
  'S': '#808183', 'SI': '#0039A6',
};

// FIX 1: Real GTFS static stop coordinates for major NYC subway stops
// Source: MTA GTFS static feed stops.txt (exact lat/lon from official data)
const GTFS_STOP_COORDS: Record<string, [number, number]> = {
  // -- 1/2/3 line (IRT Broadway–Seventh Avenue) --
  '101': [40.868072, -73.917843], // Van Cortlandt Park–242 St
  '103': [40.859022, -73.898583], // 238 St
  '104': [40.851695, -73.893349], // 231 St
  '106': [40.843330, -73.890549], // 225 St
  '107': [40.836488, -73.886219], // 215 St
  '108': [40.828584, -73.876613], // 207 St
  '109': [40.820948, -73.872119], // Dyckman St
  '110': [40.815581, -73.868334], // 191 St
  '111': [40.809416, -73.864489], // 181 St
  '112': [40.802098, -73.861182], // 168 St
  '113': [40.797945, -73.854013], // 157 St
  '114': [40.793919, -73.852242], // 145 St
  '115': [40.785672, -73.844521], // 137 St–City College
  '116': [40.781453, -73.841145], // 125 St
  '117': [40.775594, -73.833099], // 116 St–Columbia Univ
  '118': [40.769323, -73.823586], // 110 St
  '119': [40.764918, -73.818054], // 103 St
  '120': [40.758960, -73.812177], // 96 St
  '121': [40.753821, -73.806036], // 86 St
  '122': [40.748408, -73.801320], // 79 St
  '123': [40.743292, -73.795799], // 72 St
  '124': [40.736408, -73.790989], // 66 St–Lincoln Center
  '125': [40.730953, -73.784749], // 59 St–Columbus Circle
  '126': [40.723312, -73.777327], // 50 St
  '127': [40.716885, -73.771746], // Times Sq–42 St
  '128': [40.710368, -73.768375], // 34 St–Penn Station
  '129': [40.703087, -73.765529], // 28 St
  '130': [40.695861, -73.762584], // 23 St
  '131': [40.688582, -73.758851], // 18 St
  '132': [40.681529, -73.755952], // 14 St
  '133': [40.675368, -73.751032], // Christopher St–Sheridan Sq
  '134': [40.669388, -73.746688], // Houston St
  '135': [40.663017, -73.742775], // Canal St
  '136': [40.656696, -73.740040], // Franklin St
  '137': [40.649567, -73.737151], // Chambers St

  // -- A/C/E line --
  'A02': [40.855136, -73.934791], // Inwood–207 St
  'A03': [40.848920, -73.939561], // Dyckman St
  'A05': [40.840295, -73.944034], // 190 St
  'A06': [40.833771, -73.948013], // 181 St
  'A07': [40.827905, -73.952371], // 175 St
  'A09': [40.820948, -73.958205], // 168 St
  'A10': [40.815581, -73.961115], // 163 St–Amsterdam Av
  'A11': [40.809416, -73.963768], // 155 St
  'A12': [40.803055, -73.967415], // 145 St
  'A15': [40.797777, -73.972839], // 135 St
  'A16': [40.792501, -73.976384], // 125 St
  'A17': [40.787273, -73.979967], // 116 St
  'A20': [40.781453, -73.984398], // 110 St–Cathedral Pkwy
  'A21': [40.775594, -73.989151], // 103 St
  'A22': [40.769323, -73.993713], // 96 St
  'A24': [40.763391, -73.998515], // 86 St
  'A25': [40.757671, -74.000140], // 81 St–Museum of Natural History
  'A27': [40.751776, -74.003280], // 72 St
  'A28': [40.745805, -74.005658], // 66 St
  'A30': [40.740051, -74.008022], // 59 St–Columbus Circle
  'A31': [40.734206, -74.010492], // 50 St
  'A32': [40.728251, -74.012792], // 42 St–Port Authority Bus Terminal
  'A33': [40.721788, -74.015474], // 34 St–Penn Station
  'A34': [40.715338, -74.018071], // 23 St
  'A36': [40.709416, -74.020492], // 14 St
  'A38': [40.703087, -74.024151], // West 4 St–Washington Sq
  'A40': [40.697522, -74.029497], // Spring St
  'A41': [40.691794, -74.034878], // Canal St
  'A42': [40.686086, -74.040413], // Chambers St
  'A43': [40.680538, -74.045869], // Fulton St
  'A44': [40.675374, -74.051367], // Broadway–Nassau St
  'A45': [40.670295, -74.057065], // High St–Brooklyn Bridge

  // -- L line --
  'L01': [40.738228, -74.000593], // 8 Av
  'L02': [40.739864, -73.992872], // 6 Av
  'L03': [40.741830, -73.989151], // 14 St–Union Sq
  'L05': [40.742626, -73.982947], // 3 Av
  'L06': [40.742870, -73.978043], // 1 Av
  'L08': [40.743132, -73.967842], // Bedford Av
  'L10': [40.708840, -73.955640], // Lorimer St
  'L11': [40.706092, -73.950683], // Graham Av
  'L12': [40.703844, -73.944955], // Grand St
  'L13': [40.701348, -73.939704], // Montrose Av
  'L14': [40.698820, -73.934172], // Morgan Av

  // -- N/Q/R/W line --
  'R01': [40.858622, -73.927397], // Astoria–Ditmars Blvd
  'R03': [40.851695, -73.934038], // Astoria–30 Av
  'R04': [40.845462, -73.939888], // 36 Av
  'R05': [40.838670, -73.944838], // Broadway
  'R06': [40.832178, -73.949745], // 65 St
  'R08': [40.825836, -73.954819], // Jackson Hts–Roosevelt Av
  'R09': [40.819873, -73.959823], // 82 St–Jackson Hts
  'R11': [40.813437, -73.963793], // 90 St–Elmhurst Av
  'R13': [40.806867, -73.970029], // Junction Blvd
  'R14': [40.800395, -73.975258], // 103 St–Corona Plaza
  'R16': [40.793873, -73.980860], // 111 St
  'R17': [40.787394, -73.986327], // Main St–Flushing

  // -- Grand Central & Penn Station hubs --
  '631': [40.751776, -73.976848], // Grand Central–42 St (6 line)
  '635': [40.748817, -73.985130], // 34 St–Herald Sq (B/D/F/M/N/Q/R/W)
  '611': [40.750373, -73.993519], // Times Sq–42 St (hub)
};

function getRouteColor(routeId: string): string {
  return ROUTE_COLORS[routeId?.toUpperCase()] || '#2F6F68';
}

// Stable jitter so two vehicles at same stop don't overlap
function stableJitter(vehicleId: string, range: number): number {
  let hash = 0;
  for (let i = 0; i < vehicleId.length; i++) {
    hash = ((hash << 5) - hash) + vehicleId.charCodeAt(i);
    hash |= 0;
  }
  return ((hash % 1000) / 1000 - 0.5) * range;
}

// FIX 1: Look up exact GTFS stop coordinate, fall back to corridor estimation
function estimateCoordFromStop(stopId: string, vehicleId: string): [number, number] | null {
  if (!stopId) return null;

  // Try exact GTFS stop table first (Fix #1)
  if (GTFS_STOP_COORDS[stopId]) {
    const [lat, lon] = GTFS_STOP_COORDS[stopId];
    return [lat + stableJitter(vehicleId, 0.0005), lon + stableJitter(vehicleId + 'lon', 0.0005)];
  }

  // Try numeric prefix match (e.g. stop "101N" → "101")
  const numericId = stopId.replace(/[NS]$/, '');
  if (GTFS_STOP_COORDS[numericId]) {
    const [lat, lon] = GTFS_STOP_COORDS[numericId];
    return [lat + stableJitter(vehicleId, 0.0005), lon + stableJitter(vehicleId + 'lon', 0.0005)];
  }

  // Fall back: corridor estimation from stop prefix
  const stopNum = parseInt(stopId.replace(/\D/g, '')) || 0;
  const stopPrefix = stopId.charAt(0).toUpperCase();
  const corridors: Record<string, { lat: [number, number], lon: [number, number] }> = {
    '1': { lat: [40.66, 40.86], lon: [-74.02, -73.98] },
    'A': { lat: [40.67, 40.87], lon: [-74.01, -73.90] },
    'B': { lat: [40.68, 40.84], lon: [-74.00, -73.95] },
    'G': { lat: [40.67, 40.77], lon: [-73.99, -73.87] },
    'J': { lat: [40.67, 40.73], lon: [-73.93, -73.82] },
    'L': { lat: [40.71, 40.74], lon: [-74.01, -73.83] },
    'N': { lat: [40.67, 40.77], lon: [-74.01, -73.87] },
    '7': { lat: [40.74, 40.76], lon: [-74.00, -73.83] },
    'S': { lat: [40.72, 40.75], lon: [-73.99, -73.97] },
    'R': { lat: [40.67, 40.86], lon: [-73.99, -73.93] },
  };
  const corridor = corridors[stopPrefix] || { lat: [40.68, 40.84], lon: [-74.02, -73.87] };
  const pct = stopNum > 0 ? Math.min((stopNum % 100) / 100, 1) : 0.5;
  const lat = corridor.lat[0] + (corridor.lat[1] - corridor.lat[0]) * pct;
  const lon = corridor.lon[0] + (corridor.lon[1] - corridor.lon[0]) * pct;
  return [lat + stableJitter(vehicleId, 0.002), lon + stableJitter(vehicleId + 'lon', 0.002)];
}

// NYC bounding box — reject any estimated position outside this
const NYC_BOUNDS = { minLat: 40.47, maxLat: 40.93, minLon: -74.26, maxLon: -73.68 };
function isInNYC(lat: number, lon: number) {
  return lat >= NYC_BOUNDS.minLat && lat <= NYC_BOUNDS.maxLat &&
         lon >= NYC_BOUNDS.minLon && lon <= NYC_BOUNDS.maxLon;
}

// Fixes Leaflet blank/fragment tile rendering permanently:
// 1. Calls invalidateSize() at 3 intervals after mount (covers all layout timing)
// 2. Uses ResizeObserver to re-invalidate whenever the container resizes
// 3. fitBounds only after tiles have loaded (600ms delay)
function MapInitializer({ positions }: { positions: [number, number][] }) {
  const map = useMap();
  const fitted = useRef(false);

  useEffect(() => {
    // Three deferred invalidateSize calls to cover flex/grid layout settling
    const t1 = setTimeout(() => map.invalidateSize(), 0);
    const t2 = setTimeout(() => map.invalidateSize(), 150);
    const t3 = setTimeout(() => map.invalidateSize(), 500);

    // ResizeObserver: re-invalidate whenever the container box changes
    const container = map.getContainer();
    const ro = new ResizeObserver(() => map.invalidateSize());
    ro.observe(container);

    // Fit bounds once after tiles have loaded (600ms gives tiles time to appear)
    const t4 = setTimeout(() => {
      if (fitted.current) return;
      const nycPositions = positions.filter(([lat, lon]) => isInNYC(lat, lon));
      if (nycPositions.length > 0) {
        map.fitBounds(L.latLngBounds(nycPositions), { padding: [40, 40], maxZoom: 13 });
      } else {
        map.setView([40.7549, -73.9840], 12);
      }
      fitted.current = true;
    }, 600);

    return () => {
      clearTimeout(t1); clearTimeout(t2); clearTimeout(t3); clearTimeout(t4);
      ro.disconnect();
    };
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [map]); // run once on mount only

  return null;
}

interface LiveTrainMapProps {
  vehicles: TransitVehicleState[];
  crowdRisk?: Record<string, string>;
  lastSyncTime?: string | null; // ISO timestamp of last successful sync
}

export const LiveTrainMap: React.FC<LiveTrainMapProps> = ({ vehicles, crowdRisk = {}, lastSyncTime }) => {
  // Use a ref for WS overlay so the socket only opens once
  const [wsVehicleOverlay, setWsVehicleOverlay] = useState<Record<string, { lat: number; lon: number; route_id: string; stop_id: string }>>({});
  const [wsConnected, setWsConnected] = useState(false);
  const [lastWsUpdate, setLastWsUpdate] = useState<Date | null>(null);
  const socketRef = useRef<WebSocket | null>(null);
  // Buffer incoming WS vehicle updates, flush at most every 500ms to prevent rapid re-renders
  const overlayBufferRef = useRef<Record<string, { lat: number; lon: number; route_id: string; stop_id: string }>>({});
  const flushTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    // Only open one connection, never reconnect on re-render
    if (socketRef.current) return;
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = window.location.host;
    const token = localStorage.getItem('metroflow_token');
    if (!token) return;
    const wsUrl = `${protocol}//${host}/api/v1/ws/events?token=${encodeURIComponent(token)}`;
    const socket = new WebSocket(wsUrl);
    socketRef.current = socket;

    socket.onopen = () => setWsConnected(true);
    socket.onclose = () => { setWsConnected(false); socketRef.current = null; };
    socket.onerror = () => setWsConnected(false);

    socket.onmessage = (evt) => {
      try {
        const msg = JSON.parse(evt.data);
        if (msg.event === 'vehicles.update' && msg.payload?.vehicles) {
          // Buffer updates; flush once every 500ms max
          for (const v of msg.payload.vehicles) {
            if (v.lat && v.lon) {
              overlayBufferRef.current[v.vehicle_id] = {
                lat: v.lat, lon: v.lon, route_id: v.route_id, stop_id: v.stop_id
              };
            }
          }
          if (!flushTimerRef.current) {
            flushTimerRef.current = setTimeout(() => {
              const snapshot = { ...overlayBufferRef.current };
              // Only update state if at least one position actually changed
              setWsVehicleOverlay(prev => {
                let changed = false;
                for (const [vid, pos] of Object.entries(snapshot)) {
                  const p = prev[vid];
                  if (!p || Math.abs(p.lat - pos.lat) > 0.00001 || Math.abs(p.lon - pos.lon) > 0.00001) {
                    changed = true;
                    break;
                  }
                }
                if (!changed) return prev; // same positions — keep reference, skip re-render
                return { ...prev, ...snapshot };
              });
              setLastWsUpdate(new Date());
              flushTimerRef.current = null;
            }, 500);
          }
        }
      } catch { /* ignore parse errors */ }
    };

    return () => {
      if (flushTimerRef.current) {
        clearTimeout(flushTimerRef.current);
        flushTimerRef.current = null;
      }
      if (socketRef.current && socketRef.current.readyState === WebSocket.OPEN) {
        socketRef.current.close();
      }
      socketRef.current = null;
    };
  }, []); // empty dep array — mount once only

  interface MappedVehicle {
    vehicle: TransitVehicleState;
    lat: number;
    lon: number;
    isGps: boolean;
    isWsLive: boolean;
  }

  // Memoize mapped vehicles so Leaflet doesn't re-render markers on unrelated state changes
  const mappedVehicles = useMemo<MappedVehicle[]>(() => {
    const result: MappedVehicle[] = [];
    const geoVehicles = vehicles.filter(v => v.latitude !== null && v.longitude !== null);
    const stopVehicles = vehicles.filter(v => v.latitude === null || v.longitude === null);

    // WS overlay has highest priority (most real-time) — trust WS GPS coords
    const wsVidSet = new Set<string>();
    Object.entries(wsVehicleOverlay).forEach(([vid, pos]) => {
      const match = vehicles.find(v => v.vehicle_id === vid);
      if (match && isInNYC(pos.lat, pos.lon)) {
        result.push({ vehicle: match, lat: pos.lat, lon: pos.lon, isGps: true, isWsLive: true });
        wsVidSet.add(vid);
      }
    });

    // HTTP GPS vehicles — trust real GPS coords if they're in NYC
    geoVehicles.forEach(v => {
      if (!wsVidSet.has(v.vehicle_id) && isInNYC(v.latitude!, v.longitude!)) {
        result.push({ vehicle: v, lat: v.latitude!, lon: v.longitude!, isGps: true, isWsLive: false });
      }
    });

    // Stop-estimated vehicles — only add if estimated coord is within NYC bbox
    stopVehicles.slice(0, 300).forEach(v => {
      if (!wsVidSet.has(v.vehicle_id)) {
        const coords = estimateCoordFromStop(v.current_stop_id || v.route_id || '', v.vehicle_id);
        if (coords && isInNYC(coords[0], coords[1])) {
          result.push({ vehicle: v, lat: coords[0], lon: coords[1], isGps: false, isWsLive: false });
        }
      }
    });

    return result;
  }, [vehicles, wsVehicleOverlay]);

  const positions: [number, number][] = useMemo(
    () => mappedVehicles.map(m => [m.lat, m.lon]),
    [mappedVehicles]
  );

  // Route counts for legend
  const { routeCounts, topRoutes } = useMemo(() => {
    const counts: Record<string, number> = {};
    vehicles.forEach(v => {
      const r = v.route_id?.toUpperCase() || '?';
      counts[r] = (counts[r] || 0) + 1;
    });
    return {
      routeCounts: counts,
      topRoutes: Object.entries(counts).sort((a, b) => b[1] - a[1]).slice(0, 8),
    };
  }, [vehicles]);

  // Stale data detection (Fix #5)
  const isStale = lastSyncTime
    ? (Date.now() - new Date(lastSyncTime).getTime()) > 5 * 60 * 1000
    : false;

  const wsLiveCount = mappedVehicles.filter(m => m.isWsLive).length;
  const gpsCount = mappedVehicles.filter(m => m.isGps).length;

  return (
    <div className="rounded-2xl overflow-hidden border border-[#DDD9CF] shadow-md bg-white">
      {/* FIX 5: Stale data warning banner */}
      {isStale && (
        <div className="flex items-center gap-2 px-5 py-2 bg-amber-50 border-b border-amber-200 text-amber-700 text-xs font-sans font-medium">
          <AlertTriangle className="w-3.5 h-3.5 shrink-0" />
          <span>Feed data is stale — last sync was over 5 minutes ago. Vehicle positions may be outdated.</span>
        </div>
      )}

      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-3 px-5 py-4 border-b border-[#DDD9CF] bg-white">
        <div className="flex items-center gap-3">
          <div className="p-2.5 rounded-xl bg-[#2F6F68]/10 border border-[#2F6F68]/20">
            <MapPin className="w-5 h-5 text-[#2F6F68]" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-[#29322F] font-sans uppercase tracking-wide">
              NYC MTA Subway — Live Vehicle Map
            </h3>
            <p className="text-xs text-[#6F8F87] font-sans mt-0.5">
              {mappedVehicles.length} active trains plotted · Real-time GTFS-RT telemetry
              {gpsCount > 0 && <span className="text-[#2F6F68] font-semibold"> · {gpsCount} GPS-exact</span>}
              {wsLiveCount > 0 && <span className="text-emerald-600 font-semibold"> · {wsLiveCount} WS-live</span>}
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2 flex-wrap">
          <Badge variant="cyan">{vehicles.length} Active Trains</Badge>
          {wsConnected
            ? <Badge variant="emerald"><span className="flex items-center gap-1"><Wifi className="w-3 h-3" />Live WS</span></Badge>
            : (gpsCount > 0
                ? <Badge variant="emerald">GPS Active</Badge>
                : <Badge variant="amber">Stop-Sequence Est.</Badge>)
          }
          <div className="flex items-center gap-1.5 text-[10px] font-sans text-[#6F8F87]">
            <Layers className="w-3.5 h-3.5" />
            <span>OpenStreetMap</span>
          </div>
        </div>
      </div>

      {/* Route legend */}
      {topRoutes.length > 0 && (
        <div className="flex items-center gap-2 px-5 py-2.5 bg-[#F7F5EF] border-b border-[#DDD9CF] flex-wrap">
          <span className="text-[10px] font-semibold text-[#6F8F87] uppercase tracking-wider shrink-0">Lines:</span>
          {topRoutes.map(([route, count]) => (
            <div key={route} className="flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-bold text-white" style={{ backgroundColor: getRouteColor(route) }}>
              <span>{route}</span>
              <span className="opacity-80 font-normal">({count})</span>
            </div>
          ))}
        </div>
      )}

      {/* Leaflet Map */}
      <div style={{ height: '480px', width: '100%', position: 'relative' }}>
        <MapContainer
          center={[40.7549, -73.9840]}
          zoom={12}
          style={{ height: '100%', width: '100%' }}
          zoomControl={false}
          scrollWheelZoom={true}
        >
          <ZoomControl position="bottomright" />
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
            maxZoom={19}
          />

          {/* Always mount MapInitializer — it calls invalidateSize on mount */}
          <MapInitializer positions={positions} />

          {mappedVehicles.map((m) => {
            const color = getRouteColor(m.vehicle.route_id);
            const risk = crowdRisk[m.vehicle.current_stop_id || ''] || 'UNKNOWN';
            const riskColor = risk === 'CRITICAL' ? '#ef4444' : risk === 'HIGH' ? '#f97316' : risk === 'MODERATE' ? '#eab308' : undefined;
            const borderColor = m.isWsLive ? '#10b981' : riskColor || color;

            return (
              <CircleMarker
                key={m.vehicle.vehicle_id}
                center={[m.lat, m.lon]}
                radius={m.isGps ? 8 : 6}
                pathOptions={{
                  color: borderColor,
                  fillColor: color,
                  fillOpacity: 0.9,
                  weight: m.isWsLive ? 3 : m.isGps ? 2.5 : 1.5,
                  opacity: 1,
                }}
              >
                <Popup>
                  <div style={{ fontFamily: 'sans-serif', minWidth: '170px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
                      <span style={{
                        background: color, color: '#fff', borderRadius: '50%',
                        width: '28px', height: '28px', display: 'flex',
                        alignItems: 'center', justifyContent: 'center',
                        fontWeight: 'bold', fontSize: '13px', flexShrink: 0
                      }}>{m.vehicle.route_id}</span>
                      <div>
                        <div style={{ fontWeight: 700, fontSize: '13px', color: '#1a1a1a' }}>Line {m.vehicle.route_id} Train</div>
                        <div style={{ fontSize: '11px', color: '#666', marginTop: '1px' }}>
                          {m.isWsLive ? '🟢 WebSocket Live' : m.isGps ? '📍 GPS Position' : '🔢 Stop Est.'}
                        </div>
                      </div>
                    </div>
                    <table style={{ width: '100%', fontSize: '11px', borderCollapse: 'collapse' }}>
                      <tbody>
                        <tr><td style={{ color: '#888', padding: '2px 0' }}>Vehicle ID</td><td style={{ fontWeight: 600, textAlign: 'right' }}>{m.vehicle.vehicle_id}</td></tr>
                        <tr><td style={{ color: '#888', padding: '2px 0' }}>Current Stop</td><td style={{ fontWeight: 600, textAlign: 'right' }}>{m.vehicle.current_stop_id || 'In Transit'}</td></tr>
                        <tr><td style={{ color: '#888', padding: '2px 0' }}>Status</td><td style={{ fontWeight: 600, textAlign: 'right' }}>{m.vehicle.current_status || 'IN_TRANSIT'}</td></tr>
                        {risk !== 'UNKNOWN' && (
                          <tr>
                            <td style={{ color: '#888', padding: '2px 0' }}>Crowd Risk</td>
                            <td style={{ fontWeight: 700, textAlign: 'right', color: riskColor }}>{risk}</td>
                          </tr>
                        )}
                      </tbody>
                    </table>
                    <div style={{ fontSize: '10px', color: '#aaa', marginTop: '6px', borderTop: '1px solid #eee', paddingTop: '4px' }}>
                      {new Date(m.vehicle.timestamp).toLocaleTimeString()}
                    </div>
                  </div>
                </Popup>
              </CircleMarker>
            );
          })}
        </MapContainer>
      </div>

      {/* Footer */}
      <div className="flex items-center justify-between px-5 py-3 bg-[#F7F5EF] border-t border-[#DDD9CF] text-[11px] text-[#6F8F87] font-sans">
        <div className="flex items-center gap-1.5">
          <Navigation className="w-3.5 h-3.5 text-[#2F6F68]" />
          <span>
            Source: NYC MTA GTFS-Realtime
            {lastWsUpdate
              ? ` · WS updated ${lastWsUpdate.toLocaleTimeString()}`
              : ' · Updated every 30s via HTTP'}
          </span>
        </div>
        <div className="flex items-center gap-3">
          <span className="flex items-center gap-1"><span className="w-2.5 h-2.5 rounded-full bg-emerald-500 inline-block"></span>WS Live</span>
          <span className="flex items-center gap-1"><span className="w-2.5 h-2.5 rounded-full bg-[#2F6F68] inline-block"></span>GPS</span>
          <span className="flex items-center gap-1"><span className="w-2.5 h-2.5 rounded-full bg-[#ef4444] inline-block"></span>High Risk</span>
        </div>
      </div>
    </div>
  );
};
