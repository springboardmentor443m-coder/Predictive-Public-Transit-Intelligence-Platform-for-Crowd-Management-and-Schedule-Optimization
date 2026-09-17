import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Activity, Shield, LogIn, LogOut, Clock, Sparkles } from 'lucide-react';

export const Navbar: React.FC = () => {
  const { user, isAuthenticated, logout } = useAuth();
  const navigate = useNavigate();
  const [timeStr, setTimeStr] = useState('');

  useEffect(() => {
    const updateTime = () => {
      const now = new Date();
      setTimeStr(
        now.toLocaleTimeString('en-US', {
          timeZone: 'Asia/Seoul',
          hour12: false,
          hour: '2-digit',
          minute: '2-digit',
          second: '2-digit',
        }) + ' KST'
      );
    };
    updateTime();
    const interval = setInterval(updateTime, 1000);
    return () => clearInterval(interval);
  }, []);

  return (
    <header className="h-16 bg-bg-surface/95 backdrop-blur-md border-b border-border-dark px-6 flex items-center justify-between sticky top-0 z-40 shadow-card">
      {/* Brand Logo with Holographic Neon Violet & Aurora Mint Gradient */}
      <div className="flex items-center gap-3">
        <Link to="/" className="flex items-center gap-3 group">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-[#7928CA] via-[#A855F7] to-[#00F5D4] p-[1.5px] shadow-glow group-hover:scale-105 transition-all duration-300">
            <div className="w-full h-full bg-bg-main rounded-[10px] flex items-center justify-center">
              <span className="font-mono font-black text-transparent bg-clip-text bg-gradient-to-r from-[#C084FC] to-[#00F5D4] text-xl">
                M
              </span>
            </div>
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-extrabold text-xl tracking-tight bg-gradient-to-r from-white via-slate-100 to-[#C084FC] bg-clip-text text-transparent">
                MetroFlow
              </span>
              <span className="text-[10px] uppercase font-mono px-2 py-0.5 rounded-full bg-metro-primary/15 text-[#C084FC] border border-metro-primary/40 font-bold shadow-[0_0_10px_rgba(168,85,247,0.25)]">
                AI v1.0
              </span>
            </div>
            <p className="text-[11px] text-slate-400 font-sans tracking-wide">
              Seoul Metro Crowd Intelligence
            </p>
          </div>
        </Link>
      </div>

      {/* Center Live Telemetry Pill */}
      <div className="hidden md:flex items-center gap-4 px-4 py-1.5 rounded-full bg-bg-card border border-border-dark text-xs font-mono shadow-inner">
        <div className="flex items-center gap-2 text-[#05FFA1]">
          <span className="h-2 w-2 rounded-full bg-[#05FFA1] shadow-[0_0_8px_rgba(5,255,161,0.8)] animate-pulse" />
          <span className="font-semibold">NETWORK ONLINE</span>
        </div>
        <span className="text-slate-600">|</span>
        <div className="flex items-center gap-1.5 text-slate-300">
          <Clock className="w-3.5 h-3.5 text-[#00F5D4]" />
          <span className="text-slate-200">{timeStr || 'LIVE'}</span>
        </div>
      </div>

      {/* Right User & Actions */}
      <div className="flex items-center gap-3">
        {isAuthenticated && user ? (
          <div className="flex items-center gap-3 bg-bg-card border border-border-dark px-3.5 py-1.5 rounded-xl shadow-sm">
            <div className="flex items-center gap-2">
              <Shield className="w-4 h-4 text-[#C084FC]" />
              <div className="text-left font-mono">
                <p className="text-xs font-semibold text-slate-200 leading-none">
                  {user.username}
                </p>
                <p className="text-[10px] text-metro-amber uppercase leading-none mt-1 font-bold">
                  {user.role}
                </p>
              </div>
            </div>
            <button
              onClick={logout}
              title="Logout"
              className="p-1.5 hover:bg-slate-800 rounded-lg text-slate-400 hover:text-red-400 transition-colors"
            >
              <LogOut className="w-4 h-4" />
            </button>
          </div>
        ) : (
          <button
            onClick={() => navigate('/login')}
            className="flex items-center gap-2 px-4 py-2 rounded-xl bg-gradient-to-r from-metro-primary/20 to-metro-cyan/20 hover:from-metro-primary/30 hover:to-metro-cyan/30 text-white border border-metro-primary/40 font-mono text-xs font-bold transition-all shadow-glow hover:shadow-[0_0_20px_rgba(168,85,247,0.5)]"
          >
            <LogIn className="w-4 h-4 text-[#00F5D4]" />
            <span>Operator Sign In</span>
          </button>
        )}
      </div>
    </header>
  );
};
