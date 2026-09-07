import { useState } from "react";
import { AlertCircle, Loader2, TrainFront } from "lucide-react";
import { useAuth } from "../lib/auth";

const DEMO = [
  { role: "Admin", email: "admin@metroflow.io", password: "Admin@123" },
  { role: "Operator", email: "operator@metroflow.io", password: "Operator@123" },
  { role: "Viewer", email: "viewer@metroflow.io", password: "Viewer@123" },
];

export default function Login() {
  const { login } = useAuth();
  const [email, setEmail] = useState("admin@metroflow.io");
  const [password, setPassword] = useState("Admin@123");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function submit(e) {
    e.preventDefault();
    setError("");
    setBusy(true);
    try {
      await login(email, password);
      window.location.href = "/dashboard";
    } catch (err) {
      const detail = err?.response?.data?.detail;
      if (detail === "Incorrect email or password") {
        setError("Invalid email or password. No matching account found.");
      } else if (err?.response?.status === 403 || /deactivated/i.test(detail || "")) {
        setError("This account has been deactivated. Please contact your administrator for support.");
      } else {
        setError("Login failed. Is the backend running on port 8000?");
      }
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="flex min-h-screen">
      {/* Left brand panel */}
      <div className="relative hidden flex-1 flex-col justify-between overflow-hidden bg-slate-900 p-12 text-white lg:flex">
        <div className="absolute -right-32 -top-32 h-96 w-96 rounded-full bg-brand-600/30 blur-3xl" />
        <div className="absolute -bottom-40 -left-20 h-96 w-96 rounded-full bg-brand-500/20 blur-3xl" />
        <div className="relative flex items-center gap-3">
          <span className="flex h-11 w-11 items-center justify-center rounded-xl bg-brand-600">
            <TrainFront className="h-6 w-6" />
          </span>
          <div>
            <p className="text-xl font-bold leading-tight">MetroFlow</p>
            <p className="text-xs text-slate-400">Transit Intelligence Platform</p>
          </div>
        </div>
        <div className="relative max-w-md space-y-5">
          <h1 className="text-4xl font-extrabold leading-tight">
            AI-powered crowd management & scheduling for modern metros.
          </h1>
          <p className="text-slate-400">
            Monitor passenger density in real time, forecast demand with machine learning,
            optimize train frequency during peak hours, and respond to incidents instantly —
            all from one operations console.
          </p>
          <div className="grid grid-cols-3 gap-4 pt-2">
            {[
              ["10", "Stations"],
              ["24/7", "Monitoring"],
              ["<2s", "Live latency"],
            ].map(([v, l]) => (
              <div key={l} className="rounded-xl border border-slate-700/60 bg-slate-800/50 p-4">
                <p className="text-2xl font-bold text-brand-400">{v}</p>
                <p className="text-xs text-slate-400">{l}</p>
              </div>
            ))}
          </div>
        </div>
        <p className="relative text-xs text-slate-500">© 2026 MetroFlow · Smart Transportation Systems</p>
      </div>

      {/* Right form panel */}
      <div className="flex flex-1 items-center justify-center bg-slate-100 p-6">
        <div className="w-full max-w-md">
          <div className="mb-8 flex items-center gap-3 lg:hidden">
            <span className="flex h-10 w-10 items-center justify-center rounded-lg bg-brand-600">
              <TrainFront className="h-5 w-5 text-white" />
            </span>
            <p className="text-lg font-bold text-slate-900">MetroFlow</p>
          </div>

          <div className="card card-pad sm:p-8">
            <h2 className="text-2xl font-bold text-slate-900">Sign in</h2>
            <p className="mt-1 text-sm text-slate-500">Access the metro operations dashboard.</p>

            {error && (
              <div className="mt-4 flex items-start gap-2 rounded-lg bg-rose-50 p-3 text-sm text-rose-700 ring-1 ring-rose-200">
                <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" />
                {error}
              </div>
            )}

            <form onSubmit={submit} className="mt-6 space-y-4">
              <div>
                <label className="label">Email</label>
                <input
                  type="email"
                  required
                  className="input"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="you@metroflow.io"
                />
              </div>
              <div>
                <label className="label">Password</label>
                <input
                  type="password"
                  required
                  className="input"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                />
              </div>
              <button type="submit" disabled={busy} className="btn-primary w-full py-2.5">
                {busy && <Loader2 className="h-4 w-4 animate-spin" />}
                {busy ? "Signing in…" : "Sign in"}
              </button>
            </form>

            <div className="mt-6 border-t border-slate-200 pt-4">
              <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-slate-400">
                Demo accounts
              </p>
              <div className="grid grid-cols-3 gap-2">
                {DEMO.map((d) => (
                  <button
                    key={d.role}
                    type="button"
                    onClick={() => {
                      setEmail(d.email);
                      setPassword(d.password);
                    }}
                    className="rounded-lg border border-slate-200 px-2 py-1.5 text-xs font-medium text-slate-600 transition hover:border-brand-300 hover:bg-brand-50 hover:text-brand-700"
                  >
                    {d.role}
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
