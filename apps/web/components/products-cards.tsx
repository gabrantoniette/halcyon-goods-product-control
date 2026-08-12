import { StockBadge } from "./stock-badge";
import { RowActions } from "./row-actions";
import type { Product } from "@/lib/schemas";

const money = new Intl.NumberFormat("en-US", { style: "currency", currency: "USD" });

export function ProductsCards({ products }: { products: Product[] }) {
  return (
    <section
      aria-label="Registered items"
      className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4"
    >
      {products.map((product) => (
        <article
          key={product.uuid}
          className="flex flex-col gap-2 rounded-xl border bg-[var(--surface-raised)] p-4 shadow-[var(--shadow-sm)]"
        >
          <div className="flex items-start justify-between gap-2">
            <h3 className="text-sm font-semibold">{product.name}</h3>
            <span className="shrink-0 rounded-md bg-[var(--surface-sunken)] px-2 py-0.5 text-xs text-[var(--ink-secondary)]">
              {product.category}
            </span>
          </div>

          <span className="text-lg font-semibold">
            {money.format(product.price || 0)}{" "}
            <small className="text-xs font-normal text-[var(--ink-muted)]">per unit</small>
          </span>

          <div className="flex flex-wrap items-center gap-2 text-xs text-[var(--ink-secondary)]">
            <StockBadge product={product} />
            <span className="tnum">{product.stock} on hand</span>
            <span className="tnum inline-flex items-center gap-1">
              <span aria-hidden="true" className="text-[var(--warning)]">
                ★
              </span>
              {(product.rating ?? 0).toFixed(1)}
            </span>
          </div>

          {product.tags.length > 0 && (
            <div className="flex flex-wrap gap-1">
              {product.tags.map((tag) => (
                <span
                  key={tag}
                  className="rounded border px-1.5 py-0.5 text-[11px] text-[var(--ink-muted)]"
                >
                  {tag}
                </span>
              ))}
            </div>
          )}

          <div className="mt-auto pt-1">
            <RowActions product={product} />
          </div>
        </article>
      ))}
    </section>
  );
}
