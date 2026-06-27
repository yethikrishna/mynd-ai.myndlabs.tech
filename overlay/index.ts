import type { ProductOverlay } from "./types";
import { engOverlay } from "./eng-overlay";
import { grcOverlay } from "./grc-overlay";

/**
 * Slug → overlay registry. The app shell looks up the active product slug here
 * and applies the overlay's extension hooks. Products without an entry use the
 * shared design system and their config/<slug> definition unchanged.
 */
export const OVERLAYS: Record<string, ProductOverlay> = {
  eng: engOverlay,
  grc: grcOverlay,
  // sales, support, people, sre: no overlay needed yet.
};

export function getOverlay(slug: string | null | undefined): ProductOverlay {
  if (!slug) return {};
  return OVERLAYS[slug] ?? {};
}

export type { ProductOverlay };
