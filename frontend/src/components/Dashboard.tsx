import React, { useState, useEffect } from 'react';

const API_BASE = "http://localhost:8000";

interface DashboardProps {
  onLogout?: () => void;
}

type TabType = 
  | 'dashboard' 
  | 'monitoring' 
  | 'trains' 
  | 'schedules' 
  | 'alerts' 
  | 'analytics' 
  | 'settings';

export const Dashboard: React.FC<DashboardProps> = ({ onLogout }) => {
  const [activeTab, setActiveTab] = useState<TabType>('dashboard');
  const [networkData, setNetworkData] = useState<any>(null);
  const [scheduleData, setScheduleData] = useState<any>(null);
  const [alertActive, setAlertActive] = useState<boolean>(false);
  const [announcementText, setAnnouncementText] = useState<string>('');
  
  // Real-time ticking system clock
  const [currentTime, setCurrentTime] = useState<string>(new Date().toLocaleTimeString());
  const [livePackets, setLivePackets] = useState<number>(31817);

  // User Profile Dropdown Menu State
  const [showProfileMenu, setShowProfileMenu] = useState<boolean>(false);

  // External Integration Dispatch State
  const [dispatchResult, setDispatchResult] = useState<any>(null);
  const [isDispatching, setIsDispatching] = useState<boolean>(false);

  // OCC Settings Config State
  const [refreshInterval, setRefreshInterval] = useState<number>(3);
  const [congestionThreshold, setCongestionThreshold] = useState<number>(60);
  const [autoDispatch, setAutoDispatch] = useState<boolean>(true);

  // Live AI Simulator states
  const [simStation, setSimStation] = useState<string>("Tech Hub Junction");
  const [simHour, setSimHour] = useState<number>(new Date().getHours());
  const [simCondition, setSimCondition] = useState<string>("NORMAL");
  const [aiOutput, setAiOutput] = useState<any>({
    predictedInflow: 68,
    predictedDensity: 76,
    riskLevel: 'HIGH',
    headwayAction: 'Shorten headway from 5.0m to 2.8m immediately',
    confidence: '96.2%',
    fleetRecommendation: 'Deploy 2 standby rakes into active corridor'
  });

  // Ticking clock effect & packet streaming counter
  useEffect(() => {
    const clockTimer = setInterval(() => {
      setCurrentTime(new Date().toLocaleTimeString());
      setLivePackets(prev => prev + Math.floor(Math.random() * 8) + 3);
    }, 1000);
    return () => clearInterval(clockTimer);
  }, []);

  const fetchTelemetry = async () => {
    try {
      const [mapRes, schedRes] = await Promise.all([
        fetch(`${API_BASE}/api/network/map`),
        fetch(`${API_BASE}/api/schedule/dispatch`)
      ]);

      if (mapRes.ok && schedRes.ok) {
        const mapJson = await mapRes.json();
        const schedJson = await schedRes.json();
        setNetworkData(mapJson);
        setScheduleData(schedJson);
      }
    } catch (err) {
      console.error("Live streaming connection error:", err);
    }
  };

  useEffect(() => {
    fetchTelemetry();
    const timer = setInterval(fetchTelemetry, refreshInterval * 1000);
    return () => clearInterval(timer);
  }, [refreshInterval]);

  // Handle Live Integration Broadcast (Email, SMS, Push, PA System)
  const handleBroadcastAlert = async (customMsg?: string) => {
    const msgToSend = customMsg || announcementText;
    if (!msgToSend.trim()) return;

    setIsDispatching(true);
    try {
      const res = await fetch(`${API_BASE}/api/integrations/dispatch-alert`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          station_id: "ALL_STATIONS",
          priority: alertActive ? "CRITICAL" : "HIGH",
          message: msgToSend,
          channels: ["EMAIL", "SMS", "PUSH_NOTIFICATION", "PUBLIC_ADDRESS"]
        })
      });

      if (res.ok) {
        const data = await res.json();
        setDispatchResult(data);
        if (!customMsg) setAnnouncementText('');
      }
    } catch (err) {
      console.error("Error dispatching alert:", err);
    } finally {
      setIsDispatching(false);
    }
  };

  const stationsList = networkData?.stations || [
    { id: "ST-01", code: 150, name: "Central Terminal", line: "Blue Corridor", x: 120, y: 140, inflow_per_min: 36, outflow_per_min: 30, density_pct: 42, status: "NORMAL" },
    { id: "ST-02", code: 151, name: "City Hall Core", line: "Blue Corridor", x: 220, y: 140, inflow_per_min: 44, outflow_per_min: 38, density_pct: 51, status: "NORMAL" },
    { id: "ST-03", code: 222, name: "Tech Hub Junction", line: "Interchange", x: 340, y: 140, inflow_per_min: 74, outflow_per_min: 58, density_pct: 82, status: "CRITICAL" },
    { id: "ST-04", code: 216, name: "Cyber Gateway", line: "Interchange", x: 460, y: 140, inflow_per_min: 58, outflow_per_min: 46, density_pct: 68, status: "ELEVATED" },
    { id: "ST-05", code: 230, name: "Financial District", line: "Blue Corridor", x: 580, y: 140, inflow_per_min: 66, outflow_per_min: 52, density_pct: 74, status: "ELEVATED" },
    { id: "ST-06", code: 231, name: "Riverside Plaza", line: "Blue Corridor", x: 700, y: 140, inflow_per_min: 28, outflow_per_min: 24, density_pct: 32, status: "NORMAL" },
    { id: "ST-07", code: 234, name: "South Port", line: "Emerald Express", x: 120, y: 240, inflow_per_min: 34, outflow_per_min: 28, density_pct: 38, status: "NORMAL" },
    { id: "ST-08", code: 239, name: "Market Square", line: "Emerald Express", x: 240, y: 240, inflow_per_min: 49, outflow_per_min: 42, density_pct: 54, status: "NORMAL" },
    { id: "ST-09", code: 240, name: "University Park", line: "Emerald Express", x: 360, y: 240, inflow_per_min: 42, outflow_per_min: 36, density_pct: 46, status: "NORMAL" },
    { id: "ST-10", code: 241, name: "Olympic Stadium", line: "Emerald Express", x: 480, y: 240, inflow_per_min: 32, outflow_per_min: 28, density_pct: 35, status: "NORMAL" },
    { id: "ST-11", code: 242, name: "West Interchange", line: "Ruby Loop", x: 600, y: 240, inflow_per_min: 39, outflow_per_min: 32, density_pct: 44, status: "NORMAL" },
    { id: "ST-12", code: 243, name: "Innovation Campus", line: "Ruby Loop", x: 720, y: 240, inflow_per_min: 52, outflow_per_min: 44, density_pct: 58, status: "NORMAL" }
  ];

  const schedulesList = scheduleData?.schedules || [
    {
      corridor: "Blue Corridor (Line 1)",
      code: "LINE-01",
      current_headway: "5.0m",
      recommended_headway: "3.0m",
      status: "HIGH_DEMAND",
      peak_forecast_per_hr: 412,
      activeTrains: 8,
      standbyReady: 2,
      bottleneckStation: "Tech Hub Junction"
    },
    {
      corridor: "Emerald Express (Line 2)",
      code: "LINE-02",
      current_headway: "6.5m",
      recommended_headway: "5.0m",
      status: "BALANCED",
      peak_forecast_per_hr: 258,
      activeTrains: 6,
      standbyReady: 1,
      bottleneckStation: "Market Square"
    },
    {
      corridor: "Ruby Loop (Line 3)",
      code: "LINE-03",
      current_headway: "8.0m",
      recommended_headway: "7.0m",
      status: "BALANCED",
      peak_forecast_per_hr: 198,
      activeTrains: 4,
      standbyReady: 1,
      bottleneckStation: "West Interchange"
    }
  ];

  const navItems: { id: TabType; label: string; icon: string }[] = [
    { id: 'dashboard', label: 'Live Operations', icon: '📡' },
    { id: 'monitoring', label: 'Real-Time Ingestion', icon: '⚡' },
    { id: 'trains', label: 'GPS Fleet Tracking', icon: '🚆' },
    { id: 'schedules', label: 'Dynamic Headway AI', icon: '⏱️' },
    { id: 'alerts', label: 'Multi-Channel Alerts', icon: '🔔' },
    { id: 'analytics', label: 'Live AI Demand Engine', icon: '🧠' },
    { id: 'settings', label: 'Stream Config', icon: '⚙️' }
  ];

  const runAiInference = () => {
    let baseInflow = 28;
    if (simHour >= 7 && simHour <= 10) baseInflow = 68;
    else if (simHour >= 17 && simHour <= 20) baseInflow = 74;
    else if (simHour >= 12 && simHour <= 14) baseInflow = 44;

    if (simStation.includes("Tech Hub") || simStation.includes("Financial")) {
      baseInflow += 16;
    }

    if (simCondition === "WEATHER_RAIN") baseInflow = Math.round(baseInflow * 1.25);
    if (simCondition === "EVENT_SURGE") baseInflow = Math.round(baseInflow * 1.45);

    const density = Math.min(98, Math.round(baseInflow * 1.12));
    let risk = 'LOW';
    let headway = 'Maintain nominal headway (5.0m)';
    let fleet = 'Nominal fleet operations; regular rotation';

    if (density >= 80) {
      risk = 'CRITICAL';
      headway = 'Immediate headway compression to 2.0m + turnstile metering';
      fleet = 'Inject 3 emergency express trainsets immediately';
    } else if (density >= 60) {
      risk = 'HIGH';
      headway = 'Shorten headway to 2.8m - 3.2m';
      fleet = 'Deploy 2 standby rakes into active corridor';
    } else if (density >= 40) {
      risk = 'MODERATE';
      headway = 'Adjust headway to 4.0m';
      fleet = 'Prepare standby trainset on siding track';
    }

    setAiOutput({
      predictedInflow: baseInflow,
      predictedDensity: density,
      riskLevel: risk,
      headwayAction: headway,
      confidence: '96.2%',
      fleetRecommendation: fleet
    });
  };

  const hourlyCurve = [
    { hour: "06:00", riders: 22, peak: false },
    { hour: "07:00", riders: 52, peak: false },
    { hour: "08:00", riders: 92, peak: true },
    { hour: "09:00", riders: 97, peak: true },
    { hour: "10:00", riders: 68, peak: false },
    { hour: "11:00", riders: 40, peak: false },
    { hour: "12:00", riders: 56, peak: false },
    { hour: "13:00", riders: 48, peak: false },
    { hour: "14:00", riders: 38, peak: false },
    { hour: "15:00", riders: 46, peak: false },
    { hour: "16:00", riders: 62, peak: false },
    { hour: "17:00", riders: 88, peak: true },
    { hour: "18:00", riders: 99, peak: true },
    { hour: "19:00", riders: 84, peak: true },
    { hour: "20:00", riders: 50, peak: false },
    { hour: "21:00", riders: 30, peak: false },
    { hour: "22:00", riders: 18, peak: false }
  ];

  return (
    <div className="min-h-screen bg-slate-50 text-slate-800 font-sans flex flex-col">
      {/* Header Bar */}
      <header className="bg-white border-b border-emerald-100 shadow-sm sticky top-0 z-40">
        <div className="max-w-7xl mx-auto px-6 py-3 flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          
          {/* Left: Logo & Title */}
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-xl bg-emerald-600 flex items-center justify-center text-white shadow-md shadow-emerald-600/20 font-black text-xl">
              M
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <h1 className="text-xl font-extrabold text-slate-900 tracking-tight">
                  METRO<span className="text-emerald-600">FLOW</span>
                </h1>
                <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-emerald-500 text-white animate-pulse">
                  LIVE TELEMETRY
                </span>
              </div>
              <p className="text-xs text-slate-500 font-medium">Real-Time Transit Ingestion & Automated Dynamic Headway Dispatch</p>
            </div>
          </div>

          {/* Center: Prominent Real-Time OCC Clock */}
          <div className="hidden lg:flex flex-col items-center justify-center bg-slate-900 text-emerald-400 px-5 py-1.5 rounded-2xl shadow-inner border border-slate-800">
            <span className="text-[9px] uppercase tracking-widest text-slate-400 font-extrabold">OCC SYSTEM TIME</span>
            <span className="font-mono text-lg font-black tracking-wider text-emerald-400">
              {currentTime}
            </span>
          </div>

          {/* Right: MongoDB Stream & User Profile */}
          <div className="flex items-center space-x-3">
            <div className="hidden sm:flex items-center space-x-2 bg-emerald-50 border border-emerald-200 px-3 py-1.5 rounded-full">
              <span className="w-2.5 h-2.5 rounded-full bg-emerald-500 animate-ping" />
              <span className="text-xs font-semibold text-emerald-800">
                MONGODB STREAMING ({refreshInterval}s cycle)
              </span>
            </div>

            {/* User Profile Avatar with Click Dropdown */}
            <div className="relative">
              <button
                onClick={() => setShowProfileMenu(!showProfileMenu)}
                className="flex items-center space-x-2 p-1.5 pr-2.5 rounded-full hover:bg-slate-100 border border-slate-200 transition bg-white"
              >
                <div className="w-7 h-7 rounded-full bg-emerald-600 text-white font-bold text-xs flex items-center justify-center">
                  OC
                </div>
                <span className="text-slate-400 text-[10px]">▼</span>
              </button>

              {/* Profile Card Popup */}
              {showProfileMenu && (
                <div className="absolute right-0 mt-2 w-60 bg-white rounded-xl shadow-xl border border-slate-100 py-3 px-4 z-50">
                  <div className="flex items-center space-x-3 pb-3 border-b border-slate-100">
                    <div className="w-9 h-9 rounded-full bg-emerald-600 text-white font-bold text-xs flex items-center justify-center">
                      OC
                    </div>
                    <div className="overflow-hidden">
                      <h4 className="text-xs font-bold text-slate-800">OCC Controller</h4>
                      <p className="text-[11px] text-slate-500 font-medium truncate">
                        controller@metroflow.io
                      </p>
                    </div>
                  </div>

                  <div className="py-2 text-[11px] text-slate-500 border-b border-slate-100">
                    <div>Role: <span className="font-semibold text-emerald-700">Transit Chief Admin</span></div>
                  </div>

                  {onLogout && (
                    <div className="pt-2">
                      <button
                        onClick={() => {
                          setShowProfileMenu(false);
                          onLogout();
                        }}
                        className="w-full py-1.5 px-3 text-xs font-bold text-rose-600 bg-rose-50 hover:bg-rose-100 rounded-lg transition border border-rose-200"
                      >
                        Sign Out
                      </button>
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Navigation Tabs */}
        <div className="max-w-7xl mx-auto px-6 flex space-x-1 overflow-x-auto border-t border-slate-100 scrollbar-none">
          {navItems.map((item) => (
            <button
              key={item.id}
              onClick={() => setActiveTab(item.id)}
              className={`flex items-center space-x-2 px-5 py-3 text-xs font-bold transition-all border-b-2 whitespace-nowrap ${
                activeTab === item.id
                  ? 'border-emerald-600 text-emerald-700 bg-emerald-50/60'
                  : 'border-transparent text-slate-500 hover:text-slate-900 hover:bg-slate-100/50'
              }`}
            >
              <span>{item.icon}</span>
              <span>{item.label}</span>
            </button>
          ))}
        </div>
      </header>

      {/* Main Workspace */}
      <main className="max-w-7xl mx-auto w-full p-6 flex-1">
        {/* TAB 1: LIVE OPERATIONS DASHBOARD */}
        {activeTab === 'dashboard' && (
          <div className="space-y-6">
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
              <div className="bg-white border border-emerald-100 rounded-2xl p-5 shadow-sm">
                <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Live Sensor Ingestion</span>
                <div className="text-3xl font-black text-emerald-700 mt-2 flex items-baseline space-x-2">
                  <span>{livePackets.toLocaleString()}</span>
                  <span className="text-xs font-bold text-emerald-600 animate-pulse">● LIVE TAPS</span>
                </div>
                <div className="text-xs text-slate-400 mt-1">Real-time turnstile packet stream in MongoDB</div>
              </div>

              <div className="bg-white border border-emerald-100 rounded-2xl p-5 shadow-sm">
                <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Active Terminal Nodes</span>
                <div className="text-3xl font-black text-emerald-600 mt-2">
                  {networkData?.active_stations ?? "12 / 12"}
                </div>
                <div className="text-xs text-emerald-600 font-medium mt-1">All telemetry sensors online & transmitting</div>
              </div>

              <div className="bg-white border border-emerald-100 rounded-2xl p-5 shadow-sm">
                <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">System Congestion Index</span>
                <div className="text-3xl font-black text-amber-600 mt-2">
                  {networkData?.avg_congestion_pct ?? 48.6}%
                </div>
                <div className="text-xs text-slate-400 mt-1">Real-time aggregate platform capacity load</div>
              </div>

              <div className="bg-white border border-emerald-100 rounded-2xl p-5 shadow-sm">
                <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Surge Protocol Status</span>
                <div className="text-3xl font-black text-emerald-600 mt-2">
                  {alertActive ? "SURGE ACTIVE" : "NOMINAL"}
                </div>
                <div className="text-xs text-slate-400 mt-1">{alertActive ? "Turnstile metering & headway compressed" : "Automated dispatch on track"}</div>
              </div>
            </div>

            {/* Live Topology SVG */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              <div className="lg:col-span-2 bg-white border border-emerald-100 rounded-2xl p-6 shadow-sm">
                <div className="flex justify-between items-center mb-4">
                  <div>
                    <h2 className="text-base font-bold text-slate-800">Live Seoul Metro Network Topology (12 Stations)</h2>
                    <p className="text-xs text-slate-400">Continuous telemetry feed across Blue, Emerald & Ruby corridors</p>
                  </div>
                  <div className="flex space-x-3 text-xs font-medium text-slate-600">
                    <span className="flex items-center"><span className="w-2.5 h-2.5 rounded-full bg-emerald-500 mr-1.5" /> Normal (&lt;60%)</span>
                    <span className="flex items-center"><span className="w-2.5 h-2.5 rounded-full bg-amber-500 mr-1.5" /> Elevated (≥60%)</span>
                    <span className="flex items-center"><span className="w-2.5 h-2.5 rounded-full bg-rose-500 mr-1.5" /> Surge (≥80%)</span>
                  </div>
                </div>

                <div className="w-full h-96 bg-emerald-50/20 border border-emerald-100 rounded-xl relative overflow-hidden flex items-center justify-center">
                  <svg viewBox="80 80 700 220" className="w-full h-full">
                    <line x1="120" y1="140" x2="220" y2="140" stroke="#059669" strokeWidth="4" />
                    <line x1="220" y1="140" x2="340" y2="140" stroke="#059669" strokeWidth="4" />
                    <line x1="340" y1="140" x2="460" y2="140" stroke="#059669" strokeWidth="4" />
                    <line x1="460" y1="140" x2="580" y2="140" stroke="#059669" strokeWidth="4" />
                    <line x1="580" y1="140" x2="700" y2="140" stroke="#059669" strokeWidth="4" />

                    <line x1="340" y1="140" x2="360" y2="240" stroke="#10b981" strokeWidth="3" strokeDasharray="4 2" />
                    <line x1="460" y1="140" x2="480" y2="240" stroke="#10b981" strokeWidth="3" strokeDasharray="4 2" />

                    <line x1="120" y1="240" x2="240" y2="240" stroke="#34d399" strokeWidth="4" />
                    <line x1="240" y1="240" x2="360" y2="240" stroke="#34d399" strokeWidth="4" />
                    <line x1="360" y1="240" x2="480" y2="240" stroke="#34d399" strokeWidth="4" />
                    <line x1="480" y1="240" x2="600" y2="240" stroke="#047857" strokeWidth="4" />
                    <line x1="600" y1="240" x2="720" y2="240" stroke="#047857" strokeWidth="4" />

                    {stationsList.map((st: any) => (
                      <g key={st.id} className="cursor-pointer">
                        <circle
                          cx={st.x}
                          cy={st.y}
                          r="13"
                          fill="#ffffff"
                          stroke={st.density_pct >= 80 ? "#e11d48" : st.density_pct >= 60 ? "#f59e0b" : "#059669"}
                          strokeWidth="3.5"
                        />
                        <circle
                          cx={st.x}
                          cy={st.y}
                          r="5"
                          fill={st.density_pct >= 80 ? "#e11d48" : st.density_pct >= 60 ? "#d97706" : "#10b981"}
                        />
                        <text x={st.x} y={st.y - 18} textAnchor="middle" className="text-[10px] font-bold fill-slate-800">
                          {st.name}
                        </text>
                        <text x={st.x} y={st.y + 22} textAnchor="middle" className="text-[9px] font-extrabold fill-emerald-800">
                          {st.density_pct}%
                        </text>
                      </g>
                    ))}
                  </svg>
                </div>
              </div>

              {/* Live Turnstile Stream */}
              <div className="bg-white border border-emerald-100 rounded-2xl p-6 shadow-sm flex flex-col justify-between">
                <div>
                  <div className="flex justify-between items-center mb-1">
                    <h2 className="text-base font-bold text-slate-800">Live Turnstile Ingestion</h2>
                    <span className="text-[10px] font-bold text-emerald-600 bg-emerald-50 px-2 py-0.5 rounded-full animate-pulse">
                      STREAMING
                    </span>
                  </div>
                  <p className="text-xs text-slate-400 mb-4">Direct passenger inflow velocity from 192 turnstile gates</p>
                  <div className="space-y-2.5 max-h-80 overflow-y-auto pr-1">
                    {stationsList.map((st: any) => (
                      <div key={st.name} className="p-2.5 bg-emerald-50/30 rounded-xl border border-emerald-100 flex justify-between items-center">
                        <div>
                          <div className="text-xs font-bold text-slate-800">{st.name}</div>
                          <div className="text-[10px] text-slate-500">In: {st.inflow_per_min}/m • Out: {st.outflow_per_min}/m</div>
                        </div>
                        <span className={`text-[11px] font-bold px-2 py-0.5 rounded-full ${
                          st.density_pct >= 80 ? 'bg-rose-100 text-rose-800' :
                          st.density_pct >= 60 ? 'bg-amber-100 text-amber-800' : 'bg-emerald-100 text-emerald-800'
                        }`}>
                          {st.density_pct}%
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>

            {/* AI Scheduling Summary */}
            <div className="bg-white border border-emerald-100 rounded-2xl p-6 shadow-sm">
              <div className="flex justify-between items-center mb-4">
                <div>
                  <h2 className="text-base font-bold text-slate-800">Predictive Scheduling & Headway Optimization</h2>
                  <p className="text-xs text-slate-400">Random Forest automated headway regulation running on live telemetry inputs</p>
                </div>
                <span className="text-xs font-bold px-3 py-1 bg-emerald-100 text-emerald-800 rounded-full">
                  AI REGRESSOR ACTIVE
                </span>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {schedulesList.map((sc: any) => (
                  <div key={sc.corridor} className="p-4 bg-emerald-50/20 border border-emerald-100 rounded-xl">
                    <div className="flex justify-between items-center mb-2">
                      <span className="font-bold text-sm text-slate-800">{sc.corridor}</span>
                      <span className="text-[11px] font-bold px-2 py-0.5 rounded-full bg-emerald-100 text-emerald-700">
                        {sc.status}
                      </span>
                    </div>
                    <div className="text-xs text-slate-600 flex justify-between py-1 border-b border-emerald-50">
                      <span>Baseline Headway:</span>
                      <span className="font-semibold text-slate-800">{sc.current_headway}</span>
                    </div>
                    <div className="text-xs text-slate-600 flex justify-between py-1 border-b border-emerald-50">
                      <span>Recommended Headway:</span>
                      <span className="font-bold text-emerald-700">{sc.recommended_headway}</span>
                    </div>
                    <div className="text-xs text-slate-600 flex justify-between py-1 mt-1">
                      <span>Peak Inflow Forecast:</span>
                      <span className="font-bold text-slate-800">{sc.peak_forecast_per_hr} pass/hr</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* TAB 2: REAL-TIME INGESTION TABLE */}
        {activeTab === 'monitoring' && (
          <div className="space-y-6">
            <div className="bg-white border border-emerald-100 rounded-2xl p-6 shadow-sm">
              <div className="flex justify-between items-center mb-2">
                <h2 className="text-lg font-bold text-slate-800">Live Ingestion Matrix (12 Station Telemetry Streams)</h2>
                <span className="text-xs font-mono font-bold text-emerald-700 bg-emerald-50 px-3 py-1 rounded-lg">
                  INGESTION LATENCY: 8ms
                </span>
              </div>
              <p className="text-xs text-slate-500 mb-6">Continuous turnstile log ingestion streaming directly from IoT sensors into MongoDB.</p>

              <div className="border border-slate-100 rounded-xl overflow-hidden">
                <table className="w-full text-left text-xs">
                  <thead className="bg-slate-50 text-slate-500 font-bold border-b border-slate-100 uppercase">
                    <tr>
                      <th className="p-3">Station Node</th>
                      <th className="p-3">Corridor</th>
                      <th className="p-3">Inflow Velocity</th>
                      <th className="p-3">Outflow Velocity</th>
                      <th className="p-3">Platform Density</th>
                      <th className="p-3">Telemetry Health</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {stationsList.map((st: any) => (
                      <tr key={st.id} className="hover:bg-slate-50/50">
                        <td className="p-3 font-bold text-slate-800">{st.name} ({st.id})</td>
                        <td className="p-3 font-semibold text-slate-600">{st.line}</td>
                        <td className="p-3 font-mono text-emerald-700 font-bold">{st.inflow_per_min} pass/min</td>
                        <td className="p-3 font-mono text-slate-600">{st.outflow_per_min} pass/min</td>
                        <td className="p-3">
                          <div className="flex items-center space-x-2">
                            <div className="w-24 bg-slate-100 h-2 rounded-full overflow-hidden">
                              <div
                                className={`h-full rounded-full ${
                                  st.density_pct >= 80 ? 'bg-rose-500' :
                                  st.density_pct >= 60 ? 'bg-amber-500' : 'bg-emerald-500'
                                }`}
                                style={{ width: `${st.density_pct}%` }}
                              />
                            </div>
                            <span className="font-bold text-slate-700">{st.density_pct}%</span>
                          </div>
                        </td>
                        <td className="p-3">
                          <span className="px-2 py-0.5 rounded text-[11px] font-bold bg-emerald-100 text-emerald-800">
                            ONLINE (16 GATES)
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}

        {/* TAB 3: GPS FLEET TRACKING */}
        {activeTab === 'trains' && (
          <div className="space-y-6">
            <div className="bg-white border border-emerald-100 rounded-2xl p-6 shadow-sm">
              <div className="flex justify-between items-center mb-2">
                <h2 className="text-lg font-bold text-slate-800">Live Fleet GPS Telemetry & Active Control</h2>
                <span className="text-xs font-mono font-bold text-emerald-700 bg-emerald-50 px-3 py-1 rounded-lg">
                  GPS FREQUENCY: 1.0s REFRESH
                </span>
              </div>
              <p className="text-xs text-slate-500 mb-6">
                Click on action buttons to execute live headway compression or broadcast alternate routes.
              </p>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
                {[
                  {
                    id: "TR-101",
                    line: "Blue Corridor",
                    next: "Central Terminal",
                    speed: "64 km/h",
                    load: "38%",
                    status: "NOMINAL",
                    delay: "On Time (0m)",
                    altRoute: "Direct Line 1 Nominal",
                    cars: [35, 40, 36, 42]
                  },
                  {
                    id: "TR-204",
                    line: "Interchange Link",
                    next: "Tech Hub Junction",
                    speed: "42 km/h",
                    load: "84%",
                    status: "CONGESTED",
                    delay: "Delayed (+4.2m)",
                    altRoute: "Divert via Emerald Express (Line 2)",
                    cars: [88, 85, 82, 81]
                  },
                  {
                    id: "TR-309",
                    line: "Emerald Express",
                    next: "Market Square",
                    speed: "56 km/h",
                    load: "28%",
                    status: "NOMINAL",
                    delay: "On Time (0m)",
                    altRoute: "Direct Line 2 Nominal",
                    cars: [25, 30, 28, 29]
                  }
                ].map((t) => (
                  <div
                    key={t.id}
                    className="p-5 bg-emerald-50/20 hover:bg-emerald-50/40 rounded-2xl border border-emerald-100 transition-all shadow-sm flex flex-col justify-between"
                  >
                    <div>
                      <div className="flex justify-between items-center font-bold text-sm text-slate-800 mb-2">
                        <div className="flex items-center space-x-2">
                          <span className="text-base">🚆</span>
                          <span>{t.id}</span>
                        </div>
                        <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${
                          t.status === 'CONGESTED' ? 'bg-rose-100 text-rose-700' : 'bg-emerald-100 text-emerald-700'
                        }`}>
                          {t.status === 'CONGESTED' ? 'DELAYED / HIGH LOAD' : 'IN_TRANSIT (LIVE GPS)'}
                        </span>
                      </div>

                      <div className="text-xs text-slate-600 space-y-1.5 mt-3">
                        <div className="flex justify-between">
                          <span className="text-slate-400">Corridor:</span>
                          <span className="font-semibold text-slate-700">{t.line}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-slate-400">Approaching Node:</span>
                          <span className="font-semibold text-slate-900">{t.next}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-slate-400">Live Velocity:</span>
                          <span className="font-semibold text-emerald-700">{t.speed}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-slate-400">Rake Occupancy:</span>
                          <span className={`font-bold ${t.load === '84%' ? 'text-rose-600' : 'text-slate-800'}`}>
                            {t.load}
                          </span>
                        </div>
                        <div className="flex justify-between pt-1 border-t border-emerald-100">
                          <span className="text-slate-400">Schedule Drift:</span>
                          <span className={`font-semibold ${t.delay.includes('Delayed') ? 'text-rose-600' : 'text-emerald-700'}`}>
                            {t.delay}
                          </span>
                        </div>
                      </div>

                      <div className="mt-3">
                        <span className="text-[10px] font-bold text-slate-400 block mb-1">Coach Load (Cars 1-4)</span>
                        <div className="grid grid-cols-4 gap-1">
                          {t.cars.map((c, i) => (
                            <div key={i} className="h-2 rounded bg-slate-200 overflow-hidden" title={`Coach ${i+1}: ${c}%`}>
                              <div
                                className={`h-full ${c >= 80 ? 'bg-rose-500' : c >= 60 ? 'bg-amber-500' : 'bg-emerald-500'}`}
                                style={{ width: `${c}%` }}
                              />
                            </div>
                          ))}
                        </div>
                      </div>
                    </div>

                    <div className="mt-4 pt-3 border-t border-emerald-100 space-y-2">
                      <button
                        onClick={() => {
                          handleBroadcastAlert(`DISPATCH DIRECTIVE: Headway compressed by 60s for ${t.id} approaching ${t.next}.`);
                          setActiveTab('alerts');
                        }}
                        className="w-full py-2 bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-bold rounded-xl transition"
                      >
                        ⚡ Compress Headway (-60s)
                      </button>

                      <button
                        onClick={() => {
                          handleBroadcastAlert(`PASSENGER ADVISORY: ${t.id} experiencing delay. Commuters advised to divert via ${t.altRoute}.`);
                          setActiveTab('alerts');
                        }}
                        className="w-full py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-semibold rounded-xl transition border border-slate-200"
                      >
                        📢 Broadcast Alternate Route
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* TAB 4: DYNAMIC HEADWAY SCHEDULES */}
        {activeTab === 'schedules' && (
          <div className="space-y-6">
            <div className="bg-white border border-emerald-100 rounded-2xl p-6 shadow-sm">
              <div className="flex justify-between items-center mb-2">
                <div>
                  <h2 className="text-lg font-bold text-slate-800">Dynamic Headway Regulation Engine & Dispatch Control</h2>
                  <p className="text-xs text-slate-500">
                    Random Forest AI Headway recommendations. Click action buttons to execute live fleet compression or inject spare rakes.
                  </p>
                </div>
                <span className="text-xs font-mono font-bold text-emerald-800 bg-emerald-50 px-3 py-1 rounded-full border border-emerald-200">
                  AUTOMATED DISPATCH: ARMED
                </span>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-5 mt-6">
                {schedulesList.map((sc: any) => (
                  <div
                    key={sc.corridor}
                    className="p-5 bg-emerald-50/20 hover:bg-emerald-50/30 rounded-2xl border border-emerald-100 transition-all shadow-sm flex flex-col justify-between"
                  >
                    <div>
                      <div className="flex justify-between items-start mb-3">
                        <div>
                          <div className="font-bold text-slate-900 text-sm flex items-center space-x-1.5">
                            <span className="w-2.5 h-2.5 rounded-full bg-emerald-600 inline-block" />
                            <span>{sc.corridor}</span>
                          </div>
                          <span className="text-[10px] text-slate-400 font-mono">{sc.code} • Max Bottleneck: {sc.bottleneckStation}</span>
                        </div>
                        <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${
                          sc.status === 'HIGH_DEMAND' ? 'bg-rose-100 text-rose-700' : 'bg-emerald-100 text-emerald-800'
                        }`}>
                          {sc.status}
                        </span>
                      </div>

                      <div className="grid grid-cols-2 gap-2 my-3 p-3 bg-white rounded-xl border border-slate-200/80">
                        <div>
                          <span className="text-[10px] text-slate-400 font-bold uppercase block">Current Headway</span>
                          <span className="text-base font-extrabold text-slate-700">{sc.current_headway}</span>
                        </div>
                        <div className="border-l border-slate-100 pl-3">
                          <span className="text-[10px] text-emerald-600 font-bold uppercase block">AI Optimized</span>
                          <span className="text-base font-extrabold text-emerald-700">{sc.recommended_headway}</span>
                        </div>
                      </div>

                      <div className="text-xs text-slate-600 space-y-1.5 pt-1">
                        <div className="flex justify-between">
                          <span className="text-slate-400">Live Demand Velocity:</span>
                          <span className="font-bold text-slate-800">{sc.peak_forecast_per_hr} pass/hr</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-slate-400">Active Trainsets:</span>
                          <span className="font-semibold text-slate-700">{sc.activeTrains} Rakes in Transit</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-slate-400">Depot Standby Rakes:</span>
                          <span className="font-semibold text-emerald-700">{sc.standbyReady} Hot-Spare Available</span>
                        </div>
                      </div>
                    </div>

                    <div className="mt-5 pt-3 border-t border-emerald-100 space-y-2">
                      <button
                        onClick={() => {
                          handleBroadcastAlert(
                            `DISPATCH OVERRIDE: Applied AI headway (${sc.recommended_headway}) on ${sc.corridor}. Signaling system updated.`
                          );
                          setActiveTab('alerts');
                        }}
                        className="w-full py-2 bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-bold rounded-xl transition shadow-sm flex items-center justify-center space-x-1"
                      >
                        <span>⚡ Apply AI Headway ({sc.recommended_headway})</span>
                      </button>

                      <div className="grid grid-cols-2 gap-2">
                        <button
                          onClick={() => {
                            handleBroadcastAlert(
                              `DEPOT DIRECTIVE: Injecting 1 standby rake into ${sc.corridor} to absorb passenger surge at ${sc.bottleneckStation}.`
                            );
                            setActiveTab('alerts');
                          }}
                          className="py-1.5 bg-white hover:bg-emerald-50 text-emerald-800 border border-emerald-200 text-[11px] font-bold rounded-xl transition"
                        >
                          🚆 Inject Standby
                        </button>

                        <button
                          onClick={() => {
                            handleBroadcastAlert(
                              `COMMUTER NOTICE: High passenger frequency on ${sc.corridor}. Trains arriving every ${sc.recommended_headway}.`
                            );
                            setActiveTab('alerts');
                          }}
                          className="py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 border border-slate-200 text-[11px] font-semibold rounded-xl transition"
                        >
                          📢 Send Notice
                        </button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* TAB 5: MULTI-CHANNEL ALERTS */}
        {activeTab === 'alerts' && (
          <div className="space-y-6">
            <div className="bg-white border border-emerald-100 rounded-2xl p-6 shadow-sm">
              <div className="flex justify-between items-center mb-4">
                <div>
                  <h2 className="text-lg font-bold text-slate-800">Alert Service & External Integrations Hub</h2>
                  <p className="text-xs text-slate-500">
                    Live triggers for Email (SendGrid), SMS (Twilio), Push Notifications (FCM), and Public Address (PA) System.
                  </p>
                </div>
                <span className="px-3 py-1 bg-emerald-100 text-emerald-800 rounded-full text-xs font-bold">
                  4 EXTERNAL CHANNELS ACTIVE
                </span>
              </div>

              {/* Live Dispatch Log */}
              {dispatchResult && (
                <div className="p-4 mb-6 bg-slate-900 border border-emerald-500 rounded-2xl text-white shadow-xl">
                  <div className="flex justify-between items-center border-b border-slate-800 pb-2 mb-3">
                    <div className="flex items-center space-x-2">
                      <span className="w-2.5 h-2.5 rounded-full bg-emerald-400 animate-ping" />
                      <span className="text-xs font-bold text-emerald-400 uppercase tracking-wide">
                        Live Multi-Channel Broadcast Dispatched
                      </span>
                    </div>
                    <button
                      onClick={() => setDispatchResult(null)}
                      className="text-xs text-slate-400 hover:text-white underline"
                    >
                      Clear Log
                    </button>
                  </div>

                  <div className="text-xs text-slate-300 mb-3">
                    <strong>Message Broadcast:</strong> "{dispatchResult.message_broadcast}"
                  </div>

                  <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-3 text-xs">
                    <div className="bg-slate-800/80 p-3 rounded-xl border border-slate-700">
                      <span className="text-slate-400 font-bold block mb-1">✉️ Email Service</span>
                      <span className="text-emerald-400 font-bold block">{dispatchResult.channels_dispatched?.EMAIL?.status}</span>
                      <span className="text-[10px] text-slate-400">{dispatchResult.channels_dispatched?.EMAIL?.gateway}</span>
                    </div>

                    <div className="bg-slate-800/80 p-3 rounded-xl border border-slate-700">
                      <span className="text-slate-400 font-bold block mb-1">💬 SMS Service</span>
                      <span className="text-emerald-400 font-bold block">{dispatchResult.channels_dispatched?.SMS?.status}</span>
                      <span className="text-[10px] text-slate-400">{dispatchResult.channels_dispatched?.SMS?.gateway}</span>
                    </div>

                    <div className="bg-slate-800/80 p-3 rounded-xl border border-slate-700">
                      <span className="text-slate-400 font-bold block mb-1">📱 Push Notifications</span>
                      <span className="text-emerald-400 font-bold block">{dispatchResult.channels_dispatched?.PUSH_NOTIFICATION?.status}</span>
                      <span className="text-[10px] text-slate-400">{dispatchResult.channels_dispatched?.PUSH_NOTIFICATION?.service}</span>
                    </div>

                    <div className="bg-slate-800/80 p-3 rounded-xl border border-slate-700">
                      <span className="text-slate-400 font-bold block mb-1">📢 PA System</span>
                      <span className="text-emerald-400 font-bold block">{dispatchResult.channels_dispatched?.PUBLIC_ADDRESS?.status}</span>
                      <span className="text-[10px] text-slate-400">{dispatchResult.channels_dispatched?.PUBLIC_ADDRESS?.speakers_online} Speakers Online</span>
                    </div>
                  </div>
                </div>
              )}

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="p-4 border border-emerald-100 rounded-xl bg-slate-50/50 flex flex-col justify-between">
                  <div>
                    <h3 className="text-xs font-bold text-slate-800 mb-1">Broadcast Live Passenger Advisory</h3>
                    <p className="text-[11px] text-slate-400 mb-3">Dispatches simultaneous audio to station speakers & mobile notifications.</p>
                    <textarea
                      value={announcementText}
                      onChange={(e) => setAnnouncementText(e.target.value)}
                      placeholder="e.g. Surge detected at Tech Hub Junction. Compressing headway to 3.0m..."
                      className="w-full h-24 p-2.5 bg-white border border-slate-200 rounded-xl text-xs mb-3 focus:outline-none focus:border-emerald-500"
                    />
                  </div>
                  <button
                    onClick={() => handleBroadcastAlert()}
                    disabled={isDispatching}
                    className="w-full py-2.5 bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-bold rounded-xl transition shadow-sm"
                  >
                    {isDispatching ? 'Dispatching Across Channels...' : 'Dispatch Broadcast (Email, SMS, Push, PA) →'}
                  </button>
                </div>

                <div className="p-4 border border-emerald-100 rounded-xl bg-slate-50/50 flex flex-col justify-between">
                  <div>
                    <h3 className="text-xs font-bold text-slate-800 mb-1">Emergency Surge Protocol Action</h3>
                    <p className="text-[11px] text-slate-500 mb-4">
                      Immediately restricts turnstiles at high-density stations, compresses headway to 2.5m, and sends urgent SMS to Station Masters.
                    </p>
                    <div className="p-3 bg-amber-50 rounded-xl border border-amber-200 text-amber-900 text-xs mb-4">
                      <strong>Automated Directive:</strong> Instant turnstile rate-limiting across affected corridor nodes.
                    </div>
                  </div>
                  <button
                    onClick={() => {
                      const nextState = !alertActive;
                      setAlertActive(nextState);
                      handleBroadcastAlert(
                        nextState 
                          ? "CRITICAL SURGE DETECTED: Turnstile metering activated. Headway shortened to 2.5m across Blue Corridor."
                          : "SURGE CONTAINMENT DEACTIVATED: All terminal gates restored to nominal operating frequency."
                      );
                    }}
                    disabled={isDispatching}
                    className={`w-full py-3 text-xs font-bold rounded-xl transition shadow-sm ${
                      alertActive ? 'bg-rose-600 hover:bg-rose-500 text-white' : 'bg-amber-500 hover:bg-amber-400 text-white'
                    }`}
                  >
                    {alertActive ? 'DEACTIVATE SURGE PROTOCOL' : 'ACTIVATE SURGE PROTOCOL & DISPATCH ALERTS'}
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* TAB 6: LIVE AI DEMAND ENGINE */}
        {activeTab === 'analytics' && (
          <div className="space-y-6">
            <div className="bg-white border border-emerald-100 rounded-2xl p-6 shadow-sm">
              <div className="flex justify-between items-center mb-1">
                <h2 className="text-lg font-bold text-slate-800">Live AI Demand Engine & Surge Anticipation</h2>
                <span className="text-xs font-mono font-bold text-emerald-800 bg-emerald-50 px-3 py-1 rounded-xl">
                  INFERENCE LATENCY: 12ms
                </span>
              </div>
              <p className="text-xs text-slate-400 mb-6">Continuous inference on live telemetry inputs to anticipate platform bottlenecks before overcrowding occurs.</p>

              <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                <div className="p-5 bg-slate-50 border border-slate-200 rounded-2xl space-y-4">
                  <div>
                    <label className="block text-[11px] font-bold text-slate-600 uppercase mb-1">Station Telemetry Target</label>
                    <select
                      value={simStation}
                      onChange={(e) => setSimStation(e.target.value)}
                      className="w-full p-2.5 bg-white border border-slate-200 rounded-xl text-xs font-semibold"
                    >
                      {stationsList.map((st: any) => (
                        <option key={st.name} value={st.name}>{st.name} ({st.id})</option>
                      ))}
                    </select>
                  </div>

                  <div>
                    <label className="block text-[11px] font-bold text-slate-600 uppercase mb-1">Operational Hour ({simHour}:00)</label>
                    <input
                      type="range"
                      min={6}
                      max={22}
                      value={simHour}
                      onChange={(e) => setSimHour(Number(e.target.value))}
                      className="w-full accent-emerald-600 cursor-pointer"
                    />
                  </div>

                  <div>
                    <label className="block text-[11px] font-bold text-slate-600 uppercase mb-1">Live Conditions</label>
                    <select
                      value={simCondition}
                      onChange={(e) => setSimCondition(e.target.value)}
                      className="w-full p-2.5 bg-white border border-slate-200 rounded-xl text-xs font-semibold"
                    >
                      <option value="NORMAL">Standard Flow</option>
                      <option value="WEATHER_RAIN">Inclement Weather (+25%)</option>
                      <option value="EVENT_SURGE">Major Urban Event (+45%)</option>
                    </select>
                  </div>

                  <button
                    onClick={runAiInference}
                    className="w-full py-2.5 bg-emerald-600 text-white font-bold text-xs uppercase rounded-xl"
                  >
                    Run Real-Time AI Inference →
                  </button>
                </div>

                <div className="lg:col-span-2 p-5 bg-emerald-50/30 border border-emerald-100 rounded-2xl flex flex-col justify-between">
                  <div>
                    <div className="flex justify-between items-center mb-4">
                      <span className="text-xs font-bold text-slate-800">Live AI Output for {simStation}</span>
                      <span className={`px-2.5 py-0.5 rounded-full text-xs font-bold ${
                        aiOutput.riskLevel === 'CRITICAL' ? 'bg-rose-100 text-rose-800' :
                        aiOutput.riskLevel === 'HIGH' ? 'bg-amber-100 text-amber-800' : 'bg-emerald-100 text-emerald-800'
                      }`}>
                        {aiOutput.riskLevel} SURGE RISK
                      </span>
                    </div>

                    <div className="grid grid-cols-3 gap-4 mb-4">
                      <div className="p-3 bg-white rounded-xl border border-emerald-100">
                        <div className="text-[10px] text-slate-400 font-bold uppercase">Forecast Inflow Velocity</div>
                        <div className="text-xl font-black text-emerald-800 mt-1">{aiOutput.predictedInflow} pass/m</div>
                      </div>
                      <div className="p-3 bg-white rounded-xl border border-emerald-100">
                        <div className="text-[10px] text-slate-400 font-bold uppercase">Anticipated Density</div>
                        <div className="text-xl font-black text-slate-800 mt-1">{aiOutput.predictedDensity}%</div>
                      </div>
                      <div className="p-3 bg-white rounded-xl border border-emerald-100">
                        <div className="text-[10px] text-slate-400 font-bold uppercase">Confidence Score</div>
                        <div className="text-xl font-black text-emerald-700 mt-1">{aiOutput.confidence}</div>
                      </div>
                    </div>

                    <div className="p-3 bg-white rounded-xl border border-slate-200 space-y-1 text-xs">
                      <div>⚡ <strong>Automated Headway Directive:</strong> {aiOutput.headwayAction}</div>
                      <div>🚆 <strong>Fleet Regulation:</strong> {aiOutput.fleetRecommendation}</div>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <div className="bg-white border border-emerald-100 rounded-2xl p-6 shadow-sm">
              <h3 className="text-sm font-bold text-slate-800 mb-4">24-Hour Passenger Inflow Anticipation Curve</h3>
              <div className="h-40 flex items-end justify-between gap-2 border-b border-slate-100 pb-2">
                {hourlyCurve.map((bar) => (
                  <div key={bar.hour} className="flex-1 flex flex-col items-center h-full justify-end">
                    <div
                      className={`w-full rounded-t-lg ${bar.peak ? 'bg-amber-500' : 'bg-emerald-500'}`}
                      style={{ height: `${bar.riders}%` }}
                    />
                  </div>
                ))}
              </div>
              <div className="flex justify-between text-[10px] text-slate-400 mt-2 font-bold">
                {hourlyCurve.map((bar) => (
                  <span key={bar.hour}>{bar.hour}</span>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* TAB 7: INTERACTIVE TELEMETRY STREAM & OCC CONFIGURATION */}
        {activeTab === 'settings' && (
          <div className="space-y-6 max-w-4xl">
            <div className="bg-white border border-emerald-100 rounded-2xl p-6 shadow-sm">
              <div className="flex justify-between items-center mb-2">
                <div>
                  <h2 className="text-lg font-bold text-slate-800">Telemetry Stream & OCC Control Configuration</h2>
                  <p className="text-xs text-slate-500">
                    Adjust real-time ingestion rates, AI automation policies, and commuter alert thresholds.
                  </p>
                </div>
                <span className="text-xs font-mono font-bold text-emerald-800 bg-emerald-50 px-3 py-1 rounded-full border border-emerald-200">
                  OCC CONTROLLER MODE
                </span>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mt-6">
                <div className="p-4 bg-slate-50 border border-slate-200 rounded-xl">
                  <div className="flex justify-between items-center mb-2">
                    <label className="text-xs font-bold text-slate-700 uppercase">Live Ingestion Rate</label>
                    <span className="text-xs font-extrabold text-emerald-700 bg-white px-2.5 py-0.5 rounded-md border border-slate-200">
                      {refreshInterval}s Cycle
                    </span>
                  </div>
                  <input
                    type="range"
                    min={1}
                    max={10}
                    value={refreshInterval}
                    onChange={(e) => setRefreshInterval(Number(e.target.value))}
                    className="w-full accent-emerald-600 cursor-pointer"
                  />
                  <div className="flex justify-between text-[10px] text-slate-400 mt-1 font-semibold">
                    <span>1s (Ultra Real-Time)</span>
                    <span>10s (Bandwidth Saver)</span>
                  </div>
                </div>

                <div className="p-4 bg-slate-50 border border-slate-200 rounded-xl">
                  <div className="flex justify-between items-center mb-2">
                    <label className="text-xs font-bold text-slate-700 uppercase">Congestion Surge Threshold</label>
                    <span className="text-xs font-extrabold text-amber-700 bg-white px-2.5 py-0.5 rounded-md border border-slate-200">
                      {congestionThreshold}% Load
                    </span>
                  </div>
                  <input
                    type="range"
                    min={40}
                    max={85}
                    step={5}
                    value={congestionThreshold}
                    onChange={(e) => setCongestionThreshold(Number(e.target.value))}
                    className="w-full accent-amber-500 cursor-pointer"
                  />
                  <div className="flex justify-between text-[10px] text-slate-400 mt-1 font-semibold">
                    <span>40% (Early Warning)</span>
                    <span>85% (Extreme Surge Only)</span>
                  </div>
                </div>

                <div className="p-4 bg-slate-50 border border-slate-200 rounded-xl flex items-center justify-between">
                  <div>
                    <div className="text-xs font-bold text-slate-800">Auto-Apply AI Headway</div>
                    <p className="text-[11px] text-slate-500">Automatically compress frequency when surge exceeds limit</p>
                  </div>
                  <button
                    onClick={() => setAutoDispatch(!autoDispatch)}
                    className={`w-12 h-6 flex items-center rounded-full p-1 transition-colors ${
                      autoDispatch ? 'bg-emerald-600 justify-end' : 'bg-slate-300 justify-start'
                    }`}
                  >
                    <span className="w-4 h-4 bg-white rounded-full shadow-md transform transition-transform" />
                  </button>
                </div>

                <div className="p-4 bg-slate-50 border border-slate-200 rounded-xl flex items-center justify-between">
                  <div>
                    <div className="text-xs font-bold text-slate-800">Offline Voice SMS / Flash Alert</div>
                    <p className="text-[11px] text-slate-500">Audio synthesis for commuters without active data/WiFi</p>
                  </div>
                  <span className="text-[10px] font-bold px-2 py-1 rounded bg-emerald-100 text-emerald-800">
                    ENABLED (2G/4G)
                  </span>
                </div>
              </div>

              <div className="mt-6 pt-5 border-t border-slate-100 grid grid-cols-1 sm:grid-cols-3 gap-4 text-xs">
                <div className="p-3 bg-emerald-50/40 rounded-xl border border-emerald-100">
                  <span className="text-slate-400 block text-[10px] font-bold uppercase">MongoDB Storage Target</span>
                  <span className="font-mono font-bold text-slate-800 text-xs">metroflow_db</span>
                  <span className="block text-[10px] text-emerald-600 mt-0.5">● Connected (port 27017)</span>
                </div>

                <div className="p-3 bg-emerald-50/40 rounded-xl border border-emerald-100">
                  <span className="text-slate-400 block text-[10px] font-bold uppercase">Ingestion Topology Nodes</span>
                  <span className="font-bold text-slate-800 text-xs">12 Active Stations</span>
                  <span className="block text-[10px] text-slate-500 mt-0.5">192 Turnstiles Telemetry</span>
                </div>

                <div className="p-3 bg-emerald-50/40 rounded-xl border border-emerald-100">
                  <span className="text-slate-400 block text-[10px] font-bold uppercase">Model Serving Engine</span>
                  <span className="font-bold text-slate-800 text-xs">Random Forest Regressor</span>
                  <span className="block text-[10px] text-emerald-600 mt-0.5">Scikit-Learn Microservice</span>
                </div>
              </div>

              <div className="mt-6 flex flex-col sm:flex-row gap-3">
                <button
                  onClick={() => {
                    handleBroadcastAlert("CONFIGURATION APPLIED: Ingestion cycle and headway thresholds updated across OCC system.");
                    setActiveTab('alerts');
                  }}
                  className="px-5 py-2.5 bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-bold rounded-xl transition shadow-sm"
                >
                  Save & Deploy Configuration →
                </button>

                <button
                  onClick={() => {
                    setRefreshInterval(3);
                    setCongestionThreshold(60);
                    setAutoDispatch(true);
                  }}
                  className="px-4 py-2.5 bg-white border border-slate-200 text-slate-600 hover:bg-slate-50 text-xs font-semibold rounded-xl transition"
                >
                  Reset Defaults
                </button>
              </div>
            </div>
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="bg-white border-t border-slate-100 py-3 text-center text-xs text-slate-400">
        MetroFlow Operations Intelligence Platform • Real-Time Sensor Telemetry Stream (Zero-CCTV Ingestion)
      </footer>
    </div>
  );
};

export default Dashboard;