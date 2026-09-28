"use client";

import { useEffect, useState } from "react";
import {
  Users,
  Train,
  ArrowUpRight,
  ArrowDownRight,
  Activity,
  Radio,
  Wifi,
  WifiOff,
  Filter,
  CheckCircle2,
  AlertTriangle,
  RefreshCw,
  Settings2,
  ExternalLink,
  CreditCard,
  Gauge,
  SlidersHorizontal,
} from "lucide-react";
import { api } from "@/lib/api";
import { socketClient } from "@/lib/socket";
import {
  PassengerTapEvent,
  TrainPassengerTelemetry,
  StationPassengerMetric,
  GtfsRtStatus,
  GtfsRtConfig,
} from "@/types";

export default function RealtimePassengersPage() {
  const [tapEvents, setTapEvents] = useState<PassengerTapEvent[]>([]);
  const [trains, setTrains] = useState<TrainPassengerTelemetry[]>([]);
  const [stationMetrics, setStationMetrics] = useState<StationPassengerMetric[]>([]);
  const [gtfsStatus, setGtfsStatus] = useState<GtfsRtStatus | null>(null);
  
  const [systemInflow, setSystemInflow] = useState<number>(0);
  const [systemOutflow, setSystemOutflow] = useState<number>(0);
  const [totalInTransit, setTotalInTransit] = useState<number>(0);

  // Filters
  const [selectedLine, setSelectedLine] = useState<string>("ALL");
  const [eventTypeFilter, setEventTypeFilter] = useState<string>("ALL");
  const [loading, setLoading] = useState<boolean>(true);

  // GTFS-RT Modal State
  const [isModalOpen, setIsModalOpen] = useState<boolean>(false);
  const [gtfsUrl, setGtfsUrl] = useState<string>("");
  const [gtfsApiKey, setGtfsApiKey] = useState<string>("");
  const [gtfsProvider, setGtfsProvider] = useState<string>("BART Real-Time API");
  const [gtfsSaving, setGtfsSaving] = useState<boolean>(false);
  const [configFeedback, setConfigFeedback] = useState<string | null>(null);

  const PRESET_FEEDS = [
    {
      name: "BART Live Telemetry (San Francisco)",
      url: "https://api.bart.gov/gtfsrt/trips.aspx",
      key: "",
      desc: "Bay Area Rapid Transit GTFS-RT Trip Updates",
    },
    {
      name: "MTA NY Subway Live GTFS-RT",
      url: "https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs",
      key: "",
      desc: "New York City Transit Subway realtime feed",
    },
    {
      name: "MBTA Rapid Transit (Boston)",
      url: "https://cdn.mbta.com/realtime/VehiclePositions.json",
      key: "",
      desc: "Massachusetts Bay Transportation Authority Vehicle Positions",
    },
  ];

  const loadInitialData = async () => {
    try {
      setLoading(true);
      const data = await api.getLivePassengerStream();
      setTapEvents(data.recent_tap_events || []);
      setTrains(data.trains || []);
      setStationMetrics(data.station_metrics || []);
      setGtfsStatus(data.gtfs_rt_status || null);
      setSystemInflow(data.system_inflow_ppm || 0);
      setSystemOutflow(data.system_outflow_ppm || 0);
      setTotalInTransit(data.total_active_passengers_in_transit || 0);
    } catch (err) {
      console.error("Error loading passenger stream:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadInitialData();

    // Subscribe to WebSocket live telemetry
    const unsubscribe = socketClient.subscribe((msg: any) => {
      if (msg.event === "TELEMETRY_UPDATE" && msg.passengers) {
        const p = msg.passengers;
        if (p.recent_tap_events) setTapEvents(p.recent_tap_events);
        if (p.trains) setTrains(p.trains);
        if (p.station_metrics) setStationMetrics(p.station_metrics);
        if (p.gtfs_rt_status) setGtfsStatus(p.gtfs_rt_status);
        if (p.system_inflow_ppm !== undefined) setSystemInflow(p.system_inflow_ppm);
        if (p.system_outflow_ppm !== undefined) setSystemOutflow(p.system_outflow_ppm);
        if (p.total_active_passengers_in_transit !== undefined) {
          setTotalInTransit(p.total_active_passengers_in_transit);
        }
      }
    });

    return () => unsubscribe();
  }, []);

  const handleApplyGtfsConfig = async (presetUrl?: string, presetName?: string) => {
    try {
      setGtfsSaving(true);
      setConfigFeedback(null);
      const urlToUse = presetUrl || gtfsUrl;
      const nameToUse = presetName || gtfsProvider;

      const payload: GtfsRtConfig = {
        feed_url: urlToUse,
        api_key: gtfsApiKey || undefined,
        provider_name: nameToUse,
        is_enabled: true,
      };

      const res = await api.configureGtfsRt(payload);
      setGtfsStatus(res);
      setConfigFeedback(res.status_message);
      if (res.is_active) {
        setTimeout(() => setIsModalOpen(false), 1200);
      }
    } catch (err: any) {
      setConfigFeedback(`Failed to connect: ${err.message}`);
    } finally {
      setGtfsSaving(false);
    }
  };

  const handleResetToSimulation = async () => {
    try {
      setGtfsSaving(true);
      const res = await api.configureGtfsRt({
        feed_url: "",
        provider_name: "Simulated AFC/APC Real-Time Engine",
        is_enabled: false,
      });
      setGtfsStatus(res);
      setConfigFeedback("Reverted to internal high-velocity simulation engine.");
      setTimeout(() => setIsModalOpen(false), 1000);
    } catch (err: any) {
      setConfigFeedback(`Reset failed: ${err.message}`);
    } finally {
      setGtfsSaving(false);
    }
  };

  const filteredTrains = trains.filter(
    (t) => selectedLine === "ALL" || t.line_name === selectedLine
  );

  const filteredTaps = tapEvents.filter((tap) => {
    const matchesLine = selectedLine === "ALL" || tap.line_name === selectedLine;
    const matchesType = eventTypeFilter === "ALL" || tap.event_type === eventTypeFilter;
    return matchesLine && matchesType;
  });

  const getCarColor = (crowdLevel: string) => {
    switch (crowdLevel) {
      case "CRUSH_LOAD":
        return "bg-rose-500/20 border-rose-500/50 text-rose-300";
      case "CROWDED":
        return "bg-amber-500/20 border-amber-500/50 text-amber-300";
      case "STANDING_ROOM":
        return "bg-blue-500/20 border-blue-500/50 text-blue-300";
      default:
        return "bg-emerald-500/20 border-emerald-500/50 text-emerald-300";
    }
  };

  return (
    <div className="space-y-6">
      {/* Header & Controls */}
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4 border-b border-slate-800 pb-5">
        <div>
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-cyan-500/20 border border-cyan-500/30 flex items-center justify-center text-cyan-400">
              <Users className="w-5 h-5 text-cyan-400" />
            </div>
            <div>
              <h1 className="text-2xl font-black text-white flex items-center gap-2.5">
                Real-Time Passenger Data & Telemetry
                <span className="flex h-2.5 w-2.5 relative">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                  <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-emerald-500"></span>
                </span>
              </h1>
              <p className="text-xs text-slate-400 mt-0.5">
                Live Automated Fare Collection (AFC turnstile taps), carriage-level passenger loads (APC), and GTFS-RT feed ingestion
              </p>
            </div>
          </div>
        </div>

        {/* Global Controls & GTFS-RT Status Pill */}
        <div className="flex flex-wrap items-center gap-3">
          <button
            onClick={() => setIsModalOpen(true)}
            className={`flex items-center gap-2 px-3.5 py-1.5 rounded-lg border text-xs font-semibold transition-all ${
              gtfsStatus?.is_active
                ? "bg-emerald-500/10 border-emerald-500/40 text-emerald-400 hover:bg-emerald-500/20"
                : "bg-slate-800/80 border-slate-700 text-slate-300 hover:bg-slate-800 hover:border-cyan-500/50"
            }`}
          >
            {gtfsStatus?.is_active ? (
              <Wifi className="w-4 h-4 text-emerald-400" />
            ) : (
              <Radio className="w-4 h-4 text-cyan-400" />
            )}
            <span>
              {gtfsStatus?.is_active ? "GTFS-RT Connected" : "GTFS-RT Connector"}
            </span>
            <span className="text-[10px] px-1.5 py-0.5 rounded bg-slate-900 border border-slate-700 text-slate-400">
              Configure
            </span>
          </button>

          {/* Line Filter */}
          <div className="flex items-center gap-1 bg-[#0d1424] border border-slate-800 p-1 rounded-lg text-xs">
            <button
              onClick={() => setSelectedLine("ALL")}
              className={`px-3 py-1 rounded font-medium transition-all ${
                selectedLine === "ALL" ? "bg-cyan-600 text-white" : "text-slate-400 hover:text-white"
              }`}
            >
              All Lines
            </button>
            <button
              onClick={() => setSelectedLine("Red Line")}
              className={`px-3 py-1 rounded font-medium transition-all ${
                selectedLine === "Red Line" ? "bg-rose-600 text-white" : "text-slate-400 hover:text-white"
              }`}
            >
              Red Line
            </button>
            <button
              onClick={() => setSelectedLine("Blue Line")}
              className={`px-3 py-1 rounded font-medium transition-all ${
                selectedLine === "Blue Line" ? "bg-blue-600 text-white" : "text-slate-400 hover:text-white"
              }`}
            >
              Blue Line
            </button>
          </div>
        </div>
      </div>

      {/* KPI Stat Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Total In-Transit */}
        <div className="bg-[#0d1424] border border-slate-800 rounded-xl p-4 flex items-center justify-between shadow-lg">
          <div>
            <p className="text-[11px] font-semibold uppercase tracking-wider text-slate-400">
              Active In-Transit Passengers
            </p>
            <p className="text-2xl font-black text-white mt-1">
              {totalInTransit.toLocaleString()}
            </p>
            <p className="text-[11px] text-cyan-400 mt-1 flex items-center gap-1">
              <Train className="w-3 h-3" /> Across {trains.length} active trains
            </p>
          </div>
          <div className="w-12 h-12 rounded-xl bg-cyan-500/10 border border-cyan-500/20 flex items-center justify-center text-cyan-400">
            <Users className="w-6 h-6" />
          </div>
        </div>

        {/* System Inflow */}
        <div className="bg-[#0d1424] border border-slate-800 rounded-xl p-4 flex items-center justify-between shadow-lg">
          <div>
            <p className="text-[11px] font-semibold uppercase tracking-wider text-slate-400">
              System Inflow (Tap-Ins)
            </p>
            <p className="text-2xl font-black text-emerald-400 mt-1">
              {systemInflow.toLocaleString()} <span className="text-xs font-normal text-slate-400">PPM</span>
            </p>
            <p className="text-[11px] text-slate-400 mt-1 flex items-center gap-1">
              <ArrowUpRight className="w-3 h-3 text-emerald-400" /> Platform entries
            </p>
          </div>
          <div className="w-12 h-12 rounded-xl bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center text-emerald-400">
            <ArrowUpRight className="w-6 h-6" />
          </div>
        </div>

        {/* System Outflow */}
        <div className="bg-[#0d1424] border border-slate-800 rounded-xl p-4 flex items-center justify-between shadow-lg">
          <div>
            <p className="text-[11px] font-semibold uppercase tracking-wider text-slate-400">
              System Outflow (Tap-Outs)
            </p>
            <p className="text-2xl font-black text-amber-400 mt-1">
              {systemOutflow.toLocaleString()} <span className="text-xs font-normal text-slate-400">PPM</span>
            </p>
            <p className="text-[11px] text-slate-400 mt-1 flex items-center gap-1">
              <ArrowDownRight className="w-3 h-3 text-amber-400" /> Turnstile exits
            </p>
          </div>
          <div className="w-12 h-12 rounded-xl bg-amber-500/10 border border-amber-500/20 flex items-center justify-center text-amber-400">
            <ArrowDownRight className="w-6 h-6" />
          </div>
        </div>

        {/* Net Flux & Data Source */}
        <div className="bg-[#0d1424] border border-slate-800 rounded-xl p-4 flex items-center justify-between shadow-lg">
          <div>
            <p className="text-[11px] font-semibold uppercase tracking-wider text-slate-400">
              Feed Engine & Net Flux
            </p>
            <p className={`text-2xl font-black mt-1 ${systemInflow >= systemOutflow ? "text-cyan-400" : "text-amber-400"}`}>
              {systemInflow - systemOutflow > 0 ? `+${systemInflow - systemOutflow}` : systemInflow - systemOutflow} <span className="text-xs font-normal text-slate-400">net/min</span>
            </p>
            <p className="text-[11px] text-slate-400 mt-1 truncate max-w-[150px]">
              {gtfsStatus?.provider_name || "AFC/APC Stream"}
            </p>
          </div>
          <div className="w-12 h-12 rounded-xl bg-purple-500/10 border border-purple-500/20 flex items-center justify-center text-purple-400">
            <Activity className="w-6 h-6" />
          </div>
        </div>
      </div>

      {/* Main Content Layout: Trains APC Load + Live Gate Tap Ticker */}
      <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
        {/* Left 2 Cols: Train Carriage (APC) Passenger Load Visualizer */}
        <div className="xl:col-span-2 space-y-4">
          <div className="bg-[#0d1424] border border-slate-800 rounded-xl p-5 shadow-lg">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3 mb-4">
              <div>
                <h2 className="text-base font-bold text-white flex items-center gap-2">
                  <Train className="w-4 h-4 text-cyan-400" />
                  Live Train Carriage Passenger Load Visualizer (APC Sensors)
                </h2>
                <p className="text-xs text-slate-400 mt-0.5">
                  Automated Passenger Counters (APC) transmitting real-time passenger counts per carriage
                </p>
              </div>
              <div className="text-xs text-slate-400 flex items-center gap-1.5">
                <span className="inline-block w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
                <span>{filteredTrains.length} Active Trains</span>
              </div>
            </div>

            {/* Train List with Car Breakdown */}
            <div className="space-y-4">
              {filteredTrains.map((train) => {
                const isRed = train.line_name.includes("Red");
                return (
                  <div
                    key={train.train_id}
                    className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 hover:border-slate-700 transition-all"
                  >
                    {/* Train Info Header */}
                    <div className="flex flex-wrap items-center justify-between gap-2 mb-3">
                      <div className="flex items-center gap-2.5">
                        <span
                          className={`px-2 py-0.5 rounded text-[11px] font-bold ${
                            isRed ? "bg-rose-500/20 text-rose-400 border border-rose-500/30" : "bg-blue-500/20 text-blue-400 border border-blue-500/30"
                          }`}
                        >
                          {train.train_code}
                        </span>
                        <span className="text-xs font-semibold text-white">
                          {train.line_name}
                        </span>
                        <span className="text-slate-600">•</span>
                        <span className="text-xs text-slate-400">
                          {train.current_station} → <span className="text-slate-200">{train.next_station}</span>
                        </span>
                      </div>

                      <div className="flex items-center gap-3 text-xs">
                        <span className="text-slate-400">
                          Speed: <strong className="text-slate-200">{train.speed_kmh} km/h</strong>
                        </span>
                        <span className="text-slate-400">
                          ETA: <strong className="text-cyan-400">{train.eta_seconds}s</strong>
                        </span>
                        <span
                          className={`px-2 py-0.5 rounded-full text-[10px] font-bold uppercase ${
                            train.status === "BOARDING"
                              ? "bg-amber-500/20 text-amber-400 border border-amber-500/30 animate-pulse"
                              : train.status === "AT_STATION"
                              ? "bg-purple-500/20 text-purple-400 border border-purple-500/30"
                              : "bg-emerald-500/20 text-emerald-400 border border-emerald-500/30"
                          }`}
                        >
                          {train.status}
                        </span>
                      </div>
                    </div>

                    {/* Overall Load Progress */}
                    <div className="mb-3">
                      <div className="flex justify-between text-xs mb-1">
                        <span className="text-slate-400">
                          Total Passenger Load: <strong className="text-white">{train.total_passengers}</strong> / {train.total_capacity}
                        </span>
                        <span className={`font-bold ${train.overall_load_pct >= 80 ? "text-rose-400" : train.overall_load_pct >= 60 ? "text-amber-400" : "text-emerald-400"}`}>
                          {train.overall_load_pct}% Capacity
                        </span>
                      </div>
                      <div className="w-full h-2 rounded-full bg-slate-800 overflow-hidden">
                        <div
                          className={`h-full transition-all duration-700 ${
                            train.overall_load_pct >= 80
                              ? "bg-gradient-to-r from-amber-500 to-rose-500"
                              : train.overall_load_pct >= 60
                              ? "bg-gradient-to-r from-blue-500 to-amber-500"
                              : "bg-gradient-to-r from-cyan-500 to-emerald-500"
                          }`}
                          style={{ width: `${Math.min(100, train.overall_load_pct)}%` }}
                        />
                      </div>
                    </div>

                    {/* Carriage Graphic (4 Cars) */}
                    <div className="grid grid-cols-4 gap-2 pt-2 border-t border-slate-800/80">
                      {train.cars.map((car) => {
                        const styleClasses = getCarColor(car.crowd_level);
                        return (
                          <div
                            key={car.car_id}
                            className={`p-2 rounded-lg border flex flex-col justify-between ${styleClasses} transition-all`}
                          >
                            <div className="flex items-center justify-between text-[11px] font-semibold mb-1">
                              <span>Car {car.car_number}</span>
                              <span>{car.load_percentage}%</span>
                            </div>
                            <div className="text-xs font-bold text-white">
                              {car.passenger_count} <span className="text-[10px] text-slate-400 font-normal">/ {car.max_capacity}</span>
                            </div>
                            <div className="text-[9px] uppercase tracking-wider font-semibold opacity-90 mt-1 truncate">
                              {car.crowd_level.replace("_", " ")}
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Station Real-Time Flow Table */}
          <div className="bg-[#0d1424] border border-slate-800 rounded-xl p-5 shadow-lg">
            <h2 className="text-base font-bold text-white flex items-center gap-2 mb-3">
              <Activity className="w-4 h-4 text-emerald-400" />
              Live Station Passenger Flow & Platform Gauges
            </h2>
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead>
                  <tr className="border-b border-slate-800 text-slate-400 font-semibold uppercase text-[10px]">
                    <th className="py-2.5 px-3">Station</th>
                    <th className="py-2.5 px-3">Line</th>
                    <th className="py-2.5 px-3 text-right">Inflow (PPM)</th>
                    <th className="py-2.5 px-3 text-right">Outflow (PPM)</th>
                    <th className="py-2.5 px-3 text-right">Net Flux</th>
                    <th className="py-2.5 px-3 text-right">Platform Crowd</th>
                    <th className="py-2.5 px-3 text-center">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60">
                  {stationMetrics
                    .filter((s) => selectedLine === "ALL" || s.line_name === selectedLine)
                    .slice(0, 8)
                    .map((st) => (
                      <tr key={st.station_id} className="hover:bg-slate-800/30 transition-all">
                        <td className="py-2.5 px-3 font-semibold text-white">
                          {st.station_name}
                        </td>
                        <td className="py-2.5 px-3">
                          <span
                            className={`px-1.5 py-0.5 rounded text-[10px] font-bold ${
                              st.line_name.includes("Red")
                                ? "bg-rose-500/10 text-rose-400"
                                : "bg-blue-500/10 text-blue-400"
                            }`}
                          >
                            {st.station_code}
                          </span>
                        </td>
                        <td className="py-2.5 px-3 text-right text-emerald-400 font-bold">
                          +{st.tap_ins_last_minute}
                        </td>
                        <td className="py-2.5 px-3 text-right text-amber-400 font-bold">
                          -{st.tap_outs_last_minute}
                        </td>
                        <td
                          className={`py-2.5 px-3 text-right font-bold ${
                            st.net_flux >= 0 ? "text-cyan-400" : "text-slate-400"
                          }`}
                        >
                          {st.net_flux > 0 ? `+${st.net_flux}` : st.net_flux}
                        </td>
                        <td className="py-2.5 px-3 text-right font-medium text-slate-200">
                          {st.current_platform_passengers}
                        </td>
                        <td className="py-2.5 px-3 text-center">
                          <span
                            className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase ${
                              st.crowd_status === "CRITICAL"
                                ? "bg-rose-500/20 text-rose-400 border border-rose-500/30"
                                : st.crowd_status === "MODERATE"
                                ? "bg-amber-500/20 text-amber-400 border border-amber-500/30"
                                : "bg-emerald-500/20 text-emerald-400 border border-emerald-500/30"
                            }`}
                          >
                            {st.crowd_status}
                          </span>
                        </td>
                      </tr>
                    ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>

        {/* Right Col: High-Velocity Live Gate Tap Ticker (AFC) */}
        <div className="space-y-4">
          <div className="bg-[#0d1424] border border-slate-800 rounded-xl p-5 shadow-lg flex flex-col h-[780px]">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3 mb-3">
              <div>
                <h2 className="text-base font-bold text-white flex items-center gap-2">
                  <CreditCard className="w-4 h-4 text-cyan-400" />
                  Live Turnstile Tap Stream
                </h2>
                <p className="text-[11px] text-slate-400 mt-0.5">
                  Automated Fare Collection (AFC) smart card tap events
                </p>
              </div>

              {/* Tap Type Filter */}
              <div className="flex items-center gap-1 bg-slate-900 border border-slate-800 p-0.5 rounded-lg text-[10px]">
                <button
                  onClick={() => setEventTypeFilter("ALL")}
                  className={`px-2 py-0.5 rounded font-medium ${
                    eventTypeFilter === "ALL" ? "bg-cyan-600 text-white" : "text-slate-400"
                  }`}
                >
                  All
                </button>
                <button
                  onClick={() => setEventTypeFilter("TAP_IN")}
                  className={`px-2 py-0.5 rounded font-medium ${
                    eventTypeFilter === "TAP_IN" ? "bg-emerald-600 text-white" : "text-slate-400"
                  }`}
                >
                  In
                </button>
                <button
                  onClick={() => setEventTypeFilter("TAP_OUT")}
                  className={`px-2 py-0.5 rounded font-medium ${
                    eventTypeFilter === "TAP_OUT" ? "bg-amber-600 text-white" : "text-slate-400"
                  }`}
                >
                  Out
                </button>
              </div>
            </div>

            {/* Scrolling Events Feed */}
            <div className="flex-1 overflow-y-auto space-y-2 pr-1">
              {filteredTaps.slice(0, 30).map((event) => {
                const isTapIn = event.event_type === "TAP_IN";
                const eventDate = new Date(event.timestamp);
                const timeStr = eventDate.toLocaleTimeString();

                return (
                  <div
                    key={event.event_id}
                    className="p-3 rounded-lg bg-slate-900/80 border border-slate-800 hover:border-slate-700 flex items-center justify-between gap-3 transition-all animate-fadeIn"
                  >
                    <div className="flex items-center gap-3">
                      <div
                        className={`w-8 h-8 rounded-lg flex items-center justify-center ${
                          isTapIn
                            ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/30"
                            : "bg-amber-500/10 text-amber-400 border border-amber-500/30"
                        }`}
                      >
                        {isTapIn ? (
                          <ArrowUpRight className="w-4 h-4" />
                        ) : (
                          <ArrowDownRight className="w-4 h-4" />
                        )}
                      </div>
                      <div>
                        <div className="flex items-center gap-1.5">
                          <span
                            className={`text-xs font-bold ${
                              isTapIn ? "text-emerald-400" : "text-amber-400"
                            }`}
                          >
                            {event.event_type.replace("_", " ")}
                          </span>
                          <span className="text-[10px] text-slate-500 font-mono">
                            {event.gate_id}
                          </span>
                        </div>
                        <p className="text-xs text-slate-200 font-medium truncate max-w-[140px]">
                          {event.station_name}
                        </p>
                        <p className="text-[10px] text-slate-500 font-mono">
                          {event.card_token} • {event.fare_category.toLowerCase()}
                        </p>
                      </div>
                    </div>

                    <div className="text-right">
                      <span className="text-[10px] text-slate-400 font-mono block">
                        {timeStr}
                      </span>
                      <span
                        className={`inline-block mt-1 text-[9px] px-1.5 py-0.5 rounded font-bold ${
                          event.line_name.includes("Red")
                            ? "bg-rose-500/10 text-rose-400"
                            : "bg-blue-500/10 text-blue-400"
                        }`}
                      >
                        {event.station_code}
                      </span>
                    </div>
                  </div>
                );
              })}
            </div>

            {/* Bottom Stream Status */}
            <div className="pt-3 border-t border-slate-800 text-[11px] text-slate-400 flex items-center justify-between">
              <span className="flex items-center gap-1.5">
                <span className="w-2 h-2 rounded-full bg-emerald-400 animate-ping"></span>
                Broadcasting Live WebSocket Taps
              </span>
              <span className="font-mono text-slate-300">
                {filteredTaps.length} buffered
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* GTFS-RT External Connector Modal */}
      {isModalOpen && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-[#0f172a] border border-slate-800 rounded-2xl w-full max-w-xl p-6 shadow-2xl space-y-5 animate-scaleUp">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div className="flex items-center gap-2.5">
                <div className="w-8 h-8 rounded-lg bg-cyan-500/20 text-cyan-400 flex items-center justify-center">
                  <Wifi className="w-4 h-4" />
                </div>
                <div>
                  <h3 className="text-base font-bold text-white">
                    Connect External GTFS-RT Feed
                  </h3>
                  <p className="text-xs text-slate-400">
                    Ingest real-time transit data from external public transport agencies
                  </p>
                </div>
              </div>
              <button
                onClick={() => setIsModalOpen(false)}
                className="text-slate-400 hover:text-white text-lg font-bold"
              >
                ✕
              </button>
            </div>

            {/* Current Status Box */}
            <div className="p-3.5 rounded-xl bg-slate-900/90 border border-slate-800 text-xs space-y-1.5">
              <div className="flex items-center justify-between">
                <span className="text-slate-400 font-medium">Connector Status:</span>
                <span
                  className={`font-bold px-2 py-0.5 rounded text-[10px] uppercase ${
                    gtfsStatus?.is_active
                      ? "bg-emerald-500/20 text-emerald-400 border border-emerald-500/30"
                      : "bg-slate-800 text-slate-400 border border-slate-700"
                  }`}
                >
                  {gtfsStatus?.is_active ? "Connected" : "Simulated Engine"}
                </span>
              </div>
              <p className="text-slate-300">
                <strong>Provider:</strong> {gtfsStatus?.provider_name}
              </p>
              <p className="text-slate-400 text-[11px]">
                {gtfsStatus?.status_message}
              </p>
            </div>

            {/* Preset Transit Agency Feeds */}
            <div>
              <p className="text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">
                Quick-Connect Transit Presets
              </p>
              <div className="space-y-2">
                {PRESET_FEEDS.map((preset) => (
                  <div
                    key={preset.name}
                    className="p-3 rounded-lg bg-slate-900 border border-slate-800 hover:border-cyan-500/40 flex items-center justify-between gap-3 text-xs"
                  >
                    <div>
                      <p className="font-semibold text-white">{preset.name}</p>
                      <p className="text-[11px] text-slate-400 font-mono truncate max-w-sm">
                        {preset.url}
                      </p>
                    </div>
                    <button
                      onClick={() => handleApplyGtfsConfig(preset.url, preset.name)}
                      disabled={gtfsSaving}
                      className="px-3 py-1.5 rounded-lg bg-cyan-600/30 border border-cyan-500/40 text-cyan-300 hover:bg-cyan-600 hover:text-white font-medium text-xs transition-all whitespace-nowrap"
                    >
                      Connect
                    </button>
                  </div>
                ))}
              </div>
            </div>

            {/* Custom URL Input */}
            <div className="space-y-3 pt-2 border-t border-slate-800">
              <p className="text-xs font-semibold text-slate-300 uppercase tracking-wider">
                Or Custom GTFS-RT Endpoint
              </p>
              <div>
                <label className="text-[11px] text-slate-400 block mb-1">
                  Feed Endpoint URL (JSON or GTFS-RT VehiclePositions)
                </label>
                <input
                  type="text"
                  placeholder="https://transit-agency.gov/api/gtfs-rt/vehicle-positions"
                  value={gtfsUrl}
                  onChange={(e) => setGtfsUrl(e.target.value)}
                  className="w-full bg-slate-900 border border-slate-800 rounded-lg px-3 py-2 text-xs text-white placeholder-slate-600 focus:outline-none focus:border-cyan-500 font-mono"
                />
              </div>

              <div>
                <label className="text-[11px] text-slate-400 block mb-1">
                  API Key / Bearer Token (Optional)
                </label>
                <input
                  type="password"
                  placeholder="Optional authorization token..."
                  value={gtfsApiKey}
                  onChange={(e) => setGtfsApiKey(e.target.value)}
                  className="w-full bg-slate-900 border border-slate-800 rounded-lg px-3 py-2 text-xs text-white placeholder-slate-600 focus:outline-none focus:border-cyan-500 font-mono"
                />
              </div>
            </div>

            {/* Feedback Message */}
            {configFeedback && (
              <p className="text-xs text-cyan-400 bg-cyan-500/10 border border-cyan-500/20 p-2 rounded-lg">
                {configFeedback}
              </p>
            )}

            {/* Actions */}
            <div className="flex items-center justify-between pt-3 border-t border-slate-800">
              <button
                type="button"
                onClick={handleResetToSimulation}
                disabled={gtfsSaving}
                className="text-xs text-slate-400 hover:text-slate-200"
              >
                Reset to Simulated AFC/APC
              </button>

              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={() => setIsModalOpen(false)}
                  className="px-4 py-2 rounded-lg bg-slate-800 text-slate-300 hover:bg-slate-700 text-xs font-semibold"
                >
                  Cancel
                </button>
                <button
                  type="button"
                  onClick={() => handleApplyGtfsConfig()}
                  disabled={gtfsSaving || !gtfsUrl}
                  className="px-4 py-2 rounded-lg bg-cyan-600 hover:bg-cyan-500 text-white text-xs font-bold transition-all disabled:opacity-50"
                >
                  {gtfsSaving ? "Connecting..." : "Save & Sync Feed"}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
