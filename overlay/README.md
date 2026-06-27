# Product overlays

Overlays are **thin, optional** product-specific frontend code (target: < 500
LOC each) for UI that the standard Onyx layouts/sections/components don't cover.
Most products need none — branding and content come from `config/<slug>/` and
the shared Opal design system.

An overlay exports extension hooks that the app shell calls when a product slug
is active. The registry in `index.ts` maps slug → overlay module.

## Contract

```ts
export interface ProductOverlay {
  /** Extra cards/widgets injected into the product dashboard. */
  extendDashboard?: (slug: string) => React.ReactNode[];
  /** Extra routes mounted under /<slug>/... */
  routes?: () => RouteDef[];
}
```

Keep overlays declarative and small. If an overlay grows past a few hundred
lines, that signals the feature belongs in a shared `web/src/components`
component instead.
