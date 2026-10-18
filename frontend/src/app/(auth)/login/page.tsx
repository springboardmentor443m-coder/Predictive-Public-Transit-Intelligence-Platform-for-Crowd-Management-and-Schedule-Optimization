"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Train, Lock, Mail, ShieldCheck, ArrowRight } from "lucide-react";
import { api } from "@/lib/api";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("operator@metroflow.com");
  const [password, setPassword] = useState("operator123");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      const res = await api.login(email, password);
      localStorage.setItem("metroflow_token", res.access_token);
      router.push("/dashboard");
    } catch (err: any) {
      setError(err.message || "Invalid email or password");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-[85vh] flex items-center justify-center">
      <div className="w-full max-w-md bg-[#0d1424] border border-slate-800 rounded-2xl p-8 shadow-2xl space-y-6">
        {/* Header */}
        <div className="text-center space-y-2">
          <div className="w-14 h-14 rounded-2xl bg-blue-600/20 border border-blue-500/30 flex items-center justify-center text-blue-400 mx-auto mb-3 shadow-lg shadow-blue-500/10">
            <Train className="w-8 h-8 text-blue-400" />
          </div>
          <h2 className="text-2xl font-black text-white tracking-wider">
            METRO<span className="text-blue-500">FLOW</span>
          </h2>
          <p className="text-xs text-slate-400 uppercase tracking-widest font-semibold">
            Operator Console Authentication
          </p>
        </div>

        {error && (
          <div className="p-3 rounded-lg bg-rose-500/10 border border-rose-500/30 text-rose-400 text-xs text-center font-medium">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-xs font-semibold text-slate-300 uppercase mb-1.5">
              Operator Email
            </label>
            <div className="relative">
              <Mail className="w-4 h-4 text-slate-500 absolute left-3 top-3" />
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                className="w-full bg-slate-900 border border-slate-700 rounded-lg pl-9 pr-4 py-2.5 text-sm text-white focus:outline-none focus:border-blue-500"
                placeholder="operator@metroflow.com"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-300 uppercase mb-1.5">
              Password
            </label>
            <div className="relative">
              <Lock className="w-4 h-4 text-slate-500 absolute left-3 top-3" />
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                className="w-full bg-slate-900 border border-slate-700 rounded-lg pl-9 pr-4 py-2.5 text-sm text-white focus:outline-none focus:border-blue-500"
                placeholder="••••••••"
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full py-3 bg-blue-600 hover:bg-blue-500 text-white rounded-lg font-bold text-sm transition flex items-center justify-center gap-2 shadow-lg shadow-blue-600/25 disabled:opacity-50"
          >
            {loading ? "Authenticating..." : "Sign In to Control Room"}
            <ArrowRight className="w-4 h-4" />
          </button>
        </form>

        {/* Demo Credentials Box */}
        <div className="p-3 bg-slate-900/80 border border-slate-800 rounded-lg text-xs space-y-1">
          <div className="font-semibold text-slate-300 flex items-center gap-1.5">
            <ShieldCheck className="w-4 h-4 text-emerald-400" />
            Quick Demo Login Credentials:
          </div>
          <div className="text-slate-400 font-mono text-[11px]">
            Email: <span className="text-blue-400">operator@metroflow.com</span> | Pass: <span className="text-blue-400">operator123</span>
          </div>
        </div>
      </div>
    </div>
  );
}
