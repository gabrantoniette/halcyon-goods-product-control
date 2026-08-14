"use client";

import { createContext, useContext } from "react";

import type { Product } from "@/lib/schemas";

/**
 * Lives in its own module because the dashboard renders the table, and the
 * table's row actions need to reach back into the dashboard - importing the
 * dashboard from a row would be a cycle.
 */

export type FormMode = "create" | "replace" | "patch";

export type Dialogs = {
  openForm: (mode: FormMode, product?: Product) => void;
  openDelete: (product: Product) => void;
};

export const DialogContext = createContext<Dialogs | null>(null);

export function useDialogs(): Dialogs {
  const value = useContext(DialogContext);
  if (!value) throw new Error("useDialogs must be used inside the dashboard.");
  return value;
}

export type ToastKind = "success" | "error";

export type Toasts = {
  push: (kind: ToastKind, title: string, text?: string) => void;
};

export const ToastContext = createContext<Toasts | null>(null);

export function useToasts(): Toasts {
  const value = useContext(ToastContext);
  if (!value) throw new Error("useToasts must be used inside the dashboard.");
  return value;
}
