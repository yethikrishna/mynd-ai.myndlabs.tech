"use client";

import { usePathname } from "next/navigation";

// Reserved first-path-segments that are not products (mirror of the backend
// RESERVED_PREFIXES in mynd.routing.product_router).
const RESERVED = new Set([
  "api",
  "auth",
  "oauth",
  "health",
  "static",
  "_next",
  "assets",
  "admin",
  "app",
  "chat",
  "connector",
  "config",
  "craft",
  "ee",
  "federated",
  "mcp",
  "nrf",
]);

/** Derive the active product slug from the URL's first path segment.
 *
 * In a standalone (single-product) deployment, NEXT_PUBLIC_MYND_PRODUCT pins
 * the whole app to one product, so the slug is resolved regardless of path.
 */
export function useProductSlug(): string | null {
  const pinned = process.env.NEXT_PUBLIC_MYND_PRODUCT;
  if (pinned) return pinned.toLowerCase();

  const pathname = usePathname() ?? "";
  const first = pathname.split("/").filter(Boolean)[0]?.toLowerCase();
  if (!first || RESERVED.has(first)) return null;
  return first;
}
