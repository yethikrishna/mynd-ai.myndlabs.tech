import type { ReactNode } from "react";

export interface RouteDef {
  path: string;
  // Lazy component loader, e.g. () => import("./pages/Foo")
  load: () => Promise<{ default: React.ComponentType }>;
}

export interface ProductOverlay {
  /** Extra cards/widgets injected into the product dashboard. */
  extendDashboard?: (slug: string) => ReactNode[];
  /** Extra routes mounted under /<slug>/... */
  routes?: () => RouteDef[];
}
