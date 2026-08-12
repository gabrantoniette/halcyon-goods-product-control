import type { Product } from "./schemas";

/**
 * At or below this quantity an item is flagged for restocking. It is a
 * warehouse rule, not an API field, so it is derived here from `stock`.
 */
export const LOW_STOCK_THRESHOLD = 10;

export type StockState = "in" | "low" | "out";

/**
 * Three states, derived in one place so the tiles, the filter and the badges
 * can never disagree about what "low stock" means.
 */
export function stockState(product: Product): StockState {
  const onHand = Number(product.stock) || 0;
  if (!product.in_stock || onHand === 0) return "out";
  if (onHand <= LOW_STOCK_THRESHOLD) return "low";
  return "in";
}

/**
 * Colour is never the only carrier: each state also has a glyph and a word.
 * Green and red are the pair colour-blind readers are least able to separate.
 */
export const STOCK_BADGE: Record<StockState, { tone: string; glyph: string; label: string }> = {
  in: { tone: "good", glyph: "✓", label: "Available" },
  low: { tone: "warning", glyph: "▲", label: "Low stock" },
  out: { tone: "critical", glyph: "✕", label: "Out of stock" },
};

export type Summary = {
  total: number;
  categories: number;
  counts: Record<StockState, number>;
  value: number;
  averageRating: number;
  ratedCount: number;
};

/** Everything the KPI row shows, computed over the whole register. */
export function summarise(products: Product[]): Summary {
  const counts: Record<StockState, number> = { in: 0, low: 0, out: 0 };
  for (const product of products) counts[stockState(product)] += 1;

  const value = products.reduce((sum, product) => sum + (product.price || 0) * (product.stock || 0), 0);
  const rated = products.filter((product) => typeof product.rating === "number");
  const averageRating = rated.length
    ? rated.reduce((sum, product) => sum + product.rating, 0) / rated.length
    : 0;

  return {
    total: products.length,
    categories: new Set(products.map((product) => product.category)).size,
    counts,
    value,
    averageRating,
    ratedCount: rated.length,
  };
}
