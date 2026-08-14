"use client";

import { useState } from "react";

import type { Product } from "@/lib/schemas";

/**
 * Items per category — horizontal bars, sorted by count.
 *
 * One hue for every bar: the categories are nominal, so shading them by size
 * would double-encode the length as colour and burn the only free channel on
 * information the bar already carries. Each bar is directly labelled with its
 * count, which is why there are no gridlines; the tooltip adds the share of
 * the register rather than being the only way to read a value.
 */
export function CategoryChart({ products }: { products: Product[] }) {
  const [hovered, setHovered] = useState<string | null>(null);

  const counts = new Map<string, number>();
  for (const product of products) {
    counts.set(product.category, (counts.get(product.category) ?? 0) + 1);
  }

  const rows = [...counts.entries()].sort((a, b) => b[1] - a[1]);
  const max = rows.length ? Math.max(...rows.map(([, count]) => count)) : 0;
  const total = products.length;

  return (
    <section
      aria-labelledby="chart-title"
      className="rounded-xl border bg-[var(--surface-raised)] p-4 shadow-[var(--shadow-sm)] sm:p-5"
    >
      <h2 id="chart-title" className="text-sm font-semibold">
        Items per category
      </h2>
      <p className="mt-0.5 text-xs text-[var(--ink-muted)]">
        How the registered items are distributed across the warehouse categories.
      </p>

      {rows.length === 0 ? (
        <p className="py-8 text-center text-sm text-[var(--ink-muted)]">No records to plot yet.</p>
      ) : (
        // gap-0.5 is the 2px surface gap that separates adjacent bars without
        // drawing a border around them.
        <ul className="mt-4 flex flex-col gap-0.5">
          {rows.map(([category, count]) => {
            const share = Math.round((count / total) * 100);
            const active = hovered === category;

            return (
              <li
                key={category}
                // The row is the hit target, not the bar: a 6px bar would be a
                // pinpoint target.
                className="group grid min-h-[24px] grid-cols-[minmax(80px,140px)_1fr_auto] items-center gap-3 rounded px-1 py-1"
                onMouseEnter={() => setHovered(category)}
                onMouseLeave={() => setHovered(null)}
                onFocus={() => setHovered(category)}
                onBlur={() => setHovered(null)}
                tabIndex={0}
                title={`${category}: ${count} ${count === 1 ? "item" : "items"} (${share}% of the register)`}
              >
                <span className="truncate text-xs text-[var(--ink-secondary)]">{category}</span>

                <span className="h-2 w-full overflow-hidden rounded-full bg-[var(--surface-sunken)]">
                  <span
                    className="block h-full rounded-full transition-[width,opacity] duration-300"
                    style={{
                      width: `${(count / max) * 100}%`,
                      background: "var(--series)",
                      opacity: active ? 1 : 0.85,
                    }}
                  />
                </span>

                <span className="tnum w-8 text-right text-xs font-medium text-[var(--ink-secondary)]">
                  {count}
                </span>
              </li>
            );
          })}
        </ul>
      )}
    </section>
  );
}
