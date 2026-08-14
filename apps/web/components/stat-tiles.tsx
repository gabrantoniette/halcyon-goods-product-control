import { LOW_STOCK_THRESHOLD, type Summary } from "@/lib/stock";

const money = new Intl.NumberFormat("en-US", { style: "currency", currency: "USD" });
const moneyCompact = new Intl.NumberFormat("en-US", {
  style: "currency",
  currency: "USD",
  notation: "compact",
  maximumFractionDigits: 1,
});

/**
 * Six headline numbers. Each is a single figure, so it is a stat tile rather
 * than a chart - a one-bar bar chart would say the same thing with more ink.
 */
export function StatTiles({ summary }: { summary: Summary }) {
  const { total, categories, counts, value, averageRating, ratedCount } = summary;

  return (
    <section
      aria-label="Stock summary"
      className="grid grid-cols-2 gap-3 sm:grid-cols-3 xl:grid-cols-6"
    >
      <Tile
        label="Items registered"
        value={total}
        foot={total ? `across ${categories} ${categories === 1 ? "category" : "categories"}` : " "}
      />
      <Tile
        label="Available"
        value={counts.in}
        foot={<Mark tone="good" glyph="✓" text="ready to issue" />}
      />
      <Tile
        label="Low stock"
        value={counts.low}
        foot={<Mark tone="warning" glyph="▲" text={`${LOW_STOCK_THRESHOLD} or fewer on hand`} />}
      />
      <Tile
        label="Out of stock"
        value={counts.out}
        foot={<Mark tone="critical" glyph="✕" text="unavailable" />}
      />
      <Tile
        label="Stock value"
        value={total ? moneyCompact.format(value) : "—"}
        title={total ? money.format(value) : undefined}
        foot="unit cost × quantity on hand"
      />
      <Tile
        label="Average quality rating"
        value={ratedCount ? averageRating.toFixed(1) : "—"}
        foot={ratedCount ? `based on ${ratedCount} rated items` : " "}
      />
    </section>
  );
}

function Tile({
  label,
  value,
  foot,
  title,
}: {
  label: string;
  value: React.ReactNode;
  foot: React.ReactNode;
  title?: string;
}) {
  return (
    <article className="rounded-xl border bg-[var(--surface-raised)] p-4 shadow-[var(--shadow-sm)]">
      <span className="block text-xs font-medium text-[var(--ink-muted)]">{label}</span>
      {/* Proportional figures: tabular digits read loose at display sizes. */}
      <span className="mt-1 block text-2xl font-semibold tracking-tight" title={title}>
        {value}
      </span>
      <span className="mt-1 block text-xs text-[var(--ink-muted)]">{foot}</span>
    </article>
  );
}

const TONES = {
  good: "text-[var(--good)]",
  warning: "text-[var(--warning)]",
  critical: "text-[var(--critical)]",
} as const;

function Mark({ tone, glyph, text }: { tone: keyof typeof TONES; glyph: string; text: string }) {
  return (
    <span className={`inline-flex items-center gap-1 ${TONES[tone]}`}>
      <span aria-hidden="true">{glyph}</span>
      {text}
    </span>
  );
}
