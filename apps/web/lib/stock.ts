import type { Product } from "./schemas";

/**
 * At or below this quantity an item is flagged for restocking. It is a
 * warehouse rule, not an API field, so it is derived here from `stock`.
 */
export const LOW_STOCK_THRESHOLD = 10;

/**
 * Beyond this many days since the quantity was last established, the figure is
 * shown as stale. Also a warehouse rule rather than an API field.
 */
export const STALE_COUNT_DAYS = 30;

export type StockState = "in" | "low" | "out" | "withdrawn";

/**
 * Four states, derived in one place so the tiles, the filter and the badges can
 * never disagree.
 *
 * Withdrawn and out of stock are kept apart because they are not the same
 * event and do not route to the same person: an empty shelf on a line still in
 * service is a supply problem for purchasing, while a withdrawn line is a
 * decision that has already been taken and is not a signal to buy anything.
 * Merging them — which is what `!in_stock || stock === 0` did — put both under
 * one red badge and made the register unable to say which it was looking at.
 *
 * `in_stock` is checked first because it describes the line rather than the
 * shelf: a withdrawn line is withdrawn whether or not units remain, and the 40
 * units behind it are stock that exists and must not be issued.
 */
export function stockState(product: Product): StockState {
  const onHand = Number(product.stock) || 0;
  if (!product.in_stock) return "withdrawn";
  if (onHand === 0) return "out";
  if (onHand <= LOW_STOCK_THRESHOLD) return "low";
  return "in";
}

/**
 * Colour is never the only carrier: each state also has a glyph and a word.
 * Green and red are the pair colour-blind readers are least able to separate.
 *
 * Withdrawn is deliberately the only muted one. It is a settled decision rather
 * than an open problem, so putting it in an alarm colour next to the states
 * that need acting on would cost the other three their urgency.
 */
export const STOCK_BADGE: Record<StockState, { tone: string; glyph: string; label: string }> = {
  in: { tone: "good", glyph: "✓", label: "Available" },
  low: { tone: "warning", glyph: "▲", label: "Low stock" },
  out: { tone: "critical", glyph: "✕", label: "Out of stock" },
  withdrawn: { tone: "neutral", glyph: "⊘", label: "Withdrawn" },
};

/**
 * How old the quantity is, in whole days, or null when nobody has established
 * it at all. Never is treated as stale: an undated figure is not a fresh one.
 *
 * This is a separate axis from `stockState`, and stays separate everywhere. A
 * count can be stale in any of the four states, and how confident you are in a
 * number is not the same question as what the number says.
 */
export type CountAge = { days: number | null; stale: boolean };

export function countAge(product: Product, now: number = Date.now()): CountAge {
  if (!product.stock_counted_at) return { days: null, stale: true };

  const counted = Date.parse(product.stock_counted_at);
  if (Number.isNaN(counted)) return { days: null, stale: true };

  const days = Math.max(0, Math.floor((now - counted) / 86_400_000));
  return { days, stale: days > STALE_COUNT_DAYS };
}

/** "today" / "12d ago" / "never counted", for a column that has to stay narrow. */
export function countAgeLabel({ days }: CountAge): string {
  if (days === null) return "never counted";
  if (days === 0) return "today";
  return `${days}d ago`;
}

export type Summary = {
  total: number;
  categories: number;
  counts: Record<StockState, number>;
  value: number;
  /** Of `value`, the part sitting on withdrawn lines: on hand, but not issuable. */
  idleValue: number;
  staleCounts: number;
  averageRating: number;
  ratedCount: number;
};

/** Everything the KPI row shows, computed over the whole register. */
export function summarise(products: Product[], now: number = Date.now()): Summary {
  const counts: Record<StockState, number> = { in: 0, low: 0, out: 0, withdrawn: 0 };
  let value = 0;
  let idleValue = 0;
  let staleCounts = 0;

  for (const product of products) {
    const state = stockState(product);
    counts[state] += 1;

    const onShelf = (product.price || 0) * (product.stock || 0);
    value += onShelf;
    if (state === "withdrawn") idleValue += onShelf;

    if (countAge(product, now).stale) staleCounts += 1;
  }

  const rated = products.filter((product) => typeof product.rating === "number");
  const averageRating = rated.length
    ? rated.reduce((sum, product) => sum + product.rating, 0) / rated.length
    : 0;

  return {
    total: products.length,
    categories: new Set(products.map((product) => product.category)).size,
    counts,
    value,
    idleValue,
    staleCounts,
    averageRating,
    ratedCount: rated.length,
  };
}
