import { useState, useEffect } from "react";
import { AlertCircle, Eye, EyeOff, Loader2, ShieldCheck, Sparkles, TrainFront, Activity, CheckCircle2 } from "lucide-react";
import { useAuth } from "../lib/auth";
import { useToast } from "../components/ToastContext";
import api from "../lib/api";

const DEMO = [
  { role: "Admin", email: "admin@metroflow.io", password: "Admin@123", desc: "Full control, broadcasts & user management" },
  { role: "Operator", email: "operator@metroflow.io", password: "Operator@123", desc: "Timetables, delay logs & sensor ingest" },
  { role: "Viewer", email: "viewer@metroflow.io", password: "Viewer@123", desc: "Read-only live monitoring & analytics" },
];

export default function Login() {
  const { login } = useAuth();
  const { showToast } = useToast();
  const [email, setEmail] = useState("admin@metroflow.io");
  const [password, setPassword] = useState("Admin@123");
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [apiOnline, setApiOnline] = useState(null);

  useEffect(() => {
    // Check if backend is reachable
    api.get("/analytics/overview")
      .then(() => setApiOnline(true))
      .catch(() => setApiOnline(false));
  }, []);

  async function submit(e) {
    e.preventDefault();
    setError("");
    setBusy(true);
    try {
      await login(email, password);
      showToast("Signed in successfully. Welcome to MetroFlow!", "success");
      window.location.href = "/dashboard";
    } catch (err) {
      const detail = err?.response?.data?.detail;
      if (detail === "Incorrect email or password") {
        setError("Invalid email or password. Please verify credentials.");
      } else if (err?.response?.status === 403 || /deactivated/i.test(detail || "")) {
        setError("This account has been deactivated. Please contact your administrator.");
      } else {
        setError("Unable to connect to MetroFlow backend. Ensure Python FastAPI is running on port 8000.");
      }
      showToast("Sign in failed", "error");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="flex min-h-screen bg-slate-950 text-slate-100 font-sans selection:bg-brand-500 selection:text-white overflow-hidden">
      {/* Left Brand & Live Metro Visualizer Panel */}
      <div className="relative hidden flex-1 flex-col justify-between overflow-hidden bg-slate-950 p-12 lg:flex border-r border-slate-800/80">
        {/* Ambient Glowing Gradients */}
        <div className="absolute -right-24 -top-24 h-96 w-96 rounded-full bg-brand-600/25 blur-3xl animate-pulse-slow" />
        <div className="absolute -bottom-32 -left-20 h-96 w-96 rounded-full bg-emerald-500/20 blur-3xl animate-pulse-slow" />
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 h-[500px] w-[500px] rounded-full bg-indigo-600/10 blur-3xl" />

        {/* Top Header */}
        <div className="relative z-10 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <span className="flex h-12 w-12 items-center justify-center rounded-2xl bg-gradient-to-br from-brand-400 via-brand-600 to-indigo-700 shadow-lg shadow-brand-600/30 ring-1 ring-white/20">
              <TrainFront className="h-6 w-6 text-white" />
            </span>
            <div>
              <p className="text-xl font-extrabold tracking-tight text-white leading-tight">MetroFlow</p>
              <p className="text-xs font-semibold text-brand-400 tracking-wide">AI Transit Intelligence Console</p>
            </div>
          </div>
          <span className="inline-flex items-center gap-2 rounded-full bg-slate-900/90 px-3 py-1.5 text-xs font-bold text-slate-300 ring-1 ring-slate-800 backdrop-blur-md">
            <span className={`h-2 w-2 rounded-full ${apiOnline === true ? "bg-emerald-400 animate-ping" : apiOnline === false ? "bg-rose-400" : "bg-amber-400"}`} />
            {apiOnline === true ? "Backend Online · :8000" : apiOnline === false ? "Backend Offline" : "Checking Backend..."}
          </span>
        </div>

        {/* Center Futuristic Transit Map Simulation Graphic */}
        <div className="relative z-10 my-auto py-8">
          <div className="mb-6 space-y-3 max-w-lg">
            <span className="inline-flex items-center gap-1.5 rounded-full bg-brand-500/15 px-3 py-1 text-xs font-bold text-brand-300 ring-1 ring-brand-400/30">
              <Sparkles className="h-3.5 w-3.5" /> XGBoost & Realtime Socket Engine
            </span>
            <h1 className="text-4xl font-extrabold tracking-tight text-white leading-[1.15] sm:text-5xl">
              Predictive Transit Intelligence for Modern Metros
            </h1>
            <p className="text-sm text-slate-400 leading-relaxed">
              Centralized AI crowd density forecasting, headway optimization, delay inference, and emergency incident dispatch — built without CCTV.
            </p>
          </div>

          {/* Animated Metro Line Graphic */}
          <div className="relative rounded-2xl border border-slate-800/90 bg-slate-900/80 p-5 backdrop-blur-xl shadow-2xl">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3 mb-4 text-xs font-bold text-slate-400">
              <span className="flex items-center gap-2 text-white"><Activity className="h-4 w-4 text-brand-400" /> LIVE NETWORK TOPOLOGY</span>
              <span className="text-emerald-400 font-mono">10 Stations Monitored</span>
            </div>
            
            <svg viewBox="0 0 400 120" className="w-full h-auto">
              {/* Red Line */}
              <path d="M 30 30 L 150 30 L 250 80 L 370 80" fill="none" stroke="#ef4444" strokeWidth="4" strokeLinecap="round" opacity="0.8" />
              {/* Blue Line */}
              <path d="M 30 80 L 150 80 L 250 30 L 370 30" fill="none" stroke="#3b82f6" strokeWidth="4" strokeLinecap="round" opacity="0.8" />
              {/* Green Line */}
              <path d="M 80 10 L 80 110" fill="none" stroke="#10b981" strokeWidth="3" strokeDasharray="6 4" opacity="0.6" />

              {/* Station Dots */}
              {[[30,30,"ST01"], [150,30,"ST02"], [250,80,"ST03"], [370,80,"ST04"], [30,80,"ST05"], [150,80,"ST06"], [250,30,"ST07"], [370,30,"ST08"]].map(([x,y,id], i) => (
                <g key={id}>
                  <circle cx={x} cy={y} r="6" fill="#0f172a" stroke="#ffffff" strokeWidth="2" />
                  <circle cx={x} cy={y} r="3" fill={i % 3 === 0 ? "#ef4444" : i % 2 === 0 ? "#10b981" : "#3b82f6"} />
                  <text x={x} y={y - 10} textAnchor="middle" fill="#94a3b8" fontSize="8" fontWeight="bold">{id}</text>
                </g>
              ))}
            </svg>

            <div className="grid grid-cols-3 gap-3 pt-4 border-t border-slate-800/80">
              {[
                ["10", "Live Stations"],
                ["<2s", "Socket Latency"],
                ["0.896", "Crowd R² Metric"],
              ].map(([v, l]) => (
                <div key={l} className="rounded-xl border border-slate-800 bg-slate-950/60 p-3 text-center">
                  <p className="text-xl font-extrabold text-brand-400 font-mono">{v}</p>
                  <p className="text-[11px] font-medium text-slate-400">{l}</p>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Footer */}
        <p className="relative z-10 text-xs text-slate-500 font-medium">
          © 2026 MetroFlow · Transportation Intelligence Platform · All Rights Reserved
        </p>
      </div>

      {/* Right Login Form Panel */}
      <div className="flex flex-1 items-center justify-center p-6 sm:p-12 relative">
        <div className="w-full max-w-md space-y-6">
          {/* Mobile Logo Branding */}
          <div className="flex items-center gap-3 lg:hidden mb-4">
            <span className="flex h-10 w-10 items-center justify-center rounded-xl bg-brand-600 shadow-lg">
              <TrainFront className="h-5 w-5 text-white" />
            </span>
            <div>
              <p className="text-lg font-bold text-white">MetroFlow</p>
              <p className="text-xs text-slate-400">Transit Control Panel</p>
            </div>
          </div>

          <div className="card card-pad sm:p-8 border-slate-800 bg-slate-900/95 shadow-2xl backdrop-blur-2xl">
            <div className="space-y-1">
              <h2 className="text-2xl font-extrabold text-white tracking-tight">Console Sign In</h2>
              <p className="text-sm text-slate-400">Access role-authenticated transit management dashboards.</p>
            </div>

            {error && (
              <div className="mt-4 flex items-start gap-2.5 rounded-xl bg-rose-500/10 p-3.5 text-xs text-rose-300 ring-1 ring-rose-500/30">
                <AlertCircle className="mt-0.5 h-4 w-4 shrink-0 text-rose-400" />
                <div className="min-w-0 flex-1">{error}</div>
              </div>
            )}

            <form onSubmit={submit} className="mt-6 space-y-4">
              <div>
                <label className="label">Operator / Admin Email</label>
                <input
                  type="email"
                  required
                  className="input"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="admin@metroflow.io"
                />
              </div>

              <div>
                <label className="label">Password</label>
                <div className="relative">
                  <input
                    type={showPassword ? "text" : "password"}
                    required
                    className="input pr-10"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="••••••••"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-200 transition"
                  >
                    {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                  </button>
                </div>
              </div>

              <button type="submit" disabled={busy} className="btn-primary w-full py-3 text-sm font-extrabold tracking-wide">
                {busy ? <Loader2 className="h-4 w-4 animate-spin" /> : <ShieldCheck className="h-4 w-4" />}
                {busy ? "Authenticating…" : "Sign In to Operations Console"}
              </button>
            </form>

            {/* Demo Accounts Quick Select */}
            <div className="mt-6 border-t border-slate-800/80 pt-5">
              <div className="flex items-center justify-between mb-2">
                <p className="text-[11px] font-extrabold uppercase tracking-wider text-slate-400">
                  Quick Demo Accounts
                </p>
                <span className="text-[10px] text-brand-400 font-semibold">Click to autofill</span>
              </div>
              
              <div className="space-y-2">
                {DEMO.map((d) => (
                  <button
                    key={d.role}
                    type="button"
                    onClick={() => {
                      setEmail(d.email);
                      setPassword(d.password);
                      showToast(`Autofilled ${d.role} credentials`, "info");
                    }}
                    className={`w-full flex items-center justify-between rounded-xl border px-3 py-2 text-xs transition text-left ${
                      email === d.email
                        ? "border-brand-500 bg-brand-500/15 text-white ring-1 ring-brand-500/30"
                        : "border-slate-800 bg-slate-950/40 text-slate-300 hover:border-slate-700 hover:bg-slate-800/60"
                    }`}
                  >
                    <div>
                      <div className="flex items-center gap-1.5 font-bold">
                        <span>{d.role}</span>
                        {email === d.email && <CheckCircle2 className="h-3.5 w-3.5 text-brand-400" />}
                      </div>
                      <p className="text-[11px] text-slate-400">{d.desc}</p>
                    </div>
                    <span className="font-mono text-[10px] text-slate-400 bg-slate-800/80 px-1.5 py-0.5 rounded">
                      {d.email.split("@")[0]}
                    </span>
                  </button>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
