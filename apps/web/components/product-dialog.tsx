"use client";

import { useActionState, useEffect, useRef } from "react";
import { useFormStatus } from "react-dom";

import { patchProductAction, registerProduct, replaceProductAction } from "@/app/actions";
import type { ActionResult, Product } from "@/lib/schemas";
import { useToasts, type FormMode } from "./ui-context";

const TITLES: Record<FormMode, [string, string]> = {
  create: ["Register item", "Adds a new item to the internal register."],
  replace: ["Edit item", "Every field is rewritten with what you submit."],
  patch: ["Quick edit", "Only the fields you change are sent."],
};

const ACTIONS = {
  create: registerProduct,
  replace: replaceProductAction,
  patch: patchProductAction,
};

const INPUT =
  "h-9 rounded-lg border bg-[var(--surface)] px-2.5 text-sm outline-none focus-visible:border-[var(--accent)]";

export function ProductDialog({
  open,
  mode,
  product,
  categories,
  onClose,
}: {
  open: boolean;
  mode: FormMode;
  product: Product | null;
  categories: string[];
  onClose: () => void;
}) {
  const dialogRef = useRef<HTMLDialogElement>(null);
  const { push } = useToasts();

  const [result, formAction] = useActionState<ActionResult | null, FormData>(ACTIONS[mode], null);

  // showModal/close are imperative, so the open prop is mirrored onto the
  // element rather than rendered.
  useEffect(() => {
    const dialog = dialogRef.current;
    if (!dialog) return;
    if (open && !dialog.open) dialog.showModal();
    if (!open && dialog.open) dialog.close();
  }, [open]);

  useEffect(() => {
    if (!result) return;
    if (result.ok) {
      push("success", result.message);
      onClose();
    } else if (!result.fieldErrors) {
      // Field-level problems are shown next to the input; only the rest need a
      // toast to be noticed.
      push("error", "Request failed", result.message);
    }
  }, [result, push, onClose]);

  const [title, subtitle] = TITLES[mode];
  const errors = result?.fieldErrors ?? {};

  /** What the PATCH action diffs against, so only real changes are sent. */
  const original = product
    ? JSON.stringify({
        name: product.name,
        category: product.category,
        price: product.price,
        stock: product.stock,
        rating: product.rating,
        in_stock: product.in_stock,
        tags: product.tags,
      })
    : "{}";

  return (
    <dialog
      ref={dialogRef}
      onClose={onClose}
      onCancel={onClose}
      className="m-auto w-[min(42rem,calc(100vw-2rem))] rounded-2xl border bg-[var(--surface-raised)] p-0 shadow-[var(--shadow-md)] backdrop:bg-black/50"
    >
      {/* Remounted per mode/product so the inputs reset and stale errors go. */}
      <form action={formAction} key={`${mode}:${product?.uuid ?? "new"}`} noValidate>
        <input type="hidden" name="__target" value={product?.name ?? ""} />
        <input type="hidden" name="__original" value={original} />

        <div className="flex items-start justify-between gap-4 border-b p-4">
          <div>
            <h2 className="text-base font-semibold">{title}</h2>
            <p className="mt-0.5 text-xs text-[var(--ink-muted)]">{subtitle}</p>
          </div>
          <button
            type="button"
            onClick={onClose}
            aria-label="Close"
            className="flex h-8 w-8 items-center justify-center rounded-lg border text-[var(--ink-secondary)] hover:bg-[var(--surface-sunken)]"
          >
            ✕
          </button>
        </div>

        <div className="grid grid-cols-1 gap-3 p-4 sm:grid-cols-2">
          <Field label="Item name" required error={errors.name} wide>
            <input
              name="name"
              type="text"
              maxLength={80}
              autoComplete="off"
              defaultValue={product?.name ?? ""}
              className={INPUT}
            />
          </Field>

          <Field label="Category" required error={errors.category}>
            <input
              name="category"
              type="text"
              list="category-options"
              maxLength={40}
              autoComplete="off"
              defaultValue={product?.category ?? ""}
              className={INPUT}
            />
            <datalist id="category-options">
              {categories.map((category) => (
                <option key={category} value={category} />
              ))}
            </datalist>
          </Field>

          <Field label="Unit cost" required error={errors.price}>
            <input
              name="price"
              type="number"
              step="0.01"
              min="0"
              defaultValue={product?.price ?? ""}
              className={INPUT}
            />
          </Field>

          <Field label="Quantity on hand" required error={errors.stock}>
            <input
              name="stock"
              type="number"
              step="1"
              min="0"
              defaultValue={product?.stock ?? ""}
              className={INPUT}
            />
          </Field>

          <Field label="Quality rating (0–5)" required error={errors.rating}>
            <input
              name="rating"
              type="number"
              step="0.1"
              min="0"
              max="5"
              defaultValue={product?.rating ?? ""}
              className={INPUT}
            />
          </Field>

          <Field label="Tags (comma-separated)" wide>
            <input
              name="tags"
              type="text"
              placeholder="fragile, bulk, supplier-a"
              autoComplete="off"
              defaultValue={product?.tags.join(", ") ?? ""}
              className={INPUT}
            />
          </Field>

          {/*
            This is the state of the line, not of the shelf. Unticking it does
            not mean the item ran out - that is what a quantity of zero says -
            it means the line is out of service and its remaining units are not
            to be issued. The old label read as a restatement of the quantity.
          */}
          <div className="sm:col-span-2">
            <label className="flex items-center gap-2 text-sm">
              <input
                name="in_stock"
                type="checkbox"
                defaultChecked={product ? product.in_stock : true}
                className="h-4 w-4 accent-[var(--accent)]"
              />
              Line is in service
              <span className="text-xs text-[var(--ink-muted)]">
                untick to withdraw it, whatever the quantity on hand
              </span>
            </label>
          </div>

          {mode === "patch" && (
            <p className="rounded-lg bg-[var(--surface-sunken)] p-2.5 text-xs text-[var(--ink-secondary)] sm:col-span-2">
              <strong>Quick edit:</strong> only the fields you actually change are sent to the
              records service.
            </p>
          )}
        </div>

        <div className="flex justify-end gap-2 border-t p-4">
          <button
            type="button"
            onClick={onClose}
            className="h-9 rounded-lg border px-3 text-sm font-medium hover:bg-[var(--surface-sunken)]"
          >
            Cancel
          </button>
          <SubmitButton label={mode === "create" ? "Register item" : "Save changes"} />
        </div>
      </form>
    </dialog>
  );
}

function SubmitButton({ label }: { label: string }) {
  const { pending } = useFormStatus();

  return (
    <button
      type="submit"
      disabled={pending}
      className="h-9 rounded-lg bg-[var(--accent)] px-3 text-sm font-medium text-[var(--accent-ink)] transition hover:bg-[var(--accent-hover)] disabled:opacity-60"
    >
      {pending ? "Saving…" : label}
    </button>
  );
}

function Field({
  label,
  required,
  error,
  wide,
  children,
}: {
  label: string;
  required?: boolean;
  error?: string;
  wide?: boolean;
  children: React.ReactNode;
}) {
  return (
    <label className={`flex flex-col gap-1 ${wide ? "sm:col-span-2" : ""}`}>
      <span className="text-xs font-medium text-[var(--ink-secondary)]">
        {label}
        {required && (
          <span aria-hidden="true" className="ml-0.5 text-[var(--critical)]">
            *
          </span>
        )}
      </span>
      {children}
      {error && <span className="text-xs text-[var(--critical)]">{error}</span>}
    </label>
  );
}
