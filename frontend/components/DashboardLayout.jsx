import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/router";
import {
  Activity,
  Bell,
  BrainCircuit,
  CalendarClock,
  LayoutDashboard,
  LogOut,
  Menu,
  Settings,
  TrainFront,
  X,
} from "lucide-react";
import { useAuth } from "../lib/auth";

const NAV = [
  { href: "/dashboard", label: "Overview", icon: LayoutDashboard },
  { href: "/dashboard/crowd", label: "Crowd Monitoring", icon: Activity },
  { href: "/dashboard/scheduling", label: "Scheduling", icon: CalendarClock },
  { href: "/dashboard/predictions", label: "AI Predictions", icon: BrainCircuit },
  { href: "/dashboard/alerts", label: "Alerts", icon: Bell },
  { href: "/dashboard/analytics", label: "Analytics", icon: TrainFront },
];

export default function DashboardLayout({ title, subtitle, children }) {
  const { user, logout } = useAuth();
  const router = useRouter();
  const [open, setOpen] = useState(false);

  const nav = NAV.filter(
    (item) =>
      !item.adminOnly ||
      (user && (user.role === "admin" || user.role === "operator"))
  );

  return (
    <div className="min-h-screen lg:flex lg:h-screen lg:overflow-hidden">
      {/* Sidebar */}
      <aside
        className={`fixed inset-y-0 left-0 z-40 w-64 transform bg-slate-900 text-slate-300 transition-transform duration-200 lg:static lg:relative lg:h-screen lg:translate-x-0 ${
          open ? "translate-x-0" : "-translate-x-full"
        }`}
      >
        <div className="flex h-16 items-center gap-2.5 border-b border-slate-800 px-5">
          <span className="flex h-9 w-9 items-center justify-center rounded-lg bg-brand-600">
            <TrainFront className="h-5 w-5 text-white" />
          </span>
          <div>
            <p className="text-base font-bold leading-tight text-white">MetroFlow</p>
            <p className="text-[11px] leading-tight text-slate-400">Transit Intelligence</p>
          </div>
          <button className="ml-auto text-slate-400 hover:text-white lg:hidden" onClick={() => setOpen(false)}>
            <X className="h-5 w-5" />
          </button>
        </div>

        <nav className="space-y-1 p-3">
          {nav.map(({ href, label, icon: Icon }) => {
            const active = router.pathname === href;
            return (
              <Link
                key={href}
                href={href}
                onClick={() => setOpen(false)}
                className={`flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition ${
                  active
                    ? "bg-brand-600 text-white shadow"
                    : "text-slate-400 hover:bg-slate-800 hover:text-white"
                }`}
              >
                <Icon className="h-[18px] w-[18px]" />
                {label}
              </Link>
            );
          })}
        </nav>

        <div className="absolute bottom-0 w-full border-t border-slate-800 p-3">
          <Link
            href="/dashboard/settings"
            onClick={() => setOpen(false)}
            className={`mb-1 flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition ${
              router.pathname === "/dashboard/settings"
                ? "bg-brand-600 text-white"
                : "text-slate-400 hover:bg-slate-800 hover:text-white"
            }`}
          >
            <Settings className="h-[18px] w-[18px]" />
            Settings & Profile
          </Link>
          <button
            onClick={logout}
            className="flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium text-slate-400 transition hover:bg-slate-800 hover:text-white"
          >
            <LogOut className="h-[18px] w-[18px]" />
            Sign out
          </button>
        </div>
      </aside>

      {open && (
        <div className="fixed inset-0 z-30 bg-slate-900/50 lg:hidden" onClick={() => setOpen(false)} />
      )}

      {/* Main */}
      <div className="flex min-w-0 flex-1 flex-col lg:h-screen lg:overflow-y-auto">
        <header className="sticky top-0 z-20 flex h-16 items-center gap-4 border-b border-slate-200 bg-white/90 px-4 backdrop-blur sm:px-6">
          <button className="text-slate-500 hover:text-slate-800 lg:hidden" onClick={() => setOpen(true)}>
            <Menu className="h-6 w-6" />
          </button>
          <div className="min-w-0">
            <h1 className="truncate text-lg font-bold text-slate-900">{title}</h1>
            {subtitle && <p className="hidden truncate text-xs text-slate-500 sm:block">{subtitle}</p>}
          </div>
          <div className="ml-auto flex items-center gap-4">
            <span className="hidden items-center gap-2 rounded-full bg-emerald-50 px-3 py-1 text-xs font-semibold text-emerald-700 ring-1 ring-emerald-200 md:inline-flex">
              <span className="relative flex h-2 w-2">
                <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-400 opacity-75" />
                <span className="relative inline-flex h-2 w-2 rounded-full bg-emerald-500" />
              </span>
              Live
            </span>
            <div className="flex items-center gap-3">
              <div className="hidden text-right sm:block">
                <p className="text-sm font-semibold leading-tight text-slate-800">{user?.full_name}</p>
                <p className="text-xs capitalize leading-tight text-slate-500">{user?.role}</p>
              </div>
              <span className="flex h-9 w-9 items-center justify-center rounded-full bg-brand-100 text-sm font-bold text-brand-700">
                {user?.full_name?.split(" ").map((w) => w[0]).slice(0, 2).join("") || "U"}
              </span>
            </div>
          </div>
        </header>

        <main className="flex-1 p-4 sm:p-6">{children}</main>

        <footer className="border-t border-slate-200 px-6 py-3 text-center text-xs text-slate-400">
          MetroFlow · AI Platform for Metro Crowd Management & Scheduling
        </footer>
      </div>
    </div>
  );
}
