import { countAge, countAgeLabel, STALE_COUNT_DAYS } from "@/lib/stock";
import type { Product } from "@/lib/schemas";

/**
 * Fixed locale and time zone, so the tooltip renders the same string on the
 * server and in the browser. `toLocaleString()` with the ambient locale would
 * differ between the two and mismatch on hydration.
 */
const stamp = new Intl.DateTimeFormat("en-US", {
  dateStyle: "medium",
  timeStyle: "short",
  timeZone: "UTC",
});

/**
 * How old the quantity is, next to the quantity itself.
 *
 * A number with no date on it invites the reader to trust it, and that trust is
 * what a stale figure quietly spends. `updated_at` cannot carry this: it moves
 * when someone corrects a price, so it would report a six-week-old count as
 * fresh. Only a change to the quantity moves `stock_counted_at`.
 */
export function CountAge({ product }: { product: Product }) {
  const age = countAge(product);
  const counted = product.stock_counted_at;

  return (
    <span
      // The label is derived from the current time, so a render that lands
      // either side of a midnight boundary can disagree with the one the server
      // sent milliseconds earlier. The next render settles it.
      suppressHydrationWarning
      title={counted ? `Quantity last established ${stamp.format(new Date(counted))} UTC` : undefined}
      className={`inline-flex items-center gap-1 whitespace-nowrap ${
        age.stale ? "text-[var(--warning)]" : "text-[var(--ink-muted)]"
      }`}
    >
      {age.stale && (
        <>
          <span aria-hidden="true">◷</span>
          <span className="visually-hidden">
            Stale: unconfirmed for more than {STALE_COUNT_DAYS} days.
          </span>
        </>
      )}
      {countAgeLabel(age)}
    </span>
  );
}
