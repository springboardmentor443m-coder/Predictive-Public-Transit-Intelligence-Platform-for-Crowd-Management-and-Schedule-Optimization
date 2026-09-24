import { useState, useEffect } from "react";
import { useRouter } from "next/router";
import { Search, Activity, CalendarClock, BrainCircuit, TrainFront, Bell, Settings, ArrowRight, X, type LucideIcon } from "lucide-react";
import api from "../lib/api";
import type { Station } from "../lib/types";

interface NavCommand {
  href: string;
  label: string;
  icon: LucideIcon;
  section: string;
}

const NAV_ITEMS: NavCommand[] = [
  { href: "/dashboard", label: "Operations Overview", icon: Activity, section: "Navigation" },
  { href: "/dashboard/crowd", label: "Crowd Monitoring Map", icon: Activity, section: "Navigation" },
  { href: "/dashboard/trains", label: "Real-Time Train Monitoring", icon: TrainFront, section: "Navigation" },
  { href: "/dashboard/scheduling", label: "Train Schedules & Headway", icon: CalendarClock, section: "Navigation" },
  { href: "/dashboard/predictions", label: "AI Crowd & Delay Predictions", icon: BrainCircuit, section: "Navigation" },
  { href: "/dashboard/analytics", label: "Analytics & Performance Reports", icon: TrainFront, section: "Navigation" },
  { href: "/dashboard/alerts", label: "Alert Feed & Broadcast Center", icon: Bell, section: "Navigation" },
  { href: "/dashboard/settings", label: "Settings & User Management", icon: Settings, section: "Navigation" },
];

interface CommandPaletteProps {
  isOpen: boolean;
  onClose: () => void;
  onOpen: () => void;
}

export default function CommandPalette({ isOpen, onClose, onOpen }: CommandPaletteProps) {
  const router = useRouter();
  const [query, setQuery] = useState("");
  const [stations, setStations] = useState<Station[]>([]);

  useEffect(() => {
    if (isOpen) {
      api.get<Station[]>("/stations").then((r) => setStations(r.data)).catch(() => {});
    }
  }, [isOpen]);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        if (isOpen) onClose(); else onOpen();
      }
      if (e.key === "Escape" && isOpen) {
        onClose();
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isOpen, onClose, onOpen]);

  if (!isOpen) return null;

  const q = query.trim().toLowerCase();

  const filteredNav = NAV_ITEMS.filter((i) => i.label.toLowerCase().includes(q));
  const filteredStations = stations.filter(
    (s) => s.name.toLowerCase().includes(q) || s.id.toLowerCase().includes(q) || s.line.toLowerCase().includes(q)
  );

  const navigateTo = (href: string) => {
    router.push(href);
    onClose();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-start justify-center pt-20 bg-slate-950/80 backdrop-blur-md p-4" onClick={onClose}>
      <div
        className="w-full max-w-xl rounded-2xl border border-slate-700/80 bg-slate-900 shadow-2xl overflow-hidden animate-in fade-in zoom-in-95 duration-200"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center gap-3 border-b border-slate-800 px-4 py-3.5">
          <Search className="h-5 w-5 text-brand-400 shrink-0" />
          <input
            autoFocus
            type="text"
            placeholder="Search stations, lines, pages or commands... (Esc to close)"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            className="w-full bg-transparent text-sm text-slate-100 placeholder-slate-500 focus:outline-none"
          />
          <button onClick={onClose} className="rounded-lg p-1 text-slate-400 hover:bg-slate-800 hover:text-slate-200">
            <X className="h-4 w-4" />
          </button>
        </div>

        <div className="max-h-[380px] overflow-y-auto p-2 scroll-thin divide-y divide-slate-800/60">
          {filteredNav.length > 0 && (
            <div className="py-1">
              <p className="px-3 py-1.5 text-[10px] font-extrabold uppercase tracking-wider text-slate-500">Pages</p>
              {filteredNav.map((item) => {
                const Icon = item.icon;
                return (
                  <button
                    key={item.href}
                    onClick={() => navigateTo(item.href)}
                    className="w-full flex items-center gap-3 rounded-xl px-3 py-2 text-sm text-slate-300 hover:bg-brand-600/20 hover:text-white transition group"
                  >
                    <Icon className="h-4 w-4 text-slate-400 group-hover:text-brand-400" />
                    <span>{item.label}</span>
                    <ArrowRight className="ml-auto h-3.5 w-3.5 opacity-0 group-hover:opacity-100 transition text-brand-400" />
                  </button>
                );
              })}
            </div>
          )}

          {filteredStations.length > 0 && (
            <div className="py-1">
              <p className="px-3 py-1.5 text-[10px] font-extrabold uppercase tracking-wider text-slate-500">Stations ({filteredStations.length})</p>
              {filteredStations.map((s) => (
                <button
                  key={s.id}
                  onClick={() => navigateTo(`/dashboard/crowd`)}
                  className="w-full flex items-center justify-between rounded-xl px-3 py-2 text-sm text-slate-300 hover:bg-brand-600/20 hover:text-white transition group"
                >
                  <div className="flex items-center gap-2.5">
                    <span className="h-2 w-2 rounded-full bg-brand-400" />
                    <span className="font-semibold text-white">{s.name}</span>
                    <span className="text-xs text-slate-400">({s.id})</span>
                  </div>
                  <span className="text-xs uppercase font-extrabold px-2 py-0.5 rounded bg-slate-800 text-slate-300">{s.line} line</span>
                </button>
              ))}
            </div>
          )}

          {filteredNav.length === 0 && filteredStations.length === 0 && (
            <div className="py-8 text-center text-sm text-slate-500">
              No results found for &quot;{query}&quot;
            </div>
          )}
        </div>

        <div className="border-t border-slate-800 bg-slate-950/60 px-4 py-2 flex items-center justify-between text-[11px] text-slate-500">
          <span>Tip: Press <kbd className="rounded bg-slate-800 px-1.5 py-0.5 text-[10px]">Ctrl+K</kbd> anytime to open search</span>
          <span>MetroFlow Control Console</span>
        </div>
      </div>
    </div>
  );
}