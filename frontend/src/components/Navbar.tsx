import React from 'react';
import { Activity, Radio, Train, Bell, BarChart3, Users, Shield, Cpu, Clock, LogOut } from 'lucide-react';
import { User } from '../types';

interface NavbarProps {
  currentUser: User | null;
  activeTab: string;
  setActiveTab: (tab: string) => void;
  activeHorizon: number;
  setActiveHorizon: (horizon: number) => void;
  wsConnected: boolean;
  onOpenLogin: () => void;
  onLogout: () => void;
  unreadAlertCount: number;
}

export const Navbar: React.FC<NavbarProps> = ({
  currentUser,
  activeTab,
  setActiveTab,
  activeHorizon,
  setActiveHorizon,
  wsConnected,
  onOpenLogin,
  onLogout,
  unreadAlertCount
}) => {
  const horizons = [
    { label: 'Live Now', value: 0 },
    { label: '+15 Min', value: 15 },
    { label: '+30 Min', value: 30 },
    { label: '+1 Hour', value: 60 },
    { label: '+2 Hours', value: 120 }
  ];

  const navItems = [
    { id: 'monitor', label: 'Crowd Monitoring', icon: Activity },
    { id: 'predictions', label: 'AI Prediction', icon: Cpu },
    { id: 'scheduling', label: 'Scheduling & Headway', icon: Train },
    { id: 'alerts', label: 'Alerts & Broadcast', icon: Bell, badge: unreadAlertCount },
    { id: 'analytics', label: 'Analytics Dashboard', icon: BarChart3 },
    ...(currentUser?.role === 'admin' ? [{ id: 'staff', label: 'User Management', icon: Shield }] : [])
  ];

  return (
    <header className="sticky top-0 z-[1100] bg-slate-900/95 backdrop-blur-md border-b border-slate-800 text-slate-100 px-6 py-3 shadow-lg">
      <div className="flex flex-col md:flex-row items-center justify-between gap-4">
        {/* Brand & Live Beacon */}
        <div className="flex items-center space-x-4">
          <div className="flex items-center space-x-3 cursor-pointer" onClick={() => setActiveTab('monitor')}>
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-blue-600 via-indigo-600 to-cyan-400 flex items-center justify-center shadow-lg shadow-blue-500/20">
              <Train className="w-5 h-5 text-white" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <span className="text-lg font-black tracking-tight text-white">MetroFlow</span>
                <span className="text-[10px] uppercase font-bold tracking-wider px-1.5 py-0.5 rounded bg-blue-500/20 text-blue-400 border border-blue-500/30">
                  Transit AI
                </span>
              </div>
              <p className="text-[11px] text-slate-400 font-medium">NYC Subway Operations & Scheduling</p>
            </div>
          </div>

          <div className="hidden lg:flex items-center space-x-2 pl-3 border-l border-slate-800">
            <span className="relative flex h-2 w-2">
              <span className={`animate-ping absolute inline-flex h-full w-full rounded-full opacity-75 ${wsConnected ? 'bg-emerald-400' : 'bg-amber-400'}`}></span>
              <span className={`relative inline-flex rounded-full h-2 w-2 ${wsConnected ? 'bg-emerald-500' : 'bg-amber-500'}`}></span>
            </span>
            <span className="text-[11px] font-mono text-slate-400">
              {wsConnected ? 'LIVE FEED CONNECTED' : 'POLLING TELEMETRY'}
            </span>
          </div>
        </div>

        {/* Predictive Horizon Slider/Buttons - Central highlight for +15m, +30m, +1h */}
        <div className="flex items-center bg-slate-950 p-1 rounded-xl border border-slate-800 shadow-inner">
          <div className="flex items-center px-2 text-slate-400 text-xs font-semibold mr-1">
            <Clock className="w-3.5 h-3.5 mr-1 text-cyan-400" />
            <span className="hidden sm:inline">Horizon:</span>
          </div>
          {horizons.map(h => (
            <button
              key={h.value}
              onClick={() => setActiveHorizon(h.value)}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition cursor-pointer ${
                activeHorizon === h.value
                  ? 'bg-blue-600 text-white shadow-md shadow-blue-600/30 font-bold'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900'
              }`}
            >
              {h.label}
            </button>
          ))}
        </div>

        {/* User Role Badge & Actions */}
        <div className="flex items-center space-x-3">
          {currentUser ? (
            <div className="flex items-center space-x-3 bg-slate-950/80 pl-3 pr-2 py-1.5 rounded-xl border border-slate-800">
              <div className="text-right">
                <div className="text-xs font-bold text-white flex items-center justify-end space-x-1.5">
                  <span>{currentUser.name}</span>
                  <span className={`text-[10px] px-1.5 py-0.2 rounded font-bold uppercase ${
                    currentUser.role === 'admin' ? 'bg-purple-500/20 text-purple-300 border border-purple-500/30' : 'bg-blue-500/20 text-blue-300 border border-blue-500/30'
                  }`}>
                    {currentUser.role}
                  </span>
                </div>
                <div className="text-[10px] text-slate-400 font-mono">{currentUser.badge_id}</div>
              </div>

              <button
                onClick={onLogout}
                title="Log out"
                className="p-1.5 rounded-lg text-slate-400 hover:text-red-400 hover:bg-slate-900 transition cursor-pointer"
              >
                <LogOut className="w-4 h-4" />
              </button>
            </div>
          ) : (
            <button
              onClick={onOpenLogin}
              className="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-xl text-xs font-bold transition shadow-md shadow-blue-600/20 cursor-pointer"
            >
              Sign In (Admin / Operator)
            </button>
          )}
        </div>
      </div>

      {/* Navigation Sub-Bar */}
      <nav className="flex items-center space-x-1 sm:space-x-2 mt-3 pt-2 border-t border-slate-800/80 overflow-x-auto">
        {navItems.map(item => {
          const Icon = item.icon;
          const isActive = activeTab === item.id;
          return (
            <button
              key={item.id}
              onClick={() => setActiveTab(item.id)}
              className={`flex items-center space-x-2 px-3.5 py-2 rounded-xl text-xs font-semibold whitespace-nowrap transition cursor-pointer ${
                isActive
                  ? 'bg-slate-800 text-white border border-slate-700 shadow-sm'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
              }`}
            >
              <Icon className={`w-4 h-4 ${isActive ? 'text-blue-400' : 'text-slate-400'}`} />
              <span>{item.label}</span>
              {typeof item.badge === 'number' && item.badge > 0 && (
                <span className="px-1.5 py-0.2 text-[10px] font-bold rounded-full bg-red-500 text-white animate-pulse">
                  {item.badge}
                </span>
              )}
            </button>
          );
        })}
      </nav>
    </header>
  );
};
