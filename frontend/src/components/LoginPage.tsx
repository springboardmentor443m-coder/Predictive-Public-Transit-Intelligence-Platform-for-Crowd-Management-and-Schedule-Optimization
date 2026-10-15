import React, { useState } from 'react';

interface LoginPageProps {
  onLoginSuccess?: () => void;
}

export const LoginPage: React.FC<LoginPageProps> = ({ onLoginSuccess }) => {
  const [isSignUp, setIsSignUp] = useState<boolean>(false);
  const [role, setRole] = useState<'OPERATOR' | 'ADMIN'>('OPERATOR');
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const grantAccess = () => {
    if (onLoginSuccess) {
      onLoginSuccess();
    } else {
      window.location.reload();
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    if (!email.trim() || !password.trim()) {
      setErrorMsg('Please enter both email and passkey.');
      return;
    }

    const storedUsers = localStorage.getItem('metroflow_users');
    const usersList = storedUsers ? JSON.parse(storedUsers) : [];

    if (isSignUp) {
      if (password !== confirmPassword) {
        setErrorMsg('Passkeys do not match.');
        return;
      }

      const userExists = usersList.some((u: any) => u.email.toLowerCase() === email.toLowerCase());
      if (userExists) {
        setErrorMsg('Email already registered. Please sign in.');
        return;
      }

      const newUser = {
        name: name.trim() || 'Metro Controller',
        email: email.trim().toLowerCase(),
        password: password.trim(),
        role: role,
      };

      usersList.push(newUser);
      localStorage.setItem('metroflow_users', JSON.stringify(usersList));
      localStorage.setItem('metroflow_session', JSON.stringify(newUser));
      grantAccess();
    } else {
      const activeUser = {
        email: email.toLowerCase(),
        role: role,
      };
      localStorage.setItem('metroflow_session', JSON.stringify(activeUser));
      grantAccess();
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 flex items-center justify-center p-4">
      <div className="w-full max-w-md bg-slate-900 border border-slate-800 rounded-3xl p-8 shadow-2xl">
        {/* Logo and Title */}
        <div className="flex flex-col items-center mb-6">
          <div className="w-12 h-12 rounded-xl bg-slate-800 border border-slate-700 flex items-center justify-center text-emerald-400 mb-3">
            <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
            </svg>
          </div>
          <h1 className="text-xl font-black tracking-wider text-white">
            METRO<span className="text-emerald-400">FLOW</span>
          </h1>
          <p className="text-[10px] tracking-widest text-slate-400 uppercase mt-1">
            Operations & Control Terminal
          </p>
        </div>

        {/* Role Toggle */}
        <div className="grid grid-cols-2 gap-2 bg-slate-950 p-1.5 rounded-xl border border-slate-800 mb-5">
          <button
            type="button"
            onClick={() => setRole('OPERATOR')}
            className={
              role === 'OPERATOR'
                ? 'py-2 rounded-lg text-xs font-bold bg-emerald-600 text-white shadow'
                : 'py-2 rounded-lg text-xs font-bold text-slate-400'
            }
          >
            OPERATOR
          </button>
          <button
            type="button"
            onClick={() => setRole('ADMIN')}
            className={
              role === 'ADMIN'
                ? 'py-2 rounded-lg text-xs font-bold bg-emerald-600 text-white shadow'
                : 'py-2 rounded-lg text-xs font-bold text-slate-400'
            }
          >
            ADMIN
          </button>
        </div>

        {/* Error Alert */}
        {errorMsg && (
          <div className="p-3 mb-4 rounded-xl text-xs bg-rose-950/60 border border-rose-800 text-rose-300">
            {errorMsg}
          </div>
        )}

        {/* Input Form */}
        <form onSubmit={handleSubmit} className="space-y-4">
          {isSignUp && (
            <div>
              <label className="block text-[10px] font-bold text-slate-400 uppercase mb-1">
                Full Name
              </label>
              <input
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="Controller Name"
                className="w-full bg-slate-800 border border-slate-700 text-white px-3 py-2 rounded-xl text-xs focus:outline-none focus:border-emerald-500"
              />
            </div>
          )}

          <div>
            <label className="block text-[10px] font-bold text-slate-400 uppercase mb-1">
              Email Address
            </label>
            <input
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="user@metroflow.live"
              className="w-full bg-slate-800 border border-slate-700 text-white px-3 py-2 rounded-xl text-xs focus:outline-none focus:border-emerald-500"
            />
          </div>

          <div>
            <label className="block text-[10px] font-bold text-slate-400 uppercase mb-1">
              Terminal Passkey
            </label>
            <input
              type="password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
              className="w-full bg-slate-800 border border-slate-700 text-white px-3 py-2 rounded-xl text-xs focus:outline-none focus:border-emerald-500"
            />
          </div>

          {isSignUp && (
            <div>
              <label className="block text-[10px] font-bold text-slate-400 uppercase mb-1">
                Confirm Passkey
              </label>
              <input
                type="password"
                required
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                placeholder="••••••••"
                className="w-full bg-slate-800 border border-slate-700 text-white px-3 py-2 rounded-xl text-xs focus:outline-none focus:border-emerald-500"
              />
            </div>
          )}

          <button
            type="submit"
            className="w-full py-3 bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-xs uppercase rounded-xl transition-all shadow-lg shadow-emerald-900/30"
          >
            {isSignUp ? 'Create Account & Enter' : 'Enter Control Console'}
          </button>
        </form>

        {/* Mode Toggle Button */}
        <div className="mt-5 text-center">
          <button
            type="button"
            onClick={() => {
              setIsSignUp(!isSignUp);
              setErrorMsg(null);
            }}
            className="text-xs text-emerald-400 hover:underline"
          >
            {isSignUp ? 'Already registered? Sign In' : 'New Operator or Admin? Register Here'}
          </button>
        </div>
      </div>
    </div>
  );
};

export default LoginPage;