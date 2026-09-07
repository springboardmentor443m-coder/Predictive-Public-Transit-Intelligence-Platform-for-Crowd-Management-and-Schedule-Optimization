"use client";

import { useEffect, useState } from "react";
import { Bell, Radio, User, RefreshCw, ShieldAlert } from "lucide-react";
import Link from "next/link";
import { socketClient } from "@/lib/socket";

export function Navbar() {
  const [timeStr, setTimeStr] = useState<string>("");
  const [alertsCount, setAlertsCount] = useState<number>(2);
  const [isConnected, setIsConnected] = useState<boolean>(true);

  useEffect(() => {
    const updateTime = () => {
      const now = new Date();
      setTimeStr(now.toLocaleTimeString("en-US", { timeZone: "UTC", hour12: false }) + " UTC");
    };
    updateTime();
    const interval = setInterval(updateTime, 1000);

    const unsubscribe = socketClient.subscribe((msg) => {
      if (msg.event === "TELEMETRY_UPDATE") {
        setAlertsCount(msg.alerts_count || 0);
        setIsConnected(true);
      }
    });
    socketClient.connect();

    return () => {
      clearInterval(interval);
      unsubscribe();
    };
  }, []);

  return (
    <header className="h-16 bg-[#0d1424]/90 backdrop-blur border-b border-slate-800 px-6 flex items-center justify-between sticky top-0 z-20">
      {/* Telemetry Status Indicator */}
      <div className="flex items-center gap-4">
        <div className="flex items-center gap-2 px-3 py-1 rounded-full bg-slate-800/80 border border-slate-700 text-xs font-mono text-slate-300">
          <Radio className={`w-3.5 h-3.5 ${isConnected ? "text-emerald-400 animate-pulse" : "text-amber-400"}`} />
          <span>LIVE TELEMETRY</span>
          <span className="text-slate-500">|</span>
          <span className="text-blue-400 font-semibold">{timeStr}</span>
        </div>

        <div className="hidden md:flex items-center gap-2 text-xs text-slate-400">
          <span className="w-2 h-2 rounded-full bg-emerald-500"></span>
          <span>Red Line: Operational</span>
          <span className="w-2 h-2 rounded-full bg-blue-500 ml-2"></span>
          <span>Blue Line: Operational</span>
        </div>
      </div>

      {/* Operator controls & Notifications */}
      <div className="flex items-center gap-4">
        <Link
          href="/alerts"
          className="relative p-2 rounded-lg bg-slate-800/50 hover:bg-slate-800 text-slate-300 transition"
        >
          <Bell className="w-5 h-5 text-slate-300" />
          {alertsCount > 0 && (
            <span className="absolute -top-1 -right-1 w-5 h-5 bg-rose-500 text-white rounded-full text-[10px] font-bold flex items-center justify-center animate-bounce">
              {alertsCount}
            </span>
          )}
        </Link>

        {/* User profile */}
        <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-slate-800/50 border border-slate-700">
          <div className="w-7 h-7 rounded-full bg-blue-600 flex items-center justify-center text-white text-xs font-bold">
            OP
          </div>
          <div className="text-xs">
            <div className="font-semibold text-slate-200">Metro Operator</div>
            <div className="text-[10px] text-slate-400 uppercase">Control Room</div>
          </div>
        </div>
      </div>
    </header>
  );
}
