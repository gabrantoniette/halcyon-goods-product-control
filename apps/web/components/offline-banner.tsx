"use client";

import { useRouter } from "next/navigation";
import { useTransition } from "react";

export function OfflineBanner({ detail }: { detail: string }) {
  const router = useRouter();
  const [pending, startTransition] = useTransition();

  return (
    <div
      role="alert"
      className="mb-6 flex flex-wrap items-center gap-3 rounded-xl border border-[var(--critical)] bg-[var(--critical-soft)] p-4"
    >
      <span
        aria-hidden="true"
        className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-[var(--critical)] text-sm font-bold text-white"
      >
        !
      </span>
      <div className="min-w-0 flex-1">
        <strong className="block text-sm">Could not reach the records service.</strong>
        <span className="block text-xs break-words text-[var(--ink-secondary)]">{detail}</span>
      </div>
      <button
        type="button"
        onClick={() => startTransition(() => router.refresh())}
        disabled={pending}
        className="rounded-lg border border-[var(--critical)] px-3 py-1.5 text-sm font-medium transition hover:bg-[var(--surface-raised)] disabled:opacity-60"
      >
        {pending ? "Retrying…" : "Try again"}
      </button>
    </div>
  );
}
