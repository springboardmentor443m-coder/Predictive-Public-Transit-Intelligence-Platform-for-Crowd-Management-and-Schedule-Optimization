import { createContext, useContext, useState, useCallback } from "react";
import { CheckCircle2, AlertTriangle, AlertCircle, Info, X, Volume2, VolumeX } from "lucide-react";

const ToastContext = createContext({
  showToast: () => {},
  soundEnabled: true,
  setSoundEnabled: () => {},
});

export function ToastProvider({ children }) {
  const [toasts, setToasts] = useState([]);
  const [soundEnabled, setSoundEnabled] = useState(true);

  const playTone = useCallback((type) => {
    if (!soundEnabled || typeof window === "undefined") return;
    try {
      const ctx = new (window.AudioContext || window.webkitAudioContext)();
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();
      osc.connect(gain);
      gain.connect(ctx.destination);
      
      const freqs = {
        success: 587.33, // D5
        error: 329.63,   // E4
        warning: 440,    // A4
        info: 523.25,    // C5
      };
      osc.frequency.value = freqs[type] || 523.25;
      gain.gain.setValueAtTime(0.08, ctx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.25);
      osc.start();
      osc.stop(ctx.currentTime + 0.25);
    } catch {}
  }, [soundEnabled]);

  const showToast = useCallback((message, type = "info", title = "") => {
    const id = Date.now() + Math.random().toString(36).substring(2, 5);
    setToasts((prev) => [...prev, { id, message, type, title }]);
    playTone(type);
    setTimeout(() => {
      setToasts((prev) => prev.filter((t) => t.id !== id));
    }, 4500);
  }, [playTone]);

  const dismiss = (id) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  };

  return (
    <ToastContext.Provider value={{ showToast, soundEnabled, setSoundEnabled }}>
      {children}
      {/* Toast Overlay */}
      <div className="fixed bottom-5 right-5 z-50 flex max-w-md flex-col gap-2.5 pointer-events-none">
        {toasts.map((t) => {
          const icons = {
            success: <CheckCircle2 className="h-5 w-5 text-emerald-400 shrink-0 mt-0.5" />,
            warning: <AlertTriangle className="h-5 w-5 text-amber-400 shrink-0 mt-0.5" />,
            error: <AlertCircle className="h-5 w-5 text-rose-400 shrink-0 mt-0.5" />,
            info: <Info className="h-5 w-5 text-brand-400 shrink-0 mt-0.5" />,
          };
          const borders = {
            success: "border-emerald-500/40 bg-slate-900/95 text-emerald-100",
            warning: "border-amber-500/40 bg-slate-900/95 text-amber-100",
            error: "border-rose-500/40 bg-slate-900/95 text-rose-100",
            info: "border-brand-500/40 bg-slate-900/95 text-blue-100",
          };

          return (
            <div
              key={t.id}
              className={`pointer-events-auto flex items-start gap-3 rounded-2xl border ${borders[t.type]} p-4 shadow-2xl backdrop-blur-xl animate-in slide-in-from-right duration-300`}
            >
              {icons[t.type]}
              <div className="min-w-0 flex-1">
                {t.title && <p className="text-xs font-bold uppercase tracking-wider opacity-90">{t.title}</p>}
                <p className="text-sm font-medium leading-snug">{t.message}</p>
              </div>
              <button
                onClick={() => dismiss(t.id)}
                className="text-slate-400 hover:text-white transition p-1 rounded-lg hover:bg-white/10"
              >
                <X className="h-4 w-4" />
              </button>
            </div>
          );
        })}
      </div>
    </ToastContext.Provider>
  );
}

export function useToast() {
  return useContext(ToastContext);
}
