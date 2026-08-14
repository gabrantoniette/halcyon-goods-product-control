import { StockBadge } from "./stock-badge";
import { RowActions } from "./row-actions";
import type { Product } from "@/lib/schemas";

const money = new Intl.NumberFormat("en-US", { style: "currency", currency: "USD" });

/**
 * The default view. An internal control tool is read as a register, so the
 * table leads and the card grid is the alternative - the opposite of a
 * storefront. It doubles as the chart's table view.
 */
export function ProductsTable({ products }: { products: Product[] }) {
  return (
    <div className="overflow-x-auto rounded-xl border bg-[var(--surface-raised)] shadow-[var(--shadow-sm)]">
      <table className="w-full min-w-[720px] border-collapse text-sm">
        <caption className="visually-hidden">
          Registered items with category, unit cost, quantity on hand and stock status
        </caption>
        <thead>
          <tr className="border-b text-left text-xs text-[var(--ink-muted)]">
            <th scope="col" className="px-4 py-2.5 font-medium">Item</th>
            <th scope="col" className="px-4 py-2.5 font-medium">Category</th>
            <th scope="col" className="px-4 py-2.5 text-right font-medium">Unit cost</th>
            <th scope="col" className="px-4 py-2.5 text-right font-medium">On hand</th>
            <th scope="col" className="px-4 py-2.5 font-medium">Stock status</th>
            <th scope="col" className="px-4 py-2.5 text-right font-medium">Rating</th>
            <th scope="col" className="px-4 py-2.5">
              <span className="visually-hidden">Actions</span>
            </th>
          </tr>
        </thead>
        <tbody>
          {products.map((product) => (
            <tr key={product.uuid} className="border-b last:border-0 hover:bg-[var(--surface-sunken)]">
              <td className="px-4 py-2.5 font-medium">{product.name}</td>
              <td className="px-4 py-2.5 text-[var(--ink-secondary)]">{product.category}</td>
              <td className="tnum px-4 py-2.5 text-right">{money.format(product.price || 0)}</td>
              <td className="tnum px-4 py-2.5 text-right">{product.stock}</td>
              <td className="px-4 py-2.5">
                <StockBadge product={product} />
              </td>
              <td className="tnum px-4 py-2.5 text-right">{(product.rating ?? 0).toFixed(1)}</td>
              <td className="px-4 py-2.5">
                <RowActions product={product} />
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
