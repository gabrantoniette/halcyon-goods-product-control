import { ThemeToggle } from "./theme-toggle";
import { RefreshButton } from "./refresh-button";

export function TopBar({ online }: { online: boolean }) {
  return (
    <header className="sticky top-0 z-30 border-b bg-[var(--surface-raised)]/85 backdrop-blur">
      <div className="mx-auto flex max-w-[1400px] items-center justify-between gap-4 px-4 py-3 sm:px-6 lg:px-8">
        <div className="flex items-center gap-3">
          <span className="flex h-9 w-9 items-center justify-center rounded-lg bg-[var(--accent-soft)] text-[var(--accent)]">
            <svg
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="1.8"
              strokeLinecap="round"
              strokeLinejoin="round"
              className="h-5 w-5"
              aria-hidden="true"
            >
              <path d="M3 21V9l9-5 9 5v12" />
              <path d="M9 21v-6h6v6" />
              <path d="M3 21h18" />
            </svg>
          </span>
          <span className="flex flex-col leading-tight">
            <strong className="text-sm font-semibold">Halcyon Goods</strong>
            <small className="text-xs text-[var(--ink-muted)]">Internal product control</small>
          </span>
        </div>

        <div className="flex items-center gap-2">
          <span
            className="hidden rounded-md border px-2 py-1 text-[11px] font-medium tracking-wide text-[var(--ink-muted)] uppercase sm:inline"
            title="Internal system — company use only"
          >
            Internal
          </span>

          <StatusPill online={online} />
          <RefreshButton />
          <ThemeToggle />
        </div>
      </div>
    </header>
  );
}

/** State is carried by a word and a glyph, not by the colour alone. */
function StatusPill({ online }: { online: boolean }) {
  const tone = online
    ? "text-[var(--good)] bg-[var(--good-soft)]"
    : "text-[var(--critical)] bg-[var(--critical-soft)]";

  return (
    <span
      role="status"
      className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-medium ${tone}`}
    >
      <span aria-hidden="true">{online ? "●" : "▲"}</span>
      {online ? "API online" : "API offline"}
    </span>
  );
}
