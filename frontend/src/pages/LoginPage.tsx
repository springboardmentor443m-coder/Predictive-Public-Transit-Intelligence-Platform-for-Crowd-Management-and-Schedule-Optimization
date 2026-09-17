import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Shield, Lock, User, ArrowRight, CheckCircle2, AlertCircle, Sparkles } from 'lucide-react';

export const LoginPage: React.FC = () => {
  const { login, isAuthenticated } = useAuth();
  const navigate = useNavigate();

  const [username, setUsername] = useState('operator');
  const [password, setPassword] = useState('operatorpassword');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      await login(username, password);
      navigate('/alerts');
    } catch (err: any) {
      setError(err.message || 'Authentication failed. Please check credentials.');
    } finally {
      setLoading(false);
    }
  };

  const handleQuickFill = (u: string, p: string) => {
    setUsername(u);
    setPassword(p);
  };

  return (
    <div className="min-h-[calc(100vh-8rem)] flex items-center justify-center p-4">
      <div className="w-full max-w-md bg-bg-surface/95 backdrop-blur-xl border border-border-dark rounded-3xl p-8 shadow-card space-y-6 relative overflow-hidden">
        {/* Subtle decorative neon aura in background */}
        <div className="absolute -top-24 -right-24 w-48 h-48 bg-metro-primary/20 rounded-full blur-3xl pointer-events-none" />
        <div className="absolute -bottom-24 -left-24 w-48 h-48 bg-metro-cyan/15 rounded-full blur-3xl pointer-events-none" />

        {/* Header */}
        <div className="text-center space-y-2 relative z-10">
          <div className="w-14 h-14 rounded-2xl bg-gradient-to-tr from-[#7928CA] via-[#A855F7] to-[#00F5D4] p-[1.5px] mx-auto shadow-glow">
            <div className="w-full h-full bg-bg-main rounded-[14px] flex items-center justify-center text-[#C084FC]">
              <Shield className="w-7 h-7 text-[#00F5D4]" />
            </div>
          </div>
          <h2 className="text-2xl font-black text-slate-100 tracking-tight font-sans mt-2">
            Operator Access Portal
          </h2>
          <p className="text-xs font-mono text-slate-400">
            Authenticate to manage live train dispatching and resolve critical incident alerts
          </p>
        </div>

        {error && (
          <div className="bg-[#3A0518]/80 border border-[#FF0055]/60 rounded-xl p-3 text-xs font-mono text-[#FF80A0] flex items-center gap-2 shadow-[0_0_12px_rgba(255,0,85,0.2)]">
            <AlertCircle className="w-4 h-4 shrink-0 text-[#FF0055]" />
            <span>{error}</span>
          </div>
        )}

        {/* Form */}
        <form onSubmit={handleSubmit} className="space-y-4 relative z-10">
          <div className="space-y-1.5 font-mono text-xs">
            <label className="text-slate-300 font-semibold">Operator Username</label>
            <div className="relative">
              <User className="w-4 h-4 text-slate-500 absolute left-3.5 top-3.5" />
              <input
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                required
                className="w-full pl-10 pr-3 py-3 bg-bg-card border border-border-dark rounded-xl text-slate-100 focus:outline-none focus:border-metro-primary focus:shadow-[0_0_15px_rgba(168,85,247,0.3)] transition-all"
              />
            </div>
          </div>

          <div className="space-y-1.5 font-mono text-xs">
            <label className="text-slate-300 font-semibold">Security Password</label>
            <div className="relative">
              <Lock className="w-4 h-4 text-slate-500 absolute left-3.5 top-3.5" />
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                className="w-full pl-10 pr-3 py-3 bg-bg-card border border-border-dark rounded-xl text-slate-100 focus:outline-none focus:border-metro-primary focus:shadow-[0_0_15px_rgba(168,85,247,0.3)] transition-all"
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full py-3 px-4 rounded-xl bg-gradient-to-r from-metro-primary to-[#7928CA] hover:from-[#B86BFC] hover:to-[#8E3DE8] text-white font-mono text-xs font-bold transition-all shadow-glow hover:shadow-[0_0_24px_rgba(168,85,247,0.6)] flex items-center justify-center gap-2 disabled:opacity-50"
          >
            <span>{loading ? 'Authenticating Token...' : 'Authorize & Sign In with JWT'}</span>
            <ArrowRight className="w-4 h-4" />
          </button>
        </form>

        {/* Quick Credentials Helper */}
        <div className="pt-4 border-t border-border-dark/60 space-y-2 text-xs font-mono relative z-10">
          <p className="text-[11px] text-slate-400 uppercase font-bold tracking-wider">
            Demo Quick-Fill Accounts:
          </p>
          <div className="grid grid-cols-2 gap-2">
            <button
              type="button"
              onClick={() => handleQuickFill('operator', 'operatorpassword')}
              className="p-3 rounded-xl bg-bg-card border border-border-dark hover:border-[#00F5D4]/60 text-left transition-all hover:shadow-[0_0_12px_rgba(0,245,212,0.2)] group"
            >
              <p className="font-bold text-slate-200 group-hover:text-[#00F5D4]">operator</p>
              <p className="text-[10px] text-slate-400">role: operator</p>
            </button>
            <button
              type="button"
              onClick={() => handleQuickFill('admin', 'adminpassword')}
              className="p-3 rounded-xl bg-bg-card border border-border-dark hover:border-metro-primary/60 text-left transition-all hover:shadow-[0_0_12px_rgba(168,85,247,0.2)] group"
            >
              <p className="font-bold text-slate-200 group-hover:text-[#C084FC]">admin</p>
              <p className="text-[10px] text-slate-400">role: admin</p>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
