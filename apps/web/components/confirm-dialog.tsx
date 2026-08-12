"use client";

import { useEffect, useRef, useState } from "react";

import { removeProduct } from "@/app/actions";
import type { Product } from "@/lib/schemas";
import { useToasts } from "./ui-context";

export function ConfirmDialog({
  open,
  product,
  onClose,
}: {
  open: boolean;
  product: Product | null;
  onClose: () => void;
}) {
  const dialogRef = useRef<HTMLDialogElement>(null);
  const [pending, setPending] = useState(false);
  const { push } = useToasts();

  useEffect(() => {
    const dialog = dialogRef.current;
    if (!dialog) return;
    if (open && !dialog.open) dialog.showModal();
    if (!open && dialog.open) dialog.close();
  }, [open]);

  async function confirm() {
    if (!product) return;

    setPending(true);
    const result = await removeProduct(product.name);
    setPending(false);

    if (result.ok) push("success", result.message);
    else push("error", "Request failed", result.message);

    onClose();
  }

  return (
    <dialog
      ref={dialogRef}
      onClose={onClose}
      onCancel={onClose}
      className="m-auto w-[min(26rem,calc(100vw-2rem))] rounded-2xl border bg-[var(--surface-raised)] p-0 shadow-[var(--shadow-md)] backdrop:bg-black/50"
    >
      <div className="border-b p-4">
        <h2 className="text-base font-semibold">Remove item</h2>
      </div>

      <div className="p-4 text-sm text-[var(--ink-secondary)]">
        {product && (
          <p>
            <strong className="text-[var(--ink)]">&ldquo;{product.name}&rdquo;</strong> will be
            permanently removed from the internal register.
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
        <button
          type="button"
          onClick={confirm}
          disabled={pending}
          className="h-9 rounded-lg bg-[var(--critical)] px-3 text-sm font-medium text-white transition hover:opacity-90 disabled:opacity-60"
        >
          {pending ? "Removing…" : "Remove"}
        </button>
      </div>
    </dialog>
  );
}
