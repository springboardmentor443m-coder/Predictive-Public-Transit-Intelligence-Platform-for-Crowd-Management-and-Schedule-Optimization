import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/router";
import {
  Activity,
  Bell,
  BrainCircuit,
  CalendarClock,
  LayoutDashboard,
  Lock,
  LogOut,
  Menu,
  Moon,
  Search,
  Settings,
  Sun,
  TrainFront,
  Volume2,
  VolumeX,
  X,
} from "lucide-react";
import { useAuth } from "../lib/auth";
import { useTheme } from "./ThemeContext";
import { useToast } from "./ToastContext";
import CommandPalette from "./CommandPalette";
import api from "../lib/api";

const NAV = [
  { href: "/dashboard", label: "Overview", icon: LayoutDashboard, roles: ["admin", "operator", "viewer"], section: "Operate", shortcut: "1" },
  { href: "/dashboard/crowd", label: "Crowd Monitoring", icon: Activity, roles: ["admin", "operator", "viewer"], section: "Operate", shortcut: "2" },
  { href: "/dashboard/scheduling", label: "Scheduling", icon: CalendarClock, roles: ["admin", "operator"], section: "Operate", lockFor: ["viewer"], shortcut: "3" },
  { href: "/dashboard/trains", label: "Train Monitoring", icon: TrainFront, roles: ["admin", "operator", "viewer"], section: "Operate", shortcut: "4" },
  { href: "/dashboard/predictions", label: "AI Predictions", icon: BrainCircuit, roles: ["admin", "operator", "viewer"], section: "Intelligence", shortcut: "5" },
  { href: "/dashboard/analytics", label: "Analytics", icon: TrainFront, roles: ["admin", "operator", "viewer"], section: "Intelligence", shortcut: "6" },
  { href: "/dashboard/alerts", label: "Alerts", icon: Bell, roles: ["admin", "operator", "viewer"], section: "Intelligence", badge: true, shortcut: "7" },
];

