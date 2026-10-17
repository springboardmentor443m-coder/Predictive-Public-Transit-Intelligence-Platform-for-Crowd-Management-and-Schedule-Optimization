import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import { Input } from '../components/common/Input';
import { Button } from '../components/common/Button';
import { Cpu, ShieldCheck, Lock, AlertCircle, Info } from 'lucide-react';

export const LoginPage: React.FC = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const { login } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (!email || !password) {
      setError('Please enter both email and password.');
      return;
    }

    setLoading(true);
    try {
      await login(email, password);
      navigate('/dashboard');
    } catch (err: any) {
      const message = err.response?.data?.detail || 'Authentication failed. Please check credentials.';
      setError(message);
    } finally {
      setLoading(false);
    }
  };

  const fillDemoAdmin = () => {
    setEmail('admin@metroflow.io');
    setPassword('AdminPassword123!');
  };

  return (
    <div className="min-h-screen bg-[#0B0F17] bg-grid-pattern flex items-center justify-center p-4 relative overflow-hidden">
      {/* Dynamic Background Glow Elements */}
      <div className="absolute top-1/4 left-1/2 -translate-x-1/2 -translate-y-1/2 w-96 h-96 bg-cyan-500/10 rounded-full blur-3xl pointer-events-none" />
      <div className="absolute bottom-1/4 right-1/4 w-80 h-80 bg-blue-600/10 rounded-full blur-3xl pointer-events-none" />

      <div className="w-full max-w-md space-y-6 relative z-10">
        {/* Brand Logo & Title */}
        <div className="text-center space-y-2">
          <div className="inline-flex p-3 rounded-2xl bg-slate-900 border border-slate-800 text-cyan-400 shadow-xl shadow-cyan-950/40 mb-2">
            <Cpu className="w-8 h-8" />
          </div>
          <h1 className="text-2xl font-extrabold tracking-wider font-mono text-slate-100">
            METROFLOW
          </h1>
          <p className="text-xs text-slate-400 font-mono tracking-wide">
            Intelligent Metro Operations Control Platform
          </p>
        </div>

        {/* Login Card */}
        <div className="glass-panel p-8 rounded-2xl border border-slate-800/80 shadow-2xl space-y-6">
          <div className="flex items-center justify-between pb-4 border-b border-slate-800">
            <h2 className="text-sm font-semibold font-mono text-slate-200 tracking-wide flex items-center gap-2">
              <Lock className="w-4 h-4 text-cyan-400" />
              AUTHENTICATION PORTAL
            </h2>
            <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-cyan-950 text-cyan-400 border border-cyan-800/60">
              JWT Secured
            </span>
          </div>

          {error && (
            <div className="p-3.5 rounded-lg bg-rose-950/80 border border-rose-800/60 text-rose-300 text-xs flex items-start gap-2.5">
              <AlertCircle className="w-4 h-4 text-rose-400 shrink-0 mt-0.5" />
              <span>{error}</span>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <Input
              label="Operator Email"
              type="email"
              placeholder="operator@metroflow.io"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />

            <Input
              label="Access Password"
              type="password"
              placeholder="••••••••••••"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />

            <Button
              type="submit"
              variant="primary"
              size="lg"
              className="w-full mt-2"
              isLoading={loading}
            >
              <ShieldCheck className="w-4 h-4 mr-1" />
              Authenticate Session
            </Button>
          </form>

          {/* Seed Admin Helper Tip */}
          <div className="pt-4 border-t border-slate-800/80 text-xs text-slate-400 space-y-2">
            <div className="flex items-center justify-between">
              <span className="flex items-center gap-1.5 font-mono text-[11px] text-slate-400">
                <Info className="w-3.5 h-3.5 text-cyan-400" />
                Initial Setup Account:
              </span>
              <button
                onClick={fillDemoAdmin}
                type="button"
                className="text-[11px] font-mono text-cyan-400 hover:underline"
              >
                Auto-fill Admin Credentials
              </button>
            </div>
            <div className="p-2.5 rounded-lg bg-slate-900/80 border border-slate-800 font-mono text-[11px] text-slate-400 space-y-1">
              <div><span className="text-slate-500">Email:</span> admin@metroflow.io</div>
              <div><span className="text-slate-500">Password:</span> AdminPassword123!</div>
            </div>
          </div>
        </div>

        {/* Footer info */}
        <p className="text-center text-[11px] text-slate-500 font-mono">
          MetroFlow Operations Platform • Secure RBAC & Audit Log
        </p>
      </div>
    </div>
  );
};
