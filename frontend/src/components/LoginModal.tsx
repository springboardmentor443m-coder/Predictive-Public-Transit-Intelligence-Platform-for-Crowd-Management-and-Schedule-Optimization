import React, { useState } from 'react';
import { X, Shield, User as UserIcon, Lock, KeyRound, CheckCircle2 } from 'lucide-react';
import { api } from '../services/api';
import { User } from '../types';

interface LoginModalProps {
  isOpen: boolean;
  onClose: () => void;
  onLoginSuccess: (user: User) => void;
}

export const LoginModal: React.FC<LoginModalProps> = ({ isOpen, onClose, onLoginSuccess }) => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      const res = await api.login(email, password);
      onLoginSuccess(res.user);
      onClose();
    } catch (err: any) {
      setError(err.message || 'Invalid credentials');
    } finally {
      setLoading(false);
    }
  };

  const handleQuickLogin = async (role: 'admin' | 'operator') => {
    setError(null);
    setLoading(true);
    const creds = role === 'admin' 
      ? { email: 'admin@metroflow.ny', pass: 'admin123' }
      : { email: 'operator@metroflow.ny', pass: 'operator123' };

    try {
      const res = await api.login(creds.email, creds.pass);
      onLoginSuccess(res.user);
      onClose();
    } catch (err: any) {
      setError(err.message || 'Quick login failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-[2200] flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-in fade-in duration-150">
      <div className="bg-slate-900 border border-slate-700 rounded-2xl w-full max-w-md shadow-2xl p-6 text-slate-100 relative">
        <button
          onClick={onClose}
          className="absolute top-4 right-4 p-2 text-slate-400 hover:text-white rounded-lg transition"
        >
          <X className="w-5 h-5" />
        </button>

        <div className="text-center mb-6">
          <div className="inline-flex p-3 rounded-2xl bg-blue-600/20 text-blue-400 border border-blue-500/30 mb-3">
            <KeyRound className="w-6 h-6" />
          </div>
          <h2 className="text-xl font-bold text-white">Transit Control Authentication</h2>
          <p className="text-xs text-slate-400 mt-1">Role-Based Access Control for MetroFlow Operations</p>
        </div>

        {error && (
          <div className="mb-4 p-3 rounded-xl bg-red-500/20 border border-red-500/40 text-red-300 text-xs text-center">
            {error}
          </div>
        )}

        {/* Quick One-Click Switcher for pair programming / testing */}
        <div className="mb-6 p-3.5 bg-slate-950 rounded-xl border border-slate-800 space-y-2">
          <div className="text-[11px] font-bold text-slate-400 uppercase tracking-wider text-center">
            One-Click Test Accounts
          </div>
          <div className="grid grid-cols-2 gap-2">
            <button
              type="button"
              onClick={() => handleQuickLogin('admin')}
              className="p-2.5 bg-purple-600/20 hover:bg-purple-600/30 border border-purple-500/40 rounded-xl text-left transition cursor-pointer"
            >
              <div className="flex items-center space-x-1.5 text-xs font-bold text-purple-300">
                <Shield className="w-3.5 h-3.5" />
                <span>Admin Login</span>
              </div>
              <div className="text-[10px] text-slate-400 mt-0.5">Chief Director (Full Access)</div>
            </button>

            <button
              type="button"
              onClick={() => handleQuickLogin('operator')}
              className="p-2.5 bg-blue-600/20 hover:bg-blue-600/30 border border-blue-500/40 rounded-xl text-left transition cursor-pointer"
            >
              <div className="flex items-center space-x-1.5 text-xs font-bold text-blue-300">
                <UserIcon className="w-3.5 h-3.5" />
                <span>Operator Login</span>
              </div>
              <div className="text-[10px] text-slate-400 mt-0.5">Line Rail Dispatcher</div>
            </button>
          </div>
        </div>

        {/* Standard Form */}
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1">Transit ID / Email</label>
            <input
              type="email"
              value={email}
              onChange={e => setEmail(e.target.value)}
              placeholder="e.g. admin@metroflow.ny"
              required
              className="w-full px-3.5 py-2.5 bg-slate-950 border border-slate-800 rounded-xl text-xs text-white placeholder-slate-500 focus:outline-none focus:border-blue-500"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1">Security Passcode</label>
            <input
              type="password"
              value={password}
              onChange={e => setPassword(e.target.value)}
              placeholder="Enter passcode"
              required
              className="w-full px-3.5 py-2.5 bg-slate-950 border border-slate-800 rounded-xl text-xs text-white placeholder-slate-500 focus:outline-none focus:border-blue-500"
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full py-2.5 bg-blue-600 hover:bg-blue-500 text-white rounded-xl text-xs font-bold transition shadow-lg shadow-blue-600/30 cursor-pointer disabled:opacity-50"
          >
            {loading ? 'Authenticating...' : 'Sign In to Transit Console'}
          </button>
        </form>
      </div>
    </div>
  );
};
