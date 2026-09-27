import React, {
  createContext,
  useContext,
  useState,
  useCallback,
  type ReactNode,
} from "react";
import { CheckCircle2, AlertTriangle, AlertCircle, Info, X } from "lucide-react";

type ToastType = "success" | "warning" | "error" | "info";

interface Toast {
  id: string;
  message: string;
  type: ToastType;
  title: string;
}

interface ToastContextValue {
  showToast: (message: string, type?: ToastType, title?: string) => void;
  soundEnabled: boolean;
  setSoundEnabled: (enabled: boolean) => void;
}

const ToastContext = createContext<ToastContextValue>({
  showToast: () => {},
  soundEnabled: true,
  setSoundEnabled: () => {},
});

type AudioContextCtor = typeof AudioContext;

export function ToastProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([]);
  const [soundEnabled, setSoundEnabled] = useState(true);

  const playTone = useCallback(
    (type: ToastType) => {
      if (!soundEnabled || typeof window === "undefined") return;
      try {
        const Ctor: AudioContextCtor =
          window.AudioContext || (window as unknown as { webkitAudioContext: AudioContextCtor }).webkitAudioContext;
        const ctx = new Ctor();
        const osc = ctx.createOscillator();
        const gain = ctx.createGain();
        osc.connect(gain);
        gain.connect(ctx.destination);

        const freqs: Record<ToastType, number> = {
          success: 587.33, // D5
          error: 329.63, // E4
          warning: 440, // A4
          info: 523.25, // C5
        };
        osc.frequency.value = freqs[type] || 523.25;
        gain.gain.setValueAtTime(0.08, ctx.currentTime);
        gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.25);
        osc.start();
        osc.stop(ctx.currentTime + 0.25);
      } catch {}
    },
    [soundEnabled]
  );

  const showToast = useCallback(
    (message: string, type: ToastType = "info", title: string = "") => {
      const id = Date.now() + Math.random().toString(36).substring(2, 5);
      setToasts((prev) => [...prev, { id, message, type, title }]);
      playTone(type);
      setTimeout(() => {
        setToasts((prev) => prev.filter((t) => t.id !== id));
      }, 4500);
    },
    [playTone]
  );

  const dismiss = (id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  };

  const icons: Record<ToastType, ReactNode> = {
    success: <CheckCircle2 className="h-5 w-5 text-emerald-400 shrink-0 mt-0.5" />,
    warning: <AlertTriangle className="h-5 w-5 text-amber-400 shrink-0 mt-0.5" />,
    error: <AlertCircle className="h-5 w-5 text-rose-400 shrink-0 mt-0.5" />,
    info: <Info className="h-5 w-5 text-brand-400 shrink-0 mt-0.5" />,
  };

  const variants: Record<ToastType, string> = {
    success: "toast-success",
    warning: "toast-warning",
    error: "toast-error",
    info: "toast-info",
  };

  return (
    <ToastContext.Provider value={{ showToast, soundEnabled, setSoundEnabled }}>
      {children}
      {/* Toast Overlay */}
      <div className="fixed bottom-5 right-5 z-50 flex max-w-md flex-col gap-2.5 pointer-events-none">
        {toasts.map((t) => (
          <div
            key={t.id}
            className={`toast animate-toast-in ${variants[t.type]}`}
          >
            {icons[t.type]}
            <div className="min-w-0 flex-1">
              {t.title && <p className="text-xs font-bold uppercase tracking-wider opacity-90">{t.title}</p>}
              <p className="text-sm font-medium leading-snug">{t.message}</p>
            </div>
            <button
              onClick={() => dismiss(t.id)}
              className="text-slate-500 hover:text-white transition p-1 rounded-lg hover:bg-slate-800"
            >
              <X className="h-4 w-4" />
            </button>
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  );
}

export function useToast(): ToastContextValue {
  return useContext(ToastContext);
}