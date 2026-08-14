"use client";

import { useRouter } from "next/navigation";
import { useTransition } from "react";

/**
 * Re-runs the Server Component that reads the register. The pending state is
 * what the list uses to dim itself, so a refetch holds the previous render at
 * reduced opacity instead of flashing a skeleton.
 */
export function RefreshButton() {
  const router = useRouter();
  const [pending, startTransition] = useTransition();

  return (
    <button
      type="button"
      onClick={() => startTransition(() => router.refresh())}
      title="Reload records"
      aria-label="Reload records"
      className="flex h-9 w-9 items-center justify-center rounded-lg border text-[var(--ink-secondary)] transition hover:bg-[var(--surface-sunken)] hover:text-[var(--ink)] disabled:opacity-60"
      disabled={pending}
    >
      <svg
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
        className={`h-4 w-4 ${pending ? "animate-spin" : ""}`}
        aria-hidden="true"
      >
        <path d="M21 12a9 9 0 1 1-3-6.7" />
        <path d="M21 3v6h-6" />
      </svg>
    </button>
  );
}
