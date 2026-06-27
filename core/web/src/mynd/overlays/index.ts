import type { ReactNode } from "react";

// Buildable product-overlay registry. Lives under web/src so overlay code can
// use the `@/` design-system alias and compile within the Next app. The
// repo-root /overlay directory documents the contract; this is its binding.

export interface ProductOverlay {
  /** Extra cards/widgets injected into the product dashboard/landing. */
  extendDashboard?: (slug: string) => ReactNode[];
}

import { grcOverlay } from "./grc";

export const OVERLAYS: Record<string, ProductOverlay> = {
  grc: grcOverlay,
  // eng, sales, support, people, sre: no overlay needed yet.
};

export function getOverlay(slug: string | null | undefined): ProductOverlay {
  if (!slug) return {};
  return OVERLAYS[slug] ?? {};
}
