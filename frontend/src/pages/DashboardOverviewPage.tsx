import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import { useWebSocket } from '../hooks/useWebSocket';
import { Badge } from '../components/common/Badge';
import { Card } from '../components/common/Card';
import {
  Radio, Server, AlertTriangle, Users,
  Activity, ArrowRight, MapPin, ShieldAlert
} from 'lucide-react';
import { liveService, FeedHealthSummary } from '../services/liveService';
import {
  mlService, MLSummary, TrafficAnalyticsResponse, MLStationStatus
} from '../services/mlService';
import { alertService, AlertSummary } from '../services/alertService';
import { cachedFetch } from '../services/cache';
import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer
} from 'recharts';

export const DashboardOverviewPage: React.FC = () => {
  const { user } = useAuth();
  const { isConnected } = useWebSocket('/api/v1/ws/events');
  
  const [health, setHealth] = useState<FeedHealthSummary | null>(null);
  const [summary, setSummary] = useState<MLSummary | null>(null);
  const [alertSummary, setAlertSummary] = useState<AlertSummary | null>(null);
  const [traffic, setTraffic] = useState<TrafficAnalyticsResponse | null>(null);
  const [stations, setStations] = useState<MLStationStatus[]>([]);

  useEffect(() => {
    const loadFast = async () => {
      // Wave 1: fast endpoints — serve from cache instantly on re-visit
      try {
        const h = await cachedFetch('dash:health', () => liveService.getHealth(), 30_000, setHealth);
        setHealth(h);
      } catch (e) {
        console.error('Error loading fast dashboard data:', e);
      }
    };

    const loadSlow = async () => {
      // Wave 2: heavier ML endpoints — serve from cache, refresh in background
      try {
        const [s, aSum, tr, st] = await Promise.all([
          cachedFetch('dash:summary',   () => mlService.getSummary(),             60_000, setSummary),
          cachedFetch('dash:alertSum',  () => alertService.getAlertSummary(),     60_000, setAlertSummary),
          cachedFetch('dash:traffic',   () => mlService.getTrafficAnalytics(),    60_000, setTraffic),
          cachedFetch('dash:stations',  () => mlService.getStations(),            60_000,
            fresh => setStations(fresh.sort((a, b) => b.predicted_next_hour - a.predicted_next_hour))),
        ]);
        setSummary(s);
        setAlertSummary(aSum);
        setTraffic(tr);
        setStations(st.sort((a, b) => b.predicted_next_hour - a.predicted_next_hour));
      } catch (e) {
        console.error('Error loading slow dashboard data:', e);
      }
    };

    loadFast().then(() => loadSlow());
    const interval = setInterval(() => loadFast().then(() => loadSlow()), 30000);
    return () => clearInterval(interval);
  }, []);

  const formatTime = (isoString?: string | null) => {
    if (!isoString) return 'Unknown';
    return new Date(isoString).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
  };

  const getRiskBadge = (risk: string) => {
    switch (risk?.toUpperCase()) {
      case 'CRITICAL': return <Badge variant="rose">CRITICAL</Badge>;
      case 'HIGH': return <Badge variant="amber">HIGH</Badge>;
      case 'MODERATE': return <Badge variant="amber">MODERATE</Badge>;
      default: return <Badge variant="emerald">LOW</Badge>;
    }
  };

  return (
    <div className="space-y-6 font-sans pb-10">
      {/* Header */}
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4 p-5 rounded-2xl border border-[#DDD9CF] bg-white shadow-sm">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-extrabold text-[#29322F] tracking-tight">
              SYSTEM OVERVIEW
            </h1>
            <Badge variant={user?.role === 'ADMIN' ? 'cyan' : 'emerald'}>{user?.role}</Badge>
          </div>
          <p className="text-sm text-[#6F8F87] mt-1">
            Transit Operations Command Center • {new Date().toLocaleDateString()}
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          <div className="flex flex-col px-3 py-1.5 rounded-lg bg-[#F7F5EF] border border-[#DDD9CF] text-[11px] shadow-sm">
            <div className="flex items-center gap-1.5">
              <Server className="w-3.5 h-3.5 text-[#4F8A63]" />
              <span className="text-[#6F8F87]">Worker Health:</span>
              <span className={health?.is_live ? 'text-[#4F8A63] font-bold' : 'text-[#C58A3A] font-bold'}>
                {health?.status || 'UNKNOWN'}
              </span>
            </div>
            <div className="text-[#6F8F87] mt-0.5">Last Fetch: {formatTime(health?.feed_timestamp)}</div>
          </div>

          <div className="flex flex-col px-3 py-1.5 rounded-lg bg-[#F7F5EF] border border-[#DDD9CF] text-[11px] shadow-sm">
            <div className="flex items-center gap-1.5">
              <Radio className={`w-3.5 h-3.5 ${isConnected && health?.is_live ? 'text-[#4F8A63] animate-pulse' : 'text-[#C58A3A]'}`} />
              <span className="text-[#6F8F87]">Event Stream:</span>
              <span className={isConnected && health?.is_live ? 'text-[#4F8A63] font-bold' : 'text-[#C58A3A] font-bold'}>
                {isConnected && health?.is_live ? 'LIVE' : 'DISCONNECTED'}
              </span>
            </div>
            <div className="text-[#6F8F87] mt-0.5">Updated: {formatTime(health?.received_at)}</div>
          </div>
        </div>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card className="flex flex-col p-4 border-[#DDD9CF] shadow-sm bg-white hover:border-[#2F6F68]/30 transition-colors">
          <div className="flex justify-between items-start mb-2">
            <div className="p-2 rounded-lg bg-[#F7F5EF] text-[#2F6F68]"><Users className="w-5 h-5" /></div>
            <Badge variant={summary ? 'emerald' : 'slate'}>
              {summary ? 'ACTIVE SYNC' : 'INITIALIZING'}
            </Badge>
          </div>
          <div className="text-xs text-[#6F8F87] uppercase font-bold tracking-wider mb-1">Network Ingress Feed</div>
          <div className="text-xl font-black text-[#29322F]">
            LIVE TELEMETRY
          </div>
          <div className="text-[11px] text-[#6F8F87] mt-1">{summary ? `${summary.total_stations} stations · GTFS-RT` : 'Connecting to feed...'}</div>
        </Card>

        <Card className="flex flex-col p-4 border-[#DDD9CF] shadow-sm bg-white hover:border-[#2F6F68]/30 transition-colors">
          <div className="flex justify-between items-start mb-2">
            <div className="p-2 rounded-lg bg-[#F7F5EF] text-[#2F6F68]"><Activity className="w-5 h-5" /></div>
            <Badge variant="purple">FORECAST</Badge>
          </div>
          <div className="text-xs text-[#6F8F87] uppercase font-bold tracking-wider mb-1">Next-Hour Demand</div>
          <div className="text-2xl font-black text-[#29322F]">
            {summary ? Math.round(summary.next_hour_total_predicted_demand).toLocaleString() : '...'}
          </div>
          <div className="text-[11px] text-[#6F8F87] mt-1">Predicted total passenger volume</div>
        </Card>

        <Card className="flex flex-col p-4 border-[#DDD9CF] shadow-sm bg-white hover:border-[#B9574B]/30 transition-colors">
          <div className="flex justify-between items-start mb-2">
            <div className="p-2 rounded-lg bg-[#F7F5EF] text-[#B9574B]"><ShieldAlert className="w-5 h-5" /></div>
            <Badge variant="rose">RISK</Badge>
          </div>
          <div className="text-xs text-[#6F8F87] uppercase font-bold tracking-wider mb-1">High Risk Stations</div>
          <div className="text-2xl font-black text-[#29322F]">
            {summary ? summary.high_risk_stations_count + summary.critical_risk_stations_count : '...'}
          </div>
          <div className="text-[11px] text-[#B9574B] mt-1 font-medium">
            {summary ? `${summary.critical_risk_stations_count} Critical / ${summary.high_risk_stations_count} High` : '...'}
          </div>
        </Card>

        <Card className="flex flex-col p-4 border-[#DDD9CF] shadow-sm bg-white hover:border-[#C58A3A]/30 transition-colors">
          <div className="flex justify-between items-start mb-2">
            <div className="p-2 rounded-lg bg-[#F7F5EF] text-[#C58A3A]"><AlertTriangle className="w-5 h-5" /></div>
            <Badge variant="amber">EVENTS</Badge>
          </div>
          <div className="text-xs text-[#6F8F87] uppercase font-bold tracking-wider mb-1">Active Alerts</div>
          <div className="text-2xl font-black text-[#29322F]">
            {alertSummary ? alertSummary.total_active : '...'}
          </div>
          <div className="text-[11px] text-[#C58A3A] mt-1 font-medium">
            {alertSummary ? `${alertSummary.overcrowding_count} Crowd / ${alertSummary.live_delays_count} Delay` : '...'}
          </div>
        </Card>
      </div>

      <div className="space-y-6">
        <div className="space-y-6">
          <Card className="border-[#DDD9CF] shadow-sm bg-white p-5">
            <div className="flex justify-between items-center mb-6">
              <div>
                <h2 className="text-base font-bold text-[#29322F] flex items-center gap-2">
                  <Activity className="w-4 h-4 text-[#2F6F68]" />
                  24-Hour Demand Forecast
                </h2>
                <p className="text-[11px] text-[#6F8F87] mt-0.5">Historical observations vs. predicted future passenger volume</p>
              </div>
              <Badge variant={traffic?.data_state?.includes('LIVE') ? 'emerald' : 'purple'}>
                {traffic?.data_state?.includes('LIVE') ? 'LIVE FEED' : (traffic ? 'FORECAST' : 'LOADING')}
              </Badge>
            </div>
            
            <div className="h-64 w-full">
              {traffic && traffic.hourly_patterns.length > 0 ? (
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={traffic.hourly_patterns} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
                    <defs>
                      <linearGradient id="colorObserved" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#4F8A63" stopOpacity={0.3}/>
                        <stop offset="95%" stopColor="#4F8A63" stopOpacity={0}/>
                      </linearGradient>
                      <linearGradient id="colorPredicted" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#6C5CE7" stopOpacity={0.3}/>
                        <stop offset="95%" stopColor="#6C5CE7" stopOpacity={0}/>
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#E5E7EB" />
                    <XAxis 
                      dataKey="hour" 
                      axisLine={false} 
                      tickLine={false} 
                      tick={{ fill: '#6F8F87', fontSize: 11 }}
                      tickFormatter={(hour) => `${hour}:00`}
                    />
                    <YAxis 
                      axisLine={false} 
                      tickLine={false} 
                      tick={{ fill: '#6F8F87', fontSize: 11 }}
                      tickFormatter={(val) => val >= 1000 ? `${(val/1000).toFixed(1)}k` : val}
                    />
                    <Tooltip 
                      contentStyle={{ borderRadius: '8px', border: '1px solid #DDD9CF', fontSize: '12px', color: '#29322F', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }}
                      labelFormatter={(label) => `${label}:00 - ${Number(label)+1}:00`}
                    />
                    <Area type="monotone" dataKey="avg_passenger_count" name="Observed Demand" stroke="#4F8A63" strokeWidth={2} fillOpacity={1} fill="url(#colorObserved)" />
                    <Area type="monotone" dataKey="predicted_avg_count" name="Predicted Demand" stroke="#6C5CE7" strokeWidth={2} strokeDasharray="4 4" fillOpacity={1} fill="url(#colorPredicted)" />
                  </AreaChart>
                </ResponsiveContainer>
              ) : (
                <div className="w-full h-full flex flex-col items-center justify-center text-[#6F8F87] bg-[#F7F5EF] rounded-lg border border-dashed border-[#DDD9CF]">
                  <Activity className="w-8 h-8 opacity-50 mb-2" />
                  <p className="text-sm">Forecast data unavailable</p>
                </div>
              )}
            </div>
          </Card>

          <Card className="border-[#DDD9CF] shadow-sm bg-white p-5">
            <div className="flex justify-between items-center mb-4">
              <div>
                <h2 className="text-base font-bold text-[#29322F] flex items-center gap-2">
                  <MapPin className="w-4 h-4 text-[#2F6F68]" />
                  Priority Station Hotspots
                </h2>
                <p className="text-[11px] text-[#6F8F87] mt-0.5">Top stations by predicted volume and crowd risk</p>
              </div>
              <Link to="/dashboard" className="text-xs font-semibold text-[#2F6F68] hover:underline flex items-center gap-1">
                View All <ArrowRight className="w-3 h-3" />
              </Link>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead>
                  <tr className="border-b border-[#DDD9CF] text-[#6F8F87] text-[11px] uppercase tracking-wider">
                    <th className="pb-2 font-semibold">Station</th>
                    <th className="pb-2 font-semibold text-right">Predicted Demand</th>
                    <th className="pb-2 font-semibold">Risk Level</th>
                    <th className="pb-2 font-semibold">Insight</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#DDD9CF]/50">
                  {stations.slice(0, 5).map(st => (
                    <tr key={st.station_complex_id} className="hover:bg-[#F7F5EF]/50 transition-colors group">
                      <td className="py-3 font-semibold text-[#29322F]">{st.station_complex}</td>
                      <td className="py-3 text-right font-mono text-[#2F6F68]">{Math.round(st.predicted_next_hour).toLocaleString()}</td>
                      <td className="py-3 pl-4">{getRiskBadge(st.crowd_risk)}</td>
                      <td className="py-3 text-[11px] text-[#6F8F87] truncate max-w-[200px]">
                        {st.risk_explanation || 'Nominal traffic expected'}
                      </td>
                    </tr>
                  ))}
                  {stations.length === 0 && (
                    <tr>
                      <td colSpan={4} className="py-6 text-center text-[#6F8F87] text-xs">No station data available</td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </Card>
        </div>
      </div>

      {/* Quick Navigation Footer */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 pt-4 border-t border-[#DDD9CF]">
        <Link to="/dashboard" className="p-3 bg-white border border-[#DDD9CF] rounded-lg shadow-sm hover:border-[#2F6F68] transition-colors flex flex-col">
          <span className="font-semibold text-sm text-[#29322F]">Crowd Intelligence</span>
          <span className="text-[10px] text-[#6F8F87] mt-1">Detailed station analytics</span>
        </Link>
        <Link to="/live-monitoring" className="p-3 bg-white border border-[#DDD9CF] rounded-lg shadow-sm hover:border-[#2F6F68] transition-colors flex flex-col">
          <span className="font-semibold text-sm text-[#29322F]">Live Monitoring</span>
          <span className="text-[10px] text-[#6F8F87] mt-1">Real-time vehicle map</span>
        </Link>
        <Link to="/network" className="p-3 bg-white border border-[#DDD9CF] rounded-lg shadow-sm hover:border-[#2F6F68] transition-colors flex flex-col">
          <span className="font-semibold text-sm text-[#29322F]">Network Analysis</span>
          <span className="text-[10px] text-[#6F8F87] mt-1">Topological disruption impact</span>
        </Link>
        <Link to="/alerts" className="p-3 bg-white border border-[#DDD9CF] rounded-lg shadow-sm hover:border-[#2F6F68] transition-colors flex flex-col">
          <span className="font-semibold text-sm text-[#29322F]">Alerts Center</span>
          <span className="text-[10px] text-[#6F8F87] mt-1">Official MTA service events</span>
        </Link>
      </div>

      <style>{`
        .custom-scrollbar::-webkit-scrollbar { width: 4px; }
        .custom-scrollbar::-webkit-scrollbar-track { background: transparent; }
        .custom-scrollbar::-webkit-scrollbar-thumb { background: #DDD9CF; border-radius: 4px; }
      `}</style>
    </div>
  );
};