export default function DashboardLayout({ title, subtitle, children }) {
  const { user, logout } = useAuth();
  const { theme, toggleTheme } = useTheme();
  const { soundEnabled, setSoundEnabled } = useToast();
  const router = useRouter();

  const [open, setOpen] = useState(false);
  const [clock, setClock] = useState("");
  const [openAlerts, setOpenAlerts] = useState(0);
  const [cmdOpen, setCmdOpen] = useState(false);

  useEffect(() => {
    const tick = () => setClock(new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" }));
    tick();
    const iv = setInterval(tick, 1000);
    return () => clearInterval(iv);
  }, []);

  useEffect(() => {
    let alive = true;
    api.get("/alerts?acknowledged=false&limit=1").then((r) => {
      if (!alive) return;
      return api.get("/analytics/overview").then((ov) => {
        if (alive) setOpenAlerts(ov.data?.active_alerts ?? r.data?.length ?? 0);
      });
    }).catch(() => {});
    const iv = setInterval(() => {
      api.get("/analytics/overview").then((ov) => { if (alive) setOpenAlerts(ov.data?.active_alerts ?? 0); }).catch(() => {});
    }, 25000);
    return () => { alive = false; clearInterval(iv); };
  }, []);

  const role = user?.role || "viewer";
  const nav = NAV.filter((item) => item.roles.includes(role));
  const sections = ["Operate", "Intelligence"];

  return (
    <div className="min-h-screen lg:flex lg:h-screen lg:overflow-hidden text-slate-100 font-sans">
      {/* Sidebar — Deep Space Midnight Glass Panel */}
      <aside
        className={`fixed inset-y-0 left-0 z-40 flex w-[268px] flex-col bg-slate-950/95 border-r border-slate-800/80 backdrop-blur-2xl transition-transform duration-200 lg:static lg:h-screen lg:translate-x-0 ${
          open ? "translate-x-0" : "-translate-x-full"
        }`}
      >
        <div className="flex h-16 items-center gap-3 border-b border-slate-800/80 px-5">
          <span className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-brand-400 via-brand-600 to-indigo-700 shadow-lg shadow-brand-500/25">
            <TrainFront className="h-5 w-5 text-white" />
          </span>
          <div>
            <p className="text-base font-extrabold leading-tight tracking-tight text-white">MetroFlow</p>
            <p className="text-[10px] font-semibold tracking-wider text-brand-400 uppercase">AI Transit Platform</p>
          </div>
          <button className="ml-auto text-slate-400 hover:text-white lg:hidden" onClick={() => setOpen(false)}>
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Live Network Status Indicator Widget */}
        <div className="mx-3 mt-3 rounded-2xl bg-gradient-to-r from-brand-950/60 to-emerald-950/40 p-3.5 border border-slate-800/90 shadow-inner">
          <p className="text-[10px] font-extrabold uppercase tracking-[0.14em] text-slate-400">Network Telemetry</p>
          <p className="mt-1 flex items-center gap-2 text-xs font-bold text-white">
            <span className="relative flex h-2 w-2">
              <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-400 opacity-75" />
              <span className="relative inline-flex h-2 w-2 rounded-full bg-emerald-400" />
            </span>
            Live Operations Active
          </p>
          <p className="mt-0.5 text-[11px] text-slate-400 font-mono">{clock} · 10 Stations</p>
        </div>

        {/* Navigation Items */}
        <nav className="scroll-thin flex-1 space-y-4 overflow-y-auto p-3">
          {sections.map((sec) => (
            <div key={sec}>
              <p className="px-3 pb-1.5 text-[10px] font-extrabold uppercase tracking-[0.16em] text-slate-500">{sec}</p>
              <div className="space-y-1">
                {nav.filter((n) => n.section === sec).map(({ href, label, icon: Icon, badge, lockFor, shortcut }) => {
                  const active = router.pathname === href;
                  const locked = lockFor?.includes(role);
                  return (
                    <Link
                      key={href}
                      href={href}
                      onClick={() => setOpen(false)}
                      className={`group flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition-all duration-200 ${
                        active
                          ? "bg-gradient-to-r from-brand-600 to-brand-500 text-white shadow-lg shadow-brand-600/30 border border-brand-400/30"
                          : "text-slate-400 hover:bg-slate-900 hover:text-white"
                      }`}
                    >
                      <Icon className={`h-4 w-4 shrink-0 transition-transform ${active ? "text-white scale-110" : "opacity-80 group-hover:opacity-100"}`} />
                      <span className="truncate text-xs font-semibold">{label}</span>
                      
                      {badge && openAlerts > 0 && (
                        <span className="ml-auto inline-flex min-w-[20px] items-center justify-center rounded-full bg-rose-500 px-1.5 py-0.5 text-[10px] font-extrabold text-white animate-pulse">
                          {openAlerts > 99 ? "99+" : openAlerts}
                        </span>
                      )}
                      
                      {locked && <Lock className="ml-auto h-3.5 w-3.5 opacity-40" />}
                      {!locked && !badge && (
                        <span className="ml-auto text-[10px] font-mono text-slate-600 group-hover:text-slate-400 transition hidden lg:inline">
                          {shortcut}
                        </span>
                      )}
                    </Link>
                  );
                })}
              </div>
            </div>
          ))}
        </nav>

        {/* Footer User Info & Settings */}
        <div className="border-t border-slate-800/80 p-3 space-y-1">
          <Link
            href="/dashboard/settings"
            onClick={() => setOpen(false)}
            className={`flex items-center gap-3 rounded-xl px-3 py-2 text-xs font-semibold transition ${
              router.pathname === "/dashboard/settings"
                ? "bg-brand-600/20 text-white border border-brand-500/30"
                : "text-slate-400 hover:bg-slate-900 hover:text-white"
            }`}
          >
            <Settings className="h-4 w-4" />
            <span>Settings & Profile</span>
            <span className="ml-auto rounded-md bg-slate-800 px-1.5 py-0.5 text-[10px] font-extrabold uppercase tracking-wide text-brand-300">
              {role}
            </span>
          </Link>
          
          <button
            onClick={logout}
            className="flex w-full items-center gap-3 rounded-xl px-3 py-2 text-xs font-semibold text-slate-400 transition hover:bg-rose-500/10 hover:text-rose-300"
          >
            <LogOut className="h-4 w-4 text-slate-500" />
            <span>Sign Out Console</span>
          </button>
        </div>
      </aside>

      {/* Mobile Backdrop */}
      {open && (
        <div className="fixed inset-0 z-30 bg-slate-950/80 backdrop-blur-sm lg:hidden" onClick={() => setOpen(false)} />
      )}

      {/* Main Container */}
      <div className="flex min-w-0 flex-1 flex-col lg:h-screen lg:overflow-y-auto">
        {/* Top Header Bar */}
        <header className="sticky top-0 z-20 flex h-16 items-center gap-3 border-b border-slate-800/80 bg-slate-950/80 px-4 backdrop-blur-xl sm:px-6">
          <button className="text-slate-400 hover:text-white lg:hidden" onClick={() => setOpen(true)}>
            <Menu className="h-6 w-6" />
          </button>

          {/* Breadcrumb & Title */}
          <div className="min-w-0">
            <div className="flex items-center gap-2 text-[10px] font-extrabold uppercase tracking-wider text-slate-400">
              <span>MetroFlow</span>
              <span className="text-slate-600">/</span>
              <span className="text-brand-400">{title}</span>
            </div>
            <h1 className="truncate text-base font-extrabold tracking-tight text-white">{title}</h1>
          </div>

          {subtitle && <p className="hidden max-w-sm truncate text-xs text-slate-400 xl:block">· {subtitle}</p>}

          {/* Right Header Quick Tools */}
          <div className="ml-auto flex items-center gap-2.5">
            {/* Quick Search Button (Ctrl+K) */}
            <button
              onClick={() => setCmdOpen(true)}
              className="flex items-center gap-2 rounded-xl border border-slate-800 bg-slate-900 px-3 py-1.5 text-xs text-slate-400 hover:border-slate-700 hover:text-white transition shadow-sm"
            >
              <Search className="h-3.5 w-3.5 text-brand-400" />
              <span className="hidden sm:inline">Search...</span>
              <kbd className="hidden sm:inline-block rounded bg-slate-800 px-1.5 py-0.5 text-[10px] font-mono text-slate-400">Ctrl+K</kbd>
            </button>

            {/* Sound Effects Toggle */}
            <button
              onClick={() => setSoundEnabled(!soundEnabled)}
              title={soundEnabled ? "Audio alert chimes enabled" : "Audio alert chimes muted"}
              className="flex h-9 w-9 items-center justify-center rounded-xl border border-slate-800 bg-slate-900 text-slate-400 hover:border-slate-700 hover:text-white transition"
            >
              {soundEnabled ? <Volume2 className="h-4 w-4 text-emerald-400" /> : <VolumeX className="h-4 w-4 text-slate-500" />}
            </button>

            {/* Theme Toggle (Dark/Light) */}
            <button
              onClick={toggleTheme}
              title={`Switch to ${theme === "light" ? "Dark" : "Light"} mode`}
              className="flex h-9 w-9 items-center justify-center rounded-xl border border-slate-800 bg-slate-900 text-slate-400 hover:border-slate-700 hover:text-white transition"
            >
              {theme === "light" ? <Moon className="h-4 w-4 text-indigo-400" /> : <Sun className="h-4 w-4 text-amber-400" />}
            </button>

            {/* Live Clock Badge */}
            <span className="hidden items-center gap-2 rounded-full bg-emerald-500/10 px-3 py-1 text-xs font-bold text-emerald-400 border border-emerald-500/20 md:inline-flex">
              <span className="relative flex h-2 w-2">
                <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-400 opacity-75" />
                <span className="relative inline-flex h-2 w-2 rounded-full bg-emerald-400" />
              </span>
              <span className="font-mono">{clock}</span>
            </span>

            {/* User Profile Capsule */}
            <div className="flex items-center gap-2.5 rounded-full bg-slate-900 py-1 pl-1 pr-3 border border-slate-800">
              <span className="flex h-8 w-8 items-center justify-center rounded-full bg-gradient-to-br from-brand-500 to-indigo-600 text-xs font-extrabold text-white shadow">
                {user?.full_name?.split(" ").map((w) => w[0]).slice(0, 2).join("") || "U"}
              </span>
              <div className="hidden text-left sm:block">
                <p className="text-xs font-bold leading-tight text-white">{user?.full_name}</p>
                <p className="text-[10px] capitalize leading-tight text-slate-400">{user?.role}</p>
              </div>
            </div>
          </div>
        </header>

        {/* Main Content Area */}
        <main className="flex-1 p-4 sm:p-6">{children}</main>

        {/* Footer */}
        <footer className="flex flex-wrap items-center justify-between border-t border-slate-800/80 px-6 py-3 text-xs text-slate-500 gap-2">
          <span>MetroFlow · AI Platform for Metro Crowd Management & Schedule Optimization</span>
          <span className="font-mono text-[11px]">Next.js 14 · XGBoost AI · Socket.IO Realtime</span>
        </footer>
      </div>

      {/* Global Command Palette */}
      <CommandPalette isOpen={cmdOpen} onClose={() => setCmdOpen(false)} />
    </div>
  );
}
