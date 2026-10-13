import React, { useState } from 'react';
import { MetroBackground } from './MetroBackground';
import { 
  ShieldCheck, 
  UserCheck, 
  Lock, 
  Mail, 
  Activity, 
  AlertCircle,
  Radio,
  Zap,
  ChevronRight
} from 'lucide-react';

export const LoginPage: React.FC = () => {
  const [role, setRole] = useState<'OPERATOR' | 'ADMIN'>('OPERATOR');
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      const response = await fetch('http://localhost:8000/api/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password, role }),
      });

      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || 'Authentication failed');

      localStorage.setItem('metroflow_token', data.access_token);
      localStorage.setItem('metroflow_user', JSON.stringify(data.user));
      window.location.reload();
    } catch (err: any) {
      setError(err.message || 'Transit Telemetry Server Unreachable');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="relative h-screen w-screen bg-[#030712] text-slate-100 flex items-center justify-center p-4 overflow-hidden">
      <MetroBackground />

      <div className="relative z-20 w-full max-w-[440px] bg-slate-900/60 backdrop-blur-2xl border border-slate-700/60 rounded-3xl p-8 shadow-[0_0_50px_rgba(6,182,212,0.12)]">
        
        <div className="absolute top-0 left-12 right-12 h-[2px] bg-gradient-to-r from-transparent via-cyan-400 to-transparent shadow-[0_0_12px_#22d3ee]" />

        <div className="text-center mb-7">
          <div className="inline-flex items-center justify-center p-3 rounded-2xl bg-cyan-500/10 border border-cyan-400/30 text-cyan-400 mb-3.5 shadow-[0_0_20px_rgba(34,211,238,0.2)]">
            <Activity className="w-7 h-7 animate-pulse" />
          </div>
          <h1 className="text-2xl font-black tracking-widest text-slate-100 uppercase">
            Metro<span className="text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 to-blue-500">Flow</span>
          </h1>
          <p className="text-[11px] font-mono tracking-[0.25em] text-slate-400 mt-1 uppercase">
            Operations & Control Terminal
          </p>
        </div>

        <div className="grid grid-cols-2 p-1.5 rounded-xl bg-slate-950/80 border border-slate-800/80 mb-6 backdrop-blur-md">
          <button
            type="button"
            onClick={() => setRole('OPERATOR')}
            className={`flex items-center justify-center gap-2 py-2.5 rounded-lg text-xs font-bold tracking-wider transition-all duration-200 ${
              role === 'OPERATOR'
                ? 'bg-gradient-to-r from-cyan-500 to-blue-600 text-white shadow-[0_0_15px_rgba(6,182,212,0.35)]'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <UserCheck className="w-4 h-4" />
            OPERATOR
          </button>
          <button
            type="button"
            onClick={() => setRole('ADMIN')}
            className={`flex items-center justify-center gap-2 py-2.5 rounded-lg text-xs font-bold tracking-wider transition-all duration-200 ${
              role === 'ADMIN'
                ? 'bg-gradient-to-r from-blue-600 to-indigo-600 text-white shadow-[0_0_15px_rgba(59,130,246,0.35)]'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <ShieldCheck className="w-4 h-4" />
            ADMIN
          </button>
        </div>

        {error && (
          <div className="flex items-center gap-2.5 p-3 mb-5 text-xs text-rose-300 bg-rose-950/40 border border-rose-800/60 rounded-xl backdrop-blur-sm">
            <AlertCircle className="w-4 h-4 text-rose-400 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-[11px] font-mono tracking-wider text-slate-400 uppercase mb-1.5">
              Operator / Admin Email
            </label>
            <div className="relative group">
              <span className="absolute inset-y-0 left-0 flex items-center pl-3.5 pointer-events-none text-slate-500 group-focus-within:text-cyan-400 transition-colors">
                <Mail className="w-4 h-4" />
              </span>
              <input
                type="email"
                required
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder="name@metroflow.transit"
                className="w-full pl-10 pr-4 py-2.5 bg-slate-950/70 border border-slate-800 rounded-xl text-sm text-slate-100 placeholder-slate-600 focus:outline-none focus:border-cyan-400/80 focus:ring-1 focus:ring-cyan-400/40 transition-all font-mono"
              />
            </div>
          </div>

          <div>
            <label className="block text-[11px] font-mono tracking-wider text-slate-400 uppercase mb-1.5">
              Terminal Passkey
            </label>
            <div className="relative group">
              <span className="absolute inset-y-0 left-0 flex items-center pl-3.5 pointer-events-none text-slate-500 group-focus-within:text-cyan-400 transition-colors">
                <Lock className="w-4 h-4" />
              </span>
              <input
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••••••"
                className="w-full pl-10 pr-4 py-2.5 bg-slate-950/70 border border-slate-800 rounded-xl text-sm text-slate-100 placeholder-slate-600 focus:outline-none focus:border-cyan-400/80 focus:ring-1 focus:ring-cyan-400/40 transition-all font-mono"
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full mt-2 group relative overflow-hidden py-3 bg-gradient-to-r from-cyan-500 via-blue-600 to-indigo-600 hover:brightness-110 active:scale-[0.99] text-white text-xs font-extrabold tracking-widest uppercase rounded-xl shadow-[0_0_25px_rgba(6,182,212,0.3)] transition-all disabled:opacity-50 flex items-center justify-center gap-2"
          >
            {loading ? (
              <>
                <Zap className="w-4 h-4 animate-spin text-cyan-200" />
                <span>Authenticating Terminal...</span>
              </>
            ) : (
              <>
                <span>Enter Console as {role}</span>
                <ChevronRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
              </>
            )}
          </button>
        </form>

        <div className="mt-7 pt-4 border-t border-slate-800/80 flex items-center justify-between text-[11px] font-mono text-slate-500">
          <span>SEC PROTOCOL v2.4</span>
          <span className="inline-flex items-center gap-1.5 text-emerald-400">
            <Radio className="w-3 h-3 animate-pulse" />
            Online
          </span>
        </div>
      </div>
    </div>
  );
};