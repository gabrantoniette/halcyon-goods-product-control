"use client";

import { useDialogs } from "./ui-context";
import type { Product } from "@/lib/schemas";

const LINK =
  "rounded px-1 py-0.5 text-xs font-medium text-[var(--accent)] transition hover:underline focus-visible:outline-2";

export function RowActions({ product }: { product: Product }) {
  const { openForm, openDelete } = useDialogs();

  return (
    <div className="flex items-center gap-2">
      <button type="button" className={LINK} onClick={() => openForm("replace", product)}>
        Edit
      </button>
      <button type="button" className={LINK} onClick={() => openForm("patch", product)}>
        Quick edit
      </button>
      <button
        type="button"
        className={`${LINK} !text-[var(--critical)]`}
        onClick={() => openDelete(product)}
      >
        Remove
      </button>
    </div>
  );
}
