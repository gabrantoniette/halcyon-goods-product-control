import { z } from "zod";

/**
 * The shapes the API speaks, mirrored from the Pydantic models in
 * apps/api/src/halcyon_api/schemas.py. Parsing rather than casting is what
 * stops a change on the API side from surfacing as `undefined` three
 * components deep.
 */

export const productSchema = z.object({
  name: z.string(),
  category: z.string(),
  price: z.number(),
  stock: z.number().int(),
  in_stock: z.boolean(),
  rating: z.number(),
  tags: z.array(z.string()),
  uuid: z.string(),
  created_at: z.string(),
  updated_at: z.string(),
  // Nullable by design: null means nobody has established the quantity, which
  // is a different claim from "established a long time ago" and is not the same
  // as `updated_at`, which moves for any edit at all.
  stock_counted_at: z.string().nullable(),
});

export type Product = z.infer<typeof productSchema>;

export const productListSchema = z.array(productSchema);

/** The API's error body: FastAPI puts the reason in `detail`. */
export const apiErrorSchema = z.object({
  detail: z.union([z.string(), z.array(z.unknown())]).optional(),
});

/**
 * What the register form submits. The bounds match the constraints the API
 * enforces, so an invalid value is caught before a round trip rather than
 * coming back as a 422 the user has to decode.
 */
export const productFormSchema = z.object({
  name: z.string().trim().min(1, "Item name is required.").max(80),
  category: z.string().trim().min(1, "Category is required.").max(40),
  price: z.coerce.number("Enter a price of 0 or more.").min(0, "Enter a price of 0 or more."),
  stock: z.coerce
    .number("Enter a whole quantity of 0 or more.")
    .int("Enter a whole quantity of 0 or more.")
    .min(0, "Enter a whole quantity of 0 or more."),
  rating: z.coerce
    .number("Enter a rating between 0 and 5.")
    .min(0, "Enter a rating between 0 and 5.")
    .max(5, "Enter a rating between 0 and 5."),
  in_stock: z.boolean(),
  tags: z.array(z.string()),
});

export type ProductForm = z.infer<typeof productFormSchema>;

/** The result every Server Action returns, so the UI has one shape to render. */
export type ActionResult = {
  ok: boolean;
  message: string;
  /** Per-field messages, keyed by form field name. */
  fieldErrors?: Partial<Record<keyof ProductForm, string>>;
};
