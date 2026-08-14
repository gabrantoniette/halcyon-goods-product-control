"use client";

import { useCallback, useMemo, useState } from "react";

import { CategoryChart } from "./category-chart";
import { ConfirmDialog } from "./confirm-dialog";
import { ProductDialog } from "./product-dialog";
import { ProductsCards } from "./products-cards";
import { ProductsTable } from "./products-table";
import { StatTiles } from "./stat-tiles";
import { ToastProvider } from "./toasts";
import { Toolbar, type Filters, type View } from "./toolbar";
import { DialogContext, type Dialogs, type FormMode } from "./ui-context";
import type { Product } from "@/lib/schemas";
import { stockState, summarise } from "@/lib/stock";

const INITIAL_FILTERS: Filters = {
  search: "",
  category: "all",
  availability: "all",
  sort: "name-asc",
};

/**
 * The interactive shell. The register arrives as a prop from the server, so
 * this owns only what the server cannot know: the filters, the chosen view and
 * which dialog is open.
 */
export function Dashboard({ products }: { products: Product[] }) {
  const [filters, setFilters] = useState<Filters>(INITIAL_FILTERS);
  // An internal control tool is read as a register, so the table leads and the
  // card grid is the alternative - the opposite of a storefront.
  const [view, setView] = useState<View>("table");

  const [form, setForm] = useState<{ mode: FormMode; product: Product | null } | null>(null);
  const [deleting, setDeleting] = useState<Product | null>(null);

  const dialogs = useMemo<Dialogs>(
    () => ({
      openForm: (mode, product) => setForm({ mode, product: product ?? null }),
      openDelete: (product) => setDeleting(product),
    }),
    [],
  );

  const closeForm = useCallback(() => setForm(null), []);
  const closeDelete = useCallback(() => setDeleting(null), []);

  const categories = useMemo(
    () => [...new Set(products.map((product) => product.category))].sort(),
    [products],
  );

  // The tiles and the chart describe the whole register; only the list below
  // is narrowed, so a filter never makes the headline numbers lie.
  const summary = useMemo(() => summarise(products), [products]);
  const visible = useMemo(() => applyFilters(products, filters), [products, filters]);

  return (
    <ToastProvider>
      <DialogContext value={dialogs}>
        <div className="flex flex-col gap-6">
          <StatTiles summary={summary} />
          <CategoryChart products={products} />

          <Toolbar
            filters={filters}
            onFilters={setFilters}
            view={view}
            onView={setView}
            categories={categories}
          />

          <div className="flex flex-col gap-3">
            {products.length > 0 && (
              <p aria-live="polite" className="text-xs text-[var(--ink-muted)]">
                Showing {visible.length} of {products.length} registered items
              </p>
            )}

            {visible.length === 0 ? (
              <EmptyState registerIsEmpty={products.length === 0} />
            ) : view === "table" ? (
              <ProductsTable products={visible} />
            ) : (
              <ProductsCards products={visible} />
            )}
          </div>
        </div>

        <ProductDialog
          open={form !== null}
          mode={form?.mode ?? "create"}
          product={form?.product ?? null}
          categories={categories}
          onClose={closeForm}
        />

        <ConfirmDialog open={deleting !== null} product={deleting} onClose={closeDelete} />
      </DialogContext>
    </ToastProvider>
  );
}

function applyFilters(products: Product[], filters: Filters): Product[] {
  const term = filters.search.trim().toLowerCase();

  const matching = products.filter((product) => {
    if (filters.category !== "all" && product.category !== filters.category) return false;
    if (filters.availability !== "all" && stockState(product) !== filters.availability) return false;
    if (!term) return true;

    const haystack = [product.name, product.category, ...product.tags].join(" ").toLowerCase();
    return haystack.includes(term);
  });

  const [key, direction] = filters.sort.split("-");
  const sign = direction === "asc" ? 1 : -1;

  return matching.slice().sort((a, b) => {
    if (key === "name") return sign * a.name.localeCompare(b.name);
    const left = Number(a[key as "price" | "stock" | "rating"] ?? 0);
    const right = Number(b[key as "price" | "stock" | "rating"] ?? 0);
    return sign * (left - right);
  });
}

function EmptyState({ registerIsEmpty }: { registerIsEmpty: boolean }) {
  return (
    <div className="flex flex-col items-center gap-2 rounded-xl border border-dashed bg-[var(--surface-raised)] px-6 py-14 text-center">
      <svg
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.2"
        strokeLinecap="round"
        strokeLinejoin="round"
        className="h-10 w-10 text-[var(--ink-muted)]"
        aria-hidden="true"
      >
        <path d="M3 21V9l9-5 9 5v12" />
        <path d="M9 21v-6h6v6" />
        <path d="M3 21h18" />
      </svg>
      <h3 className="text-sm font-semibold">
        {registerIsEmpty ? "No items registered" : "No items found"}
      </h3>
      <p className="text-xs text-[var(--ink-muted)]">
        {registerIsEmpty
          ? "Register the first item to start controlling stock."
          : "Try adjusting your search or filters."}
      </p>
    </div>
  );
}
