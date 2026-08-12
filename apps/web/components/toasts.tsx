"use client";

import { useCallback, useMemo, useRef, useState } from "react";

import { ToastContext, type ToastKind, type Toasts } from "./ui-context";

type Toast = { id: number; kind: ToastKind; title: string; text?: string };

const LIFETIME = { success: 3200, error: 6000 } as const;

export function ToastProvider({ children }: { children: React.ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([]);
  const nextId = useRef(0);

  const push = useCallback((kind: ToastKind, title: string, text?: string) => {
    const id = nextId.current++;
    setToasts((current) => [...current, { id, kind, title, text }]);
    setTimeout(() => setToasts((current) => current.filter((toast) => toast.id !== id)), LIFETIME[kind]);
  }, []);

  const value = useMemo<Toasts>(() => ({ push }), [push]);

  return (
    <ToastContext value={value}>
      {children}

      <div
        role="region"
        aria-live="polite"
        aria-label="Notifications"
        className="pointer-events-none fixed right-4 bottom-4 z-50 flex w-[min(22rem,calc(100vw-2rem))] flex-col gap-2"
      >
        {toasts.map((toast) => (
          <div
            key={toast.id}
            className={`pointer-events-auto flex items-start gap-2 rounded-xl border p-3 shadow-[var(--shadow-md)] ${
              toast.kind === "success"
                ? "border-[var(--good)] bg-[var(--good-soft)]"
                : "border-[var(--critical)] bg-[var(--critical-soft)]"
            }`}
          >
            <span
              aria-hidden="true"
              className={`text-sm ${toast.kind === "success" ? "text-[var(--good)]" : "text-[var(--critical)]"}`}
            >
              {toast.kind === "success" ? "✓" : "✕"}
            </span>
            <div className="min-w-0 flex-1">
              <span className="block text-sm font-medium">{toast.title}</span>
              {toast.text && (
                <span className="block text-xs break-words text-[var(--ink-secondary)]">
                  {toast.text}
                </span>
              )}
            </div>
          </div>
        ))}
      </div>
    </ToastContext>
  );
}
