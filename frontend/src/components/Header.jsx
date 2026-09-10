import React from 'react';
import { 
  Train, 
  Activity, 
  Cpu, 
  Layers, 
  CalendarClock, 
  BarChart3, 
  Radio, 
  ShieldCheck,
  Zap
} from 'lucide-react';

export default function Header({ activeTab, setActiveTab, backendStatus, lastUpdated }) {
  const isOnline = backendStatus?.status === "Online";

  const navItems = [
    { id: 'prediction', label: 'Live Prediction Calculator', icon: Zap },
    { id: 'advisory', label: 'Fleet Schedule Advisory', icon: CalendarClock },
    { id: 'analytics', label: 'Network Analytics & Model', icon: BarChart3 },
  ];

  return (
    <header className="sticky top-0 z-40 w-full border-b border-slate-800/80 bg-[#090d16]/90 backdrop-blur-xl">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-20">
          
          {/* Logo & Platform Name */}
          <div className="flex items-center space-x-4">
            <div className="relative flex items-center justify-center w-12 h-12 rounded-2xl bg-gradient-to-tr from-cyan-600 via-blue-600 to-indigo-600 shadow-lg shadow-cyan-500/20 border border-cyan-400/30">
              <Train className="w-6 h-6 text-white" />
              <div className="absolute -bottom-1 -right-1 w-4 h-4 rounded-full bg-emerald-500 border-2 border-[#090d16] flex items-center justify-center">
                <span className="w-1.5 h-1.5 rounded-full bg-white animate-ping"></span>
              </div>
            </div>
            
            <div>
              <div className="flex items-center space-x-2.5">
                <h1 className="text-2xl font-extrabold tracking-tight bg-gradient-to-r from-white via-slate-100 to-slate-400 bg-clip-text text-transparent font-display">
                  Metro<span className="text-cyan-400">Flow</span>
                </h1>
                <span className="px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider rounded-md bg-cyan-500/10 text-cyan-300 border border-cyan-500/20 font-mono">
                  AI Transit v1.0
                </span>
              </div>
              <p className="text-xs text-slate-400 flex items-center gap-1.5 mt-0.5">
                <span>Predictive Crowd Monitoring & Intelligent Train Scheduling</span>
              </p>
            </div>
          </div>

          {/* Center Navigation Tabs */}
          <nav className="hidden md:flex items-center p-1.5 rounded-xl bg-slate-900/90 border border-slate-800 shadow-inner">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = activeTab === item.id;
              return (
                <button
                  key={item.id}
                  onClick={() => setActiveTab(item.id)}
                  className={`flex items-center space-x-2 px-4 py-2 rounded-lg text-xs font-semibold transition-all duration-200 ${
                    isActive
                      ? 'bg-gradient-to-r from-cyan-500 to-blue-600 text-white shadow-md shadow-cyan-500/25 border border-cyan-400/30'
                      : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
                  }`}
                >
                  <Icon className={`w-4 h-4 ${isActive ? 'text-white' : 'text-slate-400'}`} />
                  <span>{item.label}</span>
                </button>
              );
            })}
          </nav>

          {/* Right Status Badge */}
          <div className="flex items-center space-x-3">
            <div className="hidden lg:flex flex-col items-end text-right">
              <div className="flex items-center space-x-1.5">
                <div className={`w-2 h-2 rounded-full ${isOnline ? 'bg-emerald-400 radar-pulse' : 'bg-amber-400'}`}></div>
                <span className="text-xs font-medium text-slate-300">
                  {isOnline ? 'FastAPI & XGBoost Online' : 'Local Standby Mode'}
                </span>
              </div>
              <span className="text-[11px] font-mono text-slate-500">
                Port :8000 • JSON IO
              </span>
            </div>

            <div className="flex items-center px-3 py-1.5 rounded-xl bg-slate-800/80 border border-slate-700/60 text-slate-300 text-xs font-mono">
              <Cpu className="w-3.5 h-3.5 mr-1.5 text-cyan-400" />
              <span>XGBoost 95% R²</span>
            </div>
          </div>

        </div>

        {/* Mobile Navigation Bar */}
        <div className="flex md:hidden items-center justify-around py-2.5 border-t border-slate-800/60">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => setActiveTab(item.id)}
                className={`flex flex-col items-center py-1 px-2 rounded-lg text-[11px] font-medium ${
                  isActive ? 'text-cyan-400' : 'text-slate-400'
                }`}
              >
                <Icon className="w-4 h-4 mb-0.5" />
                <span>{item.label.split(' ')[0]}</span>
              </button>
            );
          })}
        </div>

      </div>
    </header>
  );
}
