"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  Activity,
  CalendarClock,
  BrainCircuit,
  Bell,
  BarChart3,
  Train,
  Database,
  ShieldCheck,
} from "lucide-react";

const NAV_ITEMS = [
  { label: "Overview", href: "/dashboard", icon: LayoutDashboard },
  { label: "Live Monitoring", href: "/live-monitoring", icon: Activity },
  { label: "AI Forecasts", href: "/predictions", icon: BrainCircuit },
  { label: "Schedule Dispatch", href: "/schedules", icon: CalendarClock },
  { label: "Alerts Center", href: "/alerts", icon: Bell },
  { label: "Analytics", href: "/analytics", icon: BarChart3 },
  { label: "Datasets & ML", href: "/datasets", icon: Database },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="w-64 bg-[#0d1424] border-r border-slate-800 flex flex-col h-screen sticky top-0 z-30">
      {/* Brand Header */}
      <div className="p-6 border-b border-slate-800 flex items-center gap-3">
        <div className="w-10 h-10 rounded-xl bg-blue-600/20 border border-blue-500/30 flex items-center justify-center text-blue-400 font-bold shadow-lg shadow-blue-500/10">
          <Train className="w-6 h-6 text-blue-400" />
        </div>
        <div>
          <h1 className="font-extrabold text-lg tracking-wider text-white flex items-center gap-1.5">
            METRO<span className="text-blue-500">FLOW</span>
          </h1>
          <p className="text-[10px] uppercase tracking-widest text-slate-400 font-medium">
            AI Transit Intelligence
          </p>
        </div>
      </div>

      {/* Navigation Links */}
      <nav className="flex-1 p-4 space-y-1.5 overflow-y-auto">
        <div className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider px-3 mb-2">
          Operations Control
        </div>
        {NAV_ITEMS.map((item) => {
          const Icon = item.icon;
          const isActive = pathname === item.href;
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`flex items-center gap-3 px-3.5 py-2.5 rounded-lg text-sm font-medium transition-all ${
                isActive
                  ? "bg-blue-600/20 text-blue-400 border border-blue-500/30 font-semibold"
                  : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/50"
              }`}
            >
              <Icon className={`w-4 h-4 ${isActive ? "text-blue-400" : "text-slate-400"}`} />
              {item.label}
            </Link>
          );
        })}
      </nav>

      {/* Footer System Status */}
      <div className="p-4 border-t border-slate-800 bg-[#090d18]">
        <div className="flex items-center gap-2.5 text-xs text-slate-300 mb-1">
          <ShieldCheck className="w-4 h-4 text-emerald-400" />
          <span className="font-medium">System Health: Nominal</span>
        </div>
        <div className="text-[11px] text-slate-500">
          Backend ML Model: Active v2.0 (Real Data)
        </div>
      </div>
    </aside>
  );
}
