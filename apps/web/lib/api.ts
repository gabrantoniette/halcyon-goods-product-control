import "server-only";

import { apiErrorSchema, productListSchema, type Product } from "./schemas";

/**
 * The only place that talks to the records API.
 *
 * `server-only` makes importing this from a Client Component a build error,
 * which is what guarantees HALCYON_API_KEY never reaches the browser: the key
 * is read here, on the server, and the browser only ever calls Server Actions.
 * It is also why no CORS configuration is needed - the API sees requests from
 * this server, never from a page.
 */

const BASE_URL = (process.env.HALCYON_API_BASE_URL ?? "http://127.0.0.1:8000").replace(/\/+$/, "");
const API_KEY = process.env.HALCYON_API_KEY || null;

const TIMEOUT_MS = 5000;

export class ApiError extends Error {
  constructor(
    message: string,
    readonly status: number | null,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

function writeHeaders(): HeadersInit {
  return {
    "Content-Type": "application/json",
    ...(API_KEY ? { "X-API-Key": API_KEY } : {}),
  };
}

/** Turn an error response into the message the UI shows. */
async function readError(response: Response): Promise<string> {
  const body = await response.json().catch(() => null);
  const parsed = apiErrorSchema.safeParse(body);
  const detail = parsed.success ? parsed.data.detail : undefined;

  if (typeof detail === "string") return detail;
  // A 422 from FastAPI's own validation carries a list, not a string.
  if (Array.isArray(detail)) return "The records service rejected the submitted values.";
  return `The records service answered ${response.status}.`;
}

async function request(path: string, init: RequestInit = {}): Promise<Response> {
  try {
    return await fetch(`${BASE_URL}${path}`, {
      ...init,
      signal: AbortSignal.timeout(TIMEOUT_MS),
      // The register changes through this app, so a cached read would show
      // the user their own edit not having happened.
      cache: "no-store",
    });
  } catch (error) {
    const reason = error instanceof Error ? error.message : "unknown error";
    throw new ApiError(`Could not reach the records service at ${BASE_URL}: ${reason}`, null);
  }
}

const PAGE_SIZE = 200;

/**
 * Every product, walked page by page.
 *
 * The API answers in pages, but the dashboard's totals, chart and filters are
 * all computed over the whole register, so the paging is resolved here instead
 * of leaking into every component.
 */
export async function listProducts(): Promise<Product[]> {
  const products: Product[] = [];
  let page = 1;
  let totalPages = 1;

  do {
    const response = await request(`/products?page=${page}&page_size=${PAGE_SIZE}`);
    if (!response.ok) throw new ApiError(await readError(response), response.status);

    const parsed = productListSchema.safeParse(await response.json());
    if (!parsed.success) throw new ApiError("The records service returned an unexpected shape.", null);

    products.push(...parsed.data);

    // A failed page would abort the walk: half the register reported as all of
    // it would make every total on the dashboard wrong.
    totalPages = Number(response.headers.get("X-Total-Pages") ?? 1) || 1;
    page += 1;
  } while (page <= totalPages);

  return products;
}

export async function health(): Promise<{ reachable: boolean; detail: string | null }> {
  try {
    const response = await request("/health");
    return { reachable: response.ok, detail: response.ok ? null : await readError(response) };
  } catch (error) {
    return { reachable: false, detail: error instanceof Error ? error.message : "unknown error" };
  }
}

/** The address the API is reached at, for the footer. Never includes the key. */
export function apiBaseUrl(): string {
  return BASE_URL;
}

async function write(method: string, name: string, body?: unknown): Promise<void> {
  const response = await request(`/products/${encodeURIComponent(name)}`, {
    method,
    headers: writeHeaders(),
    ...(body === undefined ? {} : { body: JSON.stringify(body) }),
  });

  if (!response.ok) throw new ApiError(await readError(response), response.status);
}

export const createProduct = (name: string, body: unknown) => write("POST", name, body);
export const replaceProduct = (name: string, body: unknown) => write("PUT", name, body);
export const patchProduct = (name: string, body: unknown) => write("PATCH", name, body);
export const deleteProduct = (name: string) => write("DELETE", name);
