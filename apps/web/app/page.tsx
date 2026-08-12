import { Dashboard } from "@/components/dashboard";
import { OfflineBanner } from "@/components/offline-banner";
import { TopBar } from "@/components/top-bar";
import { ApiError, apiBaseUrl, listProducts } from "@/lib/api";
import type { Product } from "@/lib/schemas";

/**
 * The register is read here, on the server, and handed to the dashboard as
 * plain data. The browser never talks to the records API directly - which is
 * what keeps the API key server-side and makes CORS configuration unnecessary.
 */
export default async function Page() {
  let products: Product[] = [];
  let failure: string | null = null;

  try {
    products = await listProducts();
  } catch (error) {
    failure = error instanceof ApiError ? error.message : "The records service is unreachable.";
  }

  return (
    <div className="flex min-h-screen flex-col">
      <TopBar online={failure === null} />

      <main className="mx-auto w-full max-w-[1400px] flex-1 px-4 py-6 sm:px-6 lg:px-8">
        {failure && <OfflineBanner detail={failure} />}

        <section className="mb-6">
          <h1 className="text-2xl font-semibold tracking-tight">Stock overview</h1>
          <p className="mt-1 max-w-3xl text-sm text-[var(--ink-secondary)]">
            Company-wide record of every item held in the warehouse — what is on hand, what is
            running low and what needs restocking.
          </p>
        </section>

        <Dashboard products={products} />
      </main>

      <footer className="mt-8 border-t px-4 py-4 text-xs text-[var(--ink-muted)] sm:px-6 lg:px-8">
        <div className="mx-auto flex max-w-[1400px] flex-wrap items-center justify-between gap-2">
          <span>
            Internal system — company use only. Records are held by the product control API.
          </span>
          <span className="font-[family-name:var(--font-mono)]">{apiBaseUrl()}</span>
        </div>
      </footer>
    </div>
  );
}
