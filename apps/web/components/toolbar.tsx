"use client";

import { useDialogs } from "./ui-context";

export type Filters = {
  search: string;
  category: string;
  availability: string;
  /** Kept apart from `availability`: how old a figure is, not what it says. */
  staleOnly: boolean;
  sort: string;
};

export type View = "table" | "cards";

const FIELD =
  "h-9 rounded-lg border bg-[var(--surface-raised)] px-2.5 text-sm text-[var(--ink)] outline-none focus-visible:border-[var(--accent)]";

/**
 * One filter row above everything it scopes: the tiles, the chart and the list
 * all read the same slice, so a per-card filter would let them disagree.
 */
export function Toolbar({
  filters,
  onFilters,
  view,
  onView,
  categories,
}: {
  filters: Filters;
  onFilters: (next: Filters) => void;
  view: View;
  onView: (next: View) => void;
  categories: string[];
}) {
  const { openForm } = useDialogs();
  const set = (patch: Partial<Filters>) => onFilters({ ...filters, ...patch });

  return (
    <section aria-label="Filters and actions" className="flex flex-wrap items-end gap-3">
      <label className="flex min-w-[200px] flex-1 flex-col gap-1">
        <span className="text-xs text-[var(--ink-muted)]">Search</span>
        <input
          type="search"
          value={filters.search}
          onChange={(event) => set({ search: event.target.value })}
          placeholder="Search by item, category or tag…"
          aria-label="Search registered items"
          autoComplete="off"
          className={FIELD}
        />
      </label>

      <label className="flex flex-col gap-1">
        <span className="text-xs text-[var(--ink-muted)]">Category</span>
        <select
          value={filters.category}
          onChange={(event) => set({ category: event.target.value })}
          aria-label="Filter by category"
          className={FIELD}
        >
          <option value="all">All</option>
          {categories.map((category) => (
            <option key={category} value={category}>
              {category}
            </option>
          ))}
        </select>
      </label>

      <label className="flex flex-col gap-1">
        <span className="text-xs text-[var(--ink-muted)]">Stock status</span>
        <select
          value={filters.availability}
          onChange={(event) => set({ availability: event.target.value })}
          aria-label="Filter by stock status"
          className={FIELD}
        >
          <option value="all">All</option>
          <option value="in">Available</option>
          <option value="low">Low stock</option>
          <option value="out">Out of stock</option>
          <option value="withdrawn">Withdrawn</option>
        </select>
      </label>

      {/*
        Its own control rather than a fifth entry in the status list. Staleness
        is a different axis - a count can be stale in any of the four states -
        and putting the two on one select would force a choice between them,
        which is the collapse this whole distinction exists to undo.
      */}
      <label className="flex h-9 items-center gap-2 self-end text-sm">
        <input
          type="checkbox"
          checked={filters.staleOnly}
          onChange={(event) => set({ staleOnly: event.target.checked })}
          className="h-4 w-4 accent-[var(--accent)]"
        />
        Stale counts only
      </label>

      <label className="flex flex-col gap-1">
        <span className="text-xs text-[var(--ink-muted)]">Sort by</span>
        <select
          value={filters.sort}
          onChange={(event) => set({ sort: event.target.value })}
          aria-label="Sort items"
          className={FIELD}
        >
          <option value="name-asc">Item (A–Z)</option>
          <option value="name-desc">Item (Z–A)</option>
          <option value="stock-asc">Lowest quantity</option>
          <option value="stock-desc">Highest quantity</option>
          <option value="price-desc">Highest unit cost</option>
          <option value="price-asc">Lowest unit cost</option>
          <option value="rating-desc">Best rated</option>
        </select>
      </label>

      <div className="ml-auto flex items-center gap-2">
        <div role="group" aria-label="Display mode" className="flex h-9 rounded-lg border p-0.5">
          <ViewButton active={view === "cards"} onClick={() => onView("cards")}>
            Cards
          </ViewButton>
          <ViewButton active={view === "table"} onClick={() => onView("table")}>
            Table
          </ViewButton>
        </div>

        <button
          type="button"
          onClick={() => openForm("create")}
          className="flex h-9 items-center gap-1.5 rounded-lg bg-[var(--accent)] px-3 text-sm font-medium text-[var(--accent-ink)] transition hover:bg-[var(--accent-hover)]"
        >
          <span aria-hidden="true">+</span>
          Register item
        </button>
      </div>
    </section>
  );
}

function ViewButton({
  active,
  onClick,
  children,
}: {
  active: boolean;
  onClick: () => void;
  children: React.ReactNode;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      aria-pressed={active}
      className={`rounded-md px-3 text-sm font-medium transition ${
        active
          ? "bg-[var(--accent-soft)] text-[var(--accent)]"
          : "text-[var(--ink-secondary)] hover:text-[var(--ink)]"
      }`}
    >
      {children}
    </button>
  );
}
