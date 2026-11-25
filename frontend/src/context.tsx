import { createContext, useContext, useState, type ReactNode } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { CheckCircle2, CircleAlert } from "lucide-react";
import type { ReferenceData } from "./types";

const ReferenceContext = createContext<ReferenceData | null>(null);

export function ReferenceProvider({ value, children }: { value: ReferenceData; children: ReactNode }) {
  return <ReferenceContext.Provider value={value}>{children}</ReferenceContext.Provider>;
}

export function useReference(): ReferenceData {
  const value = useContext(ReferenceContext);
  if (!value) throw new Error("Reference data is not loaded.");
  return value;
}

type Toast = { id: number; tone: "ok" | "err"; message: string };
type PushToast = (message: string, tone?: "ok" | "err") => void;

const ToastContext = createContext<PushToast>(() => {});

export function useToast(): PushToast {
  return useContext(ToastContext);
}

export function ToastProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([]);

  function push(message: string, tone: "ok" | "err" = "ok") {
    const id = Date.now() + Math.random();
    setToasts((current) => [...current, { id, tone, message }]);
    window.setTimeout(() => {
      setToasts((current) => current.filter((toast) => toast.id !== id));
    }, 3600);
  }

  return (
    <ToastContext.Provider value={push}>
      {children}
      <div className="toasts" aria-live="polite">
        <AnimatePresence>
          {toasts.map((toast) => (
            <motion.div
              key={toast.id}
              className={toast.tone === "ok" ? "toast" : "toast toast-err"}
              role="status"
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: 8 }}
            >
              {toast.tone === "ok" ? <CheckCircle2 size={18} /> : <CircleAlert size={18} />}
              <span>{toast.message}</span>
            </motion.div>
          ))}
        </AnimatePresence>
      </div>
    </ToastContext.Provider>
  );
}

export function labelFor(options: { value: string; label: string }[], value: string): string {
  return options.find((item) => item.value === value)?.label ?? value;
}
