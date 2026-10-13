'use client';

import React, { useEffect, useState, useRef } from 'react';
import { io } from 'socket.io-client';
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, BarChart, Bar } from 'recharts';
import { Train, Bell, Activity, Search, Clock, Zap, AlertTriangle, Send, RefreshCw } from 'lucide-react';

/* -----------------------------------------------------------------------------------
   ENLARGED INTERACTIVE G-LINE SCHEMATIC TRACK MAP COMPONENT
   ----------------------------------------------------------------------------------- */
function GLineTrackMap({ stations, trains, onStationClick }: { stations: any[]; trains: any[]; onStationClick: (name: string) => void }) {
    const G_LINE_STATIONS_LIST = [
        "Court Sq", "21 St", "Greenpoint Av", "Nassau Av", "Metropolitan Av",
        "Broadway", "Flushing Av", "Myrtle–Willoughby Avs", "Bedford–Nostrand Avs",
        "Classon Av", "Clinton–Washington Avs", "Fulton St", "Hoyt–Schermerhorn Sts",
        "Bergen St", "Carroll St", "Smith–9th Sts", "Fourth Ave / 9th St",
        "7th Ave", "15 St–Prospect Park", "Fort Hamilton Pkwy", "Church Av"
    ];

    return (
        <div className="bg-white border border-slate-200 rounded-xl p-8 shadow-sm mb-6">
            <div className="flex justify-between items-center mb-6 flex-wrap gap-2">
                <div>
                    <h2 className="text-lg font-bold text-slate-800 flex items-center gap-2">
                        <span className="h-4 w-4 rounded-full bg-lime-500 inline-block"></span>
                        G-Line Route Map (Court Sq ↔ Church Av)
                    </h2>
                    <p className="text-xs text-slate-500">Live two-way track schematic with real-time station crowd density and train positioning</p>
                </div>
                <div className="flex items-center gap-5 text-xs font-semibold">
                    <span className="flex items-center gap-2"><span className="h-3 w-3 rounded-full bg-emerald-500"></span> Normal (&lt;55%)</span>
                    <span className="flex items-center gap-2"><span className="h-3 w-3 rounded-full bg-amber-500"></span> Moderate (55-80%)</span>
                    <span className="flex items-center gap-2"><span className="h-3 w-3 rounded-full bg-rose-500 animate-pulse"></span> High Alert (&gt;80%)</span>
                </div>
            </div>

            {/* Enlarged Track Container */}
            <div className="relative overflow-x-auto pt-16 pb-24 px-8 bg-slate-50 border border-slate-200 rounded-xl">
                {/* Main G-Line Lime Green Track Line (Thicker h-4) */}
                <div className="absolute top-1/2 left-10 right-10 h-4 bg-lime-500 rounded-full -translate-y-1/2 shadow-inner"></div>

                {/* Expanded Station Spacing (min-w-[1600px]) */}
                <div className="relative flex justify-between items-center min-w-[1600px] px-4">
                    {G_LINE_STATIONS_LIST.map((stationName, idx) => {
                        const stationData = stations?.find((s) => s.station_name === stationName);
                        const status = stationData?.status || 'LOW DENSITY';
                        const trainsHere = trains?.filter((t) => t.current_station === stationName) || [];

                        const statusColor =
                            status === 'HIGH ALERT' ? 'bg-rose-500 ring-rose-300' :
                                status === 'MODERATE' ? 'bg-amber-500 ring-amber-300' : 'bg-emerald-500 ring-emerald-300';

                        return (
                            <div key={stationName} className="relative flex flex-col items-center group cursor-pointer" onClick={() => onStationClick(stationName)}>
                                {/* Larger Active Train Badges ABOVE Station */}
                                <div className="absolute -top-14 flex flex-col items-center gap-1 z-20">
                                    {trainsHere.map((t) => (
                                        <div
                                            key={t.train_id}
                                            className="bg-sky-800 text-white text-xs font-extrabold px-2 py-1 rounded-md shadow-lg border border-sky-300 flex items-center gap-1.5 animate-bounce"
                                            title={`${t.train_id} (${t.direction}) - ${t.occupancy_pct}% Full`}
                                        >
                                            <Train className="h-3.5 w-3.5 text-lime-300" />
                                            <span>{t.train_id}</span>
                                        </div>
                                    ))}
                                </div>

                                {/* Larger Station Node Marker (h-8 w-8) */}
                                <div className={`h-8 w-8 rounded-full border-2 border-white ${statusColor} ring-4 transition transform group-hover:scale-125 z-10 flex items-center justify-center shadow-lg`}>
                                    <span className="text-xs font-black text-white">{idx + 1}</span>
                                </div>

                                {/* Larger Station Label BELOW Track */}
                                <div className="absolute top-10 -rotate-45 origin-top-left w-32 text-xs font-bold text-slate-700 group-hover:text-sky-700 transition truncate">
                                    {stationName}
                                </div>

                                {/* Enhanced Station Hover Tooltip */}
                                <div className="absolute bottom-12 hidden group-hover:flex flex-col bg-slate-900 text-white text-xs p-3 rounded-xl shadow-2xl z-30 w-52 pointer-events-none border border-slate-700">
                                    <p className="font-bold text-sky-300 border-b border-slate-700 pb-1 mb-1.5">{stationName}</p>
                                    <p className="text-slate-300">Density: <span className="font-bold text-white">{stationData?.crowd_density_pct || 0}%</span></p>
                                    <p className="text-slate-300">Inflow/Outflow: <span className="font-mono text-white">+{stationData?.inflow || 0} / -{stationData?.outflow || 0}</span></p>
                                    <p className="text-slate-300">Status: <span className={`font-bold ${status === 'HIGH ALERT' ? 'text-rose-400' : 'text-emerald-400'}`}>{status}</span></p>
                                </div>
                            </div>
                        );
                    })}
                </div>
            </div>
        </div>
    );
}
/* -----------------------------------------------------------------------------------
   MAIN PLATFORM DASHBOARD
   ----------------------------------------------------------------------------------- */
export default function MetroFlowPlatform() {
    const [activeTab, setActiveTab] = useState<'dashboard' | 'crowd' | 'scheduling' | 'alerts' | 'analysis'>('dashboard');
    const [telemetry, setTelemetry] = useState<any>(null);
    const [searchTerm, setSearchTerm] = useState<string>('');

    const [forecastOffset, setForecastOffset] = useState<number>(0);
    const forecastOffsetRef = useRef<number>(0);

    const [broadcastMsg, setBroadcastMsg] = useState<string>('');
    const [manualStation, setManualStation] = useState<string>('Court Sq');
    const [manualTitle, setManualTitle] = useState<string>('High Density Warning');

    const [selectedTrainId, setSelectedTrainId] = useState<string>('G-101');
    const [inputDelay, setInputDelay] = useState<number>(3);
    const [inputHeadway, setInputHeadway] = useState<number>(5);

    const [selectedDay, setSelectedDay] = useState<number>(7);
    const [analysisData, setAnalysisData] = useState<any>(null);

    useEffect(() => {
        const socket = io('http://localhost:8000');

        socket.on('live_fleet_update', (data: any) => {
            if (forecastOffsetRef.current === 0) {
                setTelemetry(data);
            }
        });

        fetchAnalysis(7);

        return () => {
            socket.disconnect();
        };
    }, []);

    const handleForecastSelect = async (mins: number) => {
        setForecastOffset(mins);
        forecastOffsetRef.current = mins;

        if (mins === 0) {
            return;
        }

        try {
            const res = await fetch(`http://localhost:8000/api/forecast/${mins}`);
            const data = await res.json();
            setTelemetry(data);
        } catch (err) {
            console.error('Failed to fetch forecast:', err);
        }
    };

    const fetchAnalysis = async (day: number) => {
        try {
            const res = await fetch(`http://localhost:8000/api/analysis/daily/${day}`);
            const data = await res.json();
            setAnalysisData(data);
        } catch (err) {
            console.error('Failed to fetch analysis:', err);
        }
    };

    const handleBroadcast = async () => {
        if (!broadcastMsg) return;
        await fetch('http://localhost:8000/api/alerts/broadcast', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message: broadcastMsg }),
        });
        setBroadcastMsg('');
    };

    const handleManualAlert = async () => {
        await fetch('http://localhost:8000/api/alerts/manual', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                title: manualTitle,
                message: `Density overload alert generated for ${manualStation}`,
                severity: 'HIGH',
                target_station: manualStation
            }),
        });
        alert(`Alert sent to Alerts module for ${manualStation}!`);
    };

    const handleScheduleAdjust = async () => {
        await fetch('http://localhost:8000/api/schedule/adjust-train', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                train_id: selectedTrainId,
                new_delay_min: Number(inputDelay),
                new_headway_min: Number(inputHeadway)
            }),
        });
        alert(`Updated ${selectedTrainId}! Trailing fleet schedules updated.`);
    };

    const filteredStations = telemetry?.station_performance?.filter((s: any) =>
        s.station_name.toLowerCase().includes(searchTerm.toLowerCase())
    ) || [];

    const filteredTrains = telemetry?.trains?.filter((t: any) =>
        t.train_id.toLowerCase().includes(searchTerm.toLowerCase()) ||
        t.current_station.toLowerCase().includes(searchTerm.toLowerCase())
    ) || [];

    return (
        <div className="min-h-screen bg-slate-50 text-slate-800 font-sans pb-12">
            {/* Header Bar */}
            <header className="bg-sky-100 border-b border-sky-200 px-6 py-4 flex flex-wrap justify-between items-center shadow-sm">
                <div className="flex items-center gap-3">
                    <div className="bg-sky-600 text-white p-2 rounded-lg">
                        <Train className="h-6 w-6" />
                    </div>
                    <div>
                        <div className="flex items-center gap-2">
                            <span className="text-xl font-bold text-sky-900">MetroFlow</span>
                            <span className="bg-sky-200 text-sky-800 text-xs px-2 py-0.5 rounded font-mono font-semibold">AI Platform v1.0</span>
                        </div>
                        <p className="text-xs text-sky-700">G-Line Two-Way Fleet Intelligence • Brooklyn–Queens Crosstown</p>
                    </div>
                </div>

                {/* Navigation Tabs */}
                <nav className="flex items-center gap-1 bg-white/80 border border-sky-200 p-1 rounded-xl shadow-inner my-2 md:my-0">
                    {[
                        { id: 'dashboard', label: 'Dashboard' },
                        { id: 'crowd', label: 'Crowd Monitoring' },
                        { id: 'scheduling', label: 'Train Scheduling' },
                        { id: 'alerts', label: 'Alert System' },
                        { id: 'analysis', label: 'Analysis' }
                    ].map((tab) => (
                        <button
                            key={tab.id}
                            onClick={() => setActiveTab(tab.id as any)}
                            className={`px-4 py-2 text-xs font-semibold rounded-lg transition ${activeTab === tab.id
                                ? 'bg-sky-600 text-white shadow-sm'
                                : 'text-slate-600 hover:text-sky-800 hover:bg-sky-50'
                                }`}
                        >
                            {tab.label}
                        </button>
                    ))}
                </nav>

                <div className="flex items-center gap-3">
                    <div className="bg-white border border-sky-200 px-3 py-1.5 rounded-lg flex items-center gap-2 text-xs">
                        <span className="relative flex h-2.5 w-2.5">
                            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                            <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-emerald-500"></span>
                        </span>
                        <span className="font-mono text-slate-600">
                            {forecastOffset > 0 ? `Forecast Mode (+${forecastOffset}m)` : `Live Sync (${telemetry?.timestamp || 'Active'})`}
                        </span>
                    </div>
                    <button className="bg-rose-500 hover:bg-rose-600 text-white text-xs px-3 py-1.5 rounded-lg font-medium transition">
                        Logout
                    </button>
                </div>
            </header>

            {/* Main Container */}
            <main className="max-w-7xl mx-auto px-6 pt-6">

                {/* MODULE 1: DASHBOARD */}
                {activeTab === 'dashboard' && (
                    <div className="space-y-6">
                        <div className="flex justify-between items-center flex-wrap gap-4">
                            <h1 className="text-2xl font-bold text-slate-800">Operational Analytics Dashboard</h1>

                            <div className="flex items-center gap-3 flex-wrap">
                                <div className="relative">
                                    <Search className="h-4 w-4 absolute left-3 top-2.5 text-slate-400" />
                                    <input
                                        type="text"
                                        placeholder="Search station name..."
                                        value={searchTerm}
                                        onChange={(e) => setSearchTerm(e.target.value)}
                                        className="bg-white border border-slate-200 pl-9 pr-4 py-1.5 rounded-lg text-xs w-56 focus:outline-none focus:ring-2 focus:ring-sky-500"
                                    />
                                </div>

                                <div className="bg-white border border-slate-200 px-3 py-1 rounded-lg flex items-center gap-2 text-xs shadow-sm">
                                    <span className="text-slate-500 font-medium">Future Forecast:</span>
                                    {[0, 15, 30, 60].map((mins) => (
                                        <button
                                            key={mins}
                                            onClick={() => handleForecastSelect(mins)}
                                            className={`px-2.5 py-1 rounded font-mono text-xs font-semibold transition ${forecastOffset === mins
                                                ? 'bg-sky-600 text-white shadow-sm'
                                                : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                                                }`}
                                        >
                                            {mins === 0 ? 'Live' : `+${mins}m`}
                                        </button>
                                    ))}
                                    {forecastOffset > 0 && (
                                        <button
                                            onClick={() => handleForecastSelect(0)}
                                            className="bg-amber-100 text-amber-800 border border-amber-300 px-2.5 py-1 rounded text-xs font-bold flex items-center gap-1 hover:bg-amber-200 transition"
                                        >
                                            <RefreshCw className="h-3 w-3" /> Reset Live
                                        </button>
                                    )}
                                </div>
                            </div>
                        </div>

                        {forecastOffset > 0 && (
                            <div className="bg-amber-50 border border-amber-300 rounded-xl p-4 flex justify-between items-center text-xs text-amber-900 shadow-sm">
                                <div className="flex items-center gap-2 font-semibold">
                                    <Clock className="h-4 w-4 text-amber-600" />
                                    <span>🔮 FUTURE FORECAST ACTIVE (+{forecastOffset} Minutes) — Displaying predicted G-Line train positions and station crowd densities.</span>
                                </div>
                                <button
                                    onClick={() => handleForecastSelect(0)}
                                    className="bg-amber-600 text-white px-3 py-1 rounded font-bold hover:bg-amber-700 transition"
                                >
                                    Switch Back to Live Feed
                                </button>
                            </div>
                        )}

                        {/* Top KPI Cards */}
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                            <div className="bg-white border border-sky-100 rounded-xl p-5 shadow-sm flex items-center justify-between">
                                <div>
                                    <p className="text-xs text-slate-500 font-semibold uppercase tracking-wider">Monitored Stations</p>
                                    <p className="text-3xl font-extrabold text-slate-800 mt-1">{telemetry?.total_stations || 21}</p>
                                    <p className="text-xs text-sky-600 font-medium mt-1">G-Line Route Coverage</p>
                                </div>
                                <div className="p-3 bg-sky-100 text-sky-600 rounded-xl"><Train className="h-7 w-7" /></div>
                            </div>

                            <div className="bg-white border border-sky-100 rounded-xl p-5 shadow-sm flex items-center justify-between">
                                <div>
                                    <p className="text-xs text-slate-500 font-semibold uppercase tracking-wider">Active Trains (Two-Way)</p>
                                    <p className="text-3xl font-extrabold text-slate-800 mt-1">{telemetry?.active_train_count || 42}</p>
                                    <p className="text-xs text-emerald-600 font-medium mt-1">
                                        {telemetry?.period_info?.period_name || 'Standard Service'}
                                    </p>
                                </div>
                                <div className="p-3 bg-emerald-100 text-emerald-600 rounded-xl"><Activity className="h-7 w-7" /></div>
                            </div>

                            <div className="bg-white border border-sky-100 rounded-xl p-5 shadow-sm flex items-center justify-between">
                                <div>
                                    <p className="text-xs text-slate-500 font-semibold uppercase tracking-wider">High Density Alert Stations</p>
                                    <p className="text-3xl font-extrabold text-rose-600 mt-1">{telemetry?.high_alert_stations || 0}</p>
                                    <p className="text-xs text-rose-500 font-medium mt-1">Immediate Attention Required</p>
                                </div>
                                <div className="p-3 bg-rose-100 text-rose-600 rounded-xl"><AlertTriangle className="h-7 w-7" /></div>
                            </div>
                        </div>

                        {/* Frequency Banner */}
                        <div className="bg-sky-50 border border-sky-200 rounded-xl p-4 flex flex-wrap justify-between items-center gap-4">
                            <div className="flex items-center gap-3">
                                <Clock className="h-5 w-5 text-sky-600" />
                                <div>
                                    <span className="text-xs text-sky-800 font-semibold">Active Frequency Rule:</span>
                                    <p className="text-sm font-bold text-slate-800">{telemetry?.period_info?.action}</p>
                                </div>
                            </div>
                            <div className="bg-white border border-sky-200 px-4 py-2 rounded-lg text-center">
                                <span className="text-xs text-slate-500">Current Headway</span>
                                <p className="text-lg font-extrabold text-sky-700">Every {telemetry?.period_info?.recommended_headway_min || 8} Mins</p>
                            </div>
                        </div>

                        {/* LIVE G-LINE TRACK ROUTE MAP */}
                        <GLineTrackMap
                            stations={telemetry?.station_performance || []}
                            trains={telemetry?.trains || []}
                            onStationClick={(name) => setSearchTerm(name)}
                        />

                        {/* Train Schedule Performance Table */}
                        <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm">
                            <h2 className="text-lg font-bold text-slate-800 mb-4">Train Schedule Performance & Station Density</h2>
                            <div className="overflow-x-auto">
                                <table className="w-full text-left border-collapse text-xs">
                                    <thead>
                                        <tr className="border-b border-slate-200 text-slate-500 uppercase font-semibold bg-slate-50/80">
                                            <th className="py-3 px-4">Station Name</th>
                                            <th className="py-3 px-4">Trains Running at Station</th>
                                            <th className="py-3 px-4">Occupancy / Capacity</th>
                                            <th className="py-3 px-4">Crowd Density</th>
                                            <th className="py-3 px-4">Inflow / Outflow</th>
                                            <th className="py-3 px-4">Status</th>
                                            <th className="py-3 px-4 text-right">Quick Alert</th>
                                        </tr>
                                    </thead>
                                    <tbody className="divide-y divide-slate-100">
                                        {filteredStations.map((s: any) => (
                                            <tr key={s.station_name} className="hover:bg-sky-50/50 transition">
                                                <td className="py-3 px-4 font-bold text-slate-800">{s.station_name}</td>
                                                <td className="py-3 px-4 font-mono text-sky-700 font-semibold">{s.trains_running}</td>
                                                <td className="py-3 px-4">
                                                    <span className="font-semibold text-slate-700">{s.avg_occupancy_pct}%</span>
                                                    <span className="text-slate-400 font-mono text-[10px]"> (1200 Max)</span>
                                                </td>
                                                <td className="py-3 px-4">
                                                    <div className="w-28 bg-slate-100 h-2 rounded-full overflow-hidden">
                                                        <div
                                                            className={`h-full ${s.crowd_density_pct >= 80 ? 'bg-rose-500' :
                                                                s.crowd_density_pct >= 55 ? 'bg-amber-500' : 'bg-emerald-500'
                                                                }`}
                                                            style={{ width: `${s.crowd_density_pct}%` }}
                                                        ></div>
                                                    </div>
                                                    <span className="text-[10px] text-slate-500 font-mono">{s.crowd_density_pct}%</span>
                                                </td>
                                                <td className="py-3 px-4 font-mono text-slate-600">
                                                    +{s.inflow} / -{s.outflow}
                                                </td>
                                                <td className="py-3 px-4">
                                                    <span className={`px-2.5 py-1 rounded text-[10px] font-bold ${s.status === 'HIGH ALERT' ? 'bg-rose-100 text-rose-700 border border-rose-200' :
                                                        s.status === 'MODERATE' ? 'bg-amber-100 text-amber-700 border border-amber-200' :
                                                            'bg-emerald-100 text-emerald-700 border border-emerald-200'
                                                        }`}>
                                                        {s.status}
                                                    </span>
                                                </td>
                                                <td className="py-3 px-4 text-right">
                                                    <button
                                                        onClick={() => {
                                                            setManualStation(s.station_name);
                                                            handleManualAlert();
                                                        }}
                                                        className="bg-rose-50 text-rose-600 hover:bg-rose-100 border border-rose-200 px-2.5 py-1 rounded text-[10px] font-bold transition flex items-center gap-1 ml-auto"
                                                    >
                                                        <Bell className="h-3 w-3" /> Alert
                                                    </button>
                                                </td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    </div>
                )}

                {/* MODULE 2: CROWD MONITORING */}
                {activeTab === 'crowd' && (
                    <div className="space-y-6">
                        <div className="flex justify-between items-center flex-wrap gap-4">
                            <h1 className="text-2xl font-bold text-slate-800">Crowd Monitoring & Train Heatmap Analysis</h1>

                            <div className="relative">
                                <Search className="h-4 w-4 absolute left-3 top-2.5 text-slate-400" />
                                <input
                                    type="text"
                                    placeholder="Search train or station..."
                                    value={searchTerm}
                                    onChange={(e) => setSearchTerm(e.target.value)}
                                    className="bg-white border border-slate-200 pl-9 pr-4 py-1.5 rounded-lg text-xs w-64 focus:outline-none focus:ring-2 focus:ring-sky-500"
                                />
                            </div>
                        </div>

                        <div className="bg-white border border-slate-200 p-4 rounded-xl shadow-sm flex items-center justify-between flex-wrap gap-4 text-xs">
                            <span className="font-bold text-slate-700">Train Heatmap Classification:</span>
                            <div className="flex items-center gap-6">
                                <div className="flex items-center gap-2">
                                    <span className="h-3 w-3 rounded-full bg-emerald-500"></span>
                                    <span className="text-slate-600">Green = Low Density (&lt; 55%)</span>
                                </div>
                                <div className="flex items-center gap-2">
                                    <span className="h-3 w-3 rounded-full bg-amber-500"></span>
                                    <span className="text-slate-600">Yellow = Mid Density (55% - 80%)</span>
                                </div>
                                <div className="flex items-center gap-2">
                                    <span className="h-3 w-3 rounded-full bg-rose-500"></span>
                                    <span className="text-slate-600">Red = High Density (&gt; 80%)</span>
                                </div>
                            </div>
                        </div>

                        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
                            {filteredTrains.slice(0, 24).map((t: any) => (
                                <div
                                    key={t.train_id}
                                    className={`border rounded-xl p-4 transition shadow-sm bg-white ${t.occupancy_pct >= 80 ? 'border-rose-300 bg-rose-50/20' :
                                        t.occupancy_pct >= 55 ? 'border-amber-300 bg-amber-50/20' : 'border-emerald-300 bg-emerald-50/20'
                                        }`}
                                >
                                    <div className="flex justify-between items-center mb-2">
                                        <span className="font-extrabold text-slate-800 text-base">{t.train_id}</span>
                                        <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${t.occupancy_pct >= 80 ? 'bg-rose-500 text-white' :
                                            t.occupancy_pct >= 55 ? 'bg-amber-500 text-white' : 'bg-emerald-500 text-white'
                                            }`}>
                                            {t.occupancy_pct}%
                                        </span>
                                    </div>

                                    <p className="text-xs text-slate-500 font-mono mb-1">{t.route}</p>
                                    <p className="text-xs text-slate-600 mb-1">Station: <span className="font-semibold text-slate-800">{t.current_station}</span></p>
                                    <p className="text-xs text-slate-600 mb-3">Load: <span className="font-mono text-slate-800">{t.passenger_count} / {t.capacity}</span></p>

                                    <button
                                        onClick={() => {
                                            setManualStation(t.current_station);
                                            handleManualAlert();
                                        }}
                                        className="w-full bg-sky-600 hover:bg-sky-700 text-white text-xs py-1.5 rounded-lg font-semibold transition flex items-center justify-center gap-1"
                                    >
                                        <Bell className="h-3.5 w-3.5" /> Dispatch Density Alert
                                    </button>
                                </div>
                            ))}
                        </div>
                    </div>
                )}

                {/* MODULE 3: SCHEDULING */}
                {activeTab === 'scheduling' && (
                    <div className="space-y-6">
                        <h1 className="text-2xl font-bold text-slate-800">Train Scheduling & Frequency Adjustment</h1>

                        <div className="bg-white border border-sky-200 rounded-xl p-6 shadow-sm space-y-4">
                            <h2 className="text-base font-bold text-slate-800 flex items-center gap-2">
                                <Zap className="h-5 w-5 text-sky-600" /> Cascade Line Frequency Adjuster
                            </h2>
                            <p className="text-xs text-slate-500">
                                Updating frequency or delay for a specific train automatically updates schedule timings for following trains behind it on the G-Line route.
                            </p>

                            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                                <div>
                                    <label className="text-xs text-slate-600 font-semibold mb-1 block">Select Train ID:</label>
                                    <select
                                        value={selectedTrainId}
                                        onChange={(e) => setSelectedTrainId(e.target.value)}
                                        className="w-full bg-slate-50 border border-slate-200 rounded-lg p-2 text-xs focus:ring-2 focus:ring-sky-500"
                                    >
                                        {telemetry?.trains?.map((t: any) => (
                                            <option key={t.train_id} value={t.train_id}>{t.train_id} ({t.current_station})</option>
                                        ))}
                                    </select>
                                </div>

                                <div>
                                    <label className="text-xs text-slate-600 font-semibold mb-1 block">Set Delay (Minutes):</label>
                                    <input
                                        type="number"
                                        value={inputDelay}
                                        onChange={(e) => setInputDelay(Number(e.target.value))}
                                        className="w-full bg-slate-50 border border-slate-200 rounded-lg p-2 text-xs focus:ring-2 focus:ring-sky-500"
                                    />
                                </div>

                                <div>
                                    <label className="text-xs text-slate-600 font-semibold mb-1 block">Line Headway (Minutes):</label>
                                    <input
                                        type="number"
                                        value={inputHeadway}
                                        onChange={(e) => setInputHeadway(Number(e.target.value))}
                                        className="w-full bg-slate-50 border border-slate-200 rounded-lg p-2 text-xs focus:ring-2 focus:ring-sky-500"
                                    />
                                </div>
                            </div>

                            <button
                                onClick={handleScheduleAdjust}
                                className="bg-sky-600 hover:bg-sky-700 text-white text-xs px-5 py-2.5 rounded-lg font-bold transition flex items-center gap-2"
                            >
                                <Zap className="h-4 w-4" /> Apply Cascade Frequency Adjustment
                            </button>
                        </div>

                        <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm">
                            <h2 className="text-lg font-bold text-slate-800 mb-4">G-Line Master Train Timetable</h2>
                            <div className="overflow-x-auto">
                                <table className="w-full text-left border-collapse text-xs">
                                    <thead>
                                        <tr className="border-b border-slate-200 text-slate-500 uppercase font-semibold bg-slate-50/80">
                                            <th className="py-3 px-4">Train ID</th>
                                            <th className="py-3 px-4">Line</th>
                                            <th className="py-3 px-4">Route</th>
                                            <th className="py-3 px-4">Frequency</th>
                                            <th className="py-3 px-4">Occupancy</th>
                                            <th className="py-3 px-4">Delay</th>
                                            <th className="py-3 px-4 text-right">Frequency Adjustment</th>
                                        </tr>
                                    </thead>
                                    <tbody className="divide-y divide-slate-100 font-mono">
                                        {telemetry?.trains?.slice(0, 15).map((t: any) => (
                                            <tr key={t.train_id} className="hover:bg-sky-50/50 transition">
                                                <td className="py-3 px-4 font-bold text-sky-800">{t.train_id}</td>
                                                <td className="py-3 px-4 font-semibold text-emerald-600">{t.line}</td>
                                                <td className="py-3 px-4 text-slate-600 font-sans">{t.route}</td>
                                                <td className="py-3 px-4 text-slate-700">Every {t.scheduled_headway_min}m</td>
                                                <td className="py-3 px-4 font-bold text-slate-800">{t.occupancy_pct}%</td>
                                                <td className="py-3 px-4">
                                                    <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${t.delay_min > 0 ? 'bg-rose-100 text-rose-700' : 'bg-emerald-100 text-emerald-700'
                                                        }`}>
                                                        {t.delay_min > 0 ? `+${t.delay_min} min Delay` : 'On Time'}
                                                    </span>
                                                </td>
                                                <td className="py-3 px-4 text-right font-sans">
                                                    <button
                                                        onClick={() => {
                                                            setSelectedTrainId(t.train_id);
                                                            handleScheduleAdjust();
                                                        }}
                                                        className="bg-sky-50 text-sky-700 hover:bg-sky-100 border border-sky-200 px-3 py-1 rounded text-xs font-semibold transition"
                                                    >
                                                        Update
                                                    </button>
                                                </td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    </div>
                )}

                {/* MODULE 4: ALERTS */}
                {activeTab === 'alerts' && (
                    <div className="space-y-6">
                        <h1 className="text-2xl font-bold text-slate-800">Alert & Emergency Announcement Module</h1>

                        <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm space-y-3">
                            <h2 className="text-sm font-bold text-slate-800">Broadcast System Announcement</h2>
                            <div className="flex gap-3">
                                <input
                                    type="text"
                                    placeholder="Enter public alert or operational emergency update..."
                                    value={broadcastMsg}
                                    onChange={(e) => setBroadcastMsg(e.target.value)}
                                    className="bg-slate-50 border border-slate-200 text-slate-800 px-4 py-2.5 rounded-lg text-xs w-full focus:outline-none focus:ring-2 focus:ring-rose-500"
                                />
                                <button
                                    onClick={handleBroadcast}
                                    className="bg-rose-600 hover:bg-rose-700 text-white px-6 py-2.5 rounded-lg text-xs font-bold transition shrink-0 flex items-center gap-1"
                                >
                                    <Send className="h-4 w-4" /> Broadcast
                                </button>
                            </div>
                        </div>

                        <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm">
                            <h2 className="text-base font-bold text-slate-800 mb-4">Live Generated Alerts & Audit Logs</h2>
                            <div className="space-y-3">
                                {telemetry?.alerts?.map((a: any) => (
                                    <div key={a.id} className="bg-slate-50 border border-slate-200 rounded-lg p-4 flex justify-between items-start">
                                        <div>
                                            <div className="flex items-center gap-2 mb-1">
                                                <span className={`px-2 py-0.5 text-[10px] rounded font-extrabold uppercase ${a.severity === 'HIGH' ? 'bg-rose-500 text-white' :
                                                    a.severity === 'WARNING' ? 'bg-amber-500 text-white' : 'bg-sky-600 text-white'
                                                    }`}>
                                                    {a.severity}
                                                </span>
                                                <span className="text-xs font-bold text-slate-800">{a.category}</span>
                                            </div>
                                            <p className="text-xs text-slate-600">{a.message}</p>
                                        </div>
                                        <span className="text-[10px] font-mono text-slate-400 shrink-0">{a.timestamp}</span>
                                    </div>
                                ))}
                            </div>
                        </div>
                    </div>
                )}

                {/* MODULE 5: ANALYSIS */}
                {activeTab === 'analysis' && (
                    <div className="space-y-6">
                        <div className="flex justify-between items-center flex-wrap gap-4">
                            <h1 className="text-2xl font-bold text-slate-800">Station Performance Reporting Module</h1>

                            <div className="flex items-center gap-2 bg-white border border-slate-200 px-3 py-1.5 rounded-lg">
                                <span className="text-xs text-slate-600 font-semibold">Select Day of Month:</span>
                                <select
                                    value={selectedDay}
                                    onChange={(e) => {
                                        const day = Number(e.target.value);
                                        setSelectedDay(day);
                                        fetchAnalysis(day);
                                    }}
                                    className="bg-slate-50 border border-slate-200 text-xs px-2 py-1 rounded font-bold text-sky-800 focus:outline-none"
                                >
                                    {Array.from({ length: 31 }, (_, i) => i + 1).map((d) => (
                                        <option key={d} value={d}>Day {d}</option>
                                    ))}
                                </select>
                            </div>
                        </div>

                        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                            <div className="bg-white border border-sky-100 rounded-xl p-5 shadow-sm">
                                <p className="text-xs text-slate-500 uppercase font-semibold">Average Crowd Density</p>
                                <p className="text-3xl font-extrabold text-sky-700 mt-1">
                                    {analysisData?.kpis?.avg_crowd_density_pct || 64.2}%
                                </p>
                                <p className="text-xs text-slate-400 mt-1">Selected Day Average</p>
                            </div>

                            <div className="bg-white border border-sky-100 rounded-xl p-5 shadow-sm">
                                <p className="text-xs text-slate-500 uppercase font-semibold">Delay Frequency</p>
                                <p className="text-3xl font-extrabold text-amber-600 mt-1">
                                    {analysisData?.kpis?.delay_frequency_per_hr || 3.4} / hr
                                </p>
                                <p className="text-xs text-slate-400 mt-1">Average Incidents</p>
                            </div>

                            <div className="bg-white border border-sky-100 rounded-xl p-5 shadow-sm">
                                <p className="text-xs text-slate-500 uppercase font-semibold">Daily Throughput</p>
                                <p className="text-3xl font-extrabold text-emerald-600 mt-1">
                                    {analysisData?.kpis?.daily_throughput_passengers?.toLocaleString() || '245,000'}
                                </p>
                                <p className="text-xs text-slate-400 mt-1">Total Passengers</p>
                            </div>
                        </div>

                        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                            <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm">
                                <h2 className="text-base font-bold text-slate-800 mb-4">24-Hour Passenger Density Curve (Day {selectedDay})</h2>
                                <div className="h-64">
                                    <ResponsiveContainer width="100%" height="100%">
                                        <LineChart data={analysisData?.hourly_density || []}>
                                            <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                                            <XAxis dataKey="hour" stroke="#94a3b8" fontSize={10} />
                                            <YAxis stroke="#94a3b8" fontSize={10} unit="%" />
                                            <Tooltip />
                                            <Line type="monotone" dataKey="density" stroke="#0284c7" strokeWidth={3} dot={{ r: 3 }} />
                                        </LineChart>
                                    </ResponsiveContainer>
                                </div>
                            </div>

                            <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm">
                                <h2 className="text-base font-bold text-slate-800 mb-4">Station Throughput Breakdown (Day {selectedDay})</h2>
                                <div className="h-64">
                                    <ResponsiveContainer width="100%" height="100%">
                                        <BarChart data={analysisData?.station_breakdown || []}>
                                            <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                                            <XAxis dataKey="station" stroke="#94a3b8" fontSize={9} interval={0} angle={-25} textAnchor="end" />
                                            <YAxis stroke="#94a3b8" fontSize={10} />
                                            <Tooltip />
                                            <Bar dataKey="throughput" fill="#10b981" radius={[4, 4, 0, 0]} />
                                        </BarChart>
                                    </ResponsiveContainer>
                                </div>
                            </div>
                        </div>
                    </div>
                )}

            </main>
        </div>
    );
}