import { STOCK_BADGE, stockState } from "@/lib/stock";
import type { Product } from "@/lib/schemas";

const TONES = {
  good: "text-[var(--good)] bg-[var(--good-soft)]",
  warning: "text-[var(--warning)] bg-[var(--warning-soft)]",
  critical: "text-[var(--critical)] bg-[var(--critical-soft)]",
  neutral: "text-[var(--neutral)] bg-[var(--neutral-soft)]",
} as const;

/**
 * Status is shown with a glyph and a word alongside the colour, never colour
 * alone: green and red are the pair colour-blind readers are least able to
 * separate. The amber used for low stock is darkened for text, where the fill
 * colour would not clear 4.5:1 on a light surface.
 *
 * Four badges, not three. "Withdrawn" and "Out of stock" used to share this
 * one, which meant the register could tell them apart and the screen could not.
 */
export function StockBadge({ product }: { product: Product }) {
  const { tone, glyph, label } = STOCK_BADGE[stockState(product)];

  return (
    <span
      className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-medium whitespace-nowrap ${TONES[tone as keyof typeof TONES]}`}
    >
      <span aria-hidden="true">{glyph}</span>
      {label}
    </span>
  );
}
