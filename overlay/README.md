# Product overlays

Overlays are **thin, optional** product-specific frontend code (target: < 500
LOC each) for UI the standard Onyx layouts/sections/components don't cover. Most
products need none — branding and content come from `config/<slug>/` and the
shared Opal design system.

## Where overlays live

Overlay implementations use the Next app's `@/` design-system alias (e.g.
`@/refresh-components/cards`), so they must compile **inside** the web app:

- **Buildable registry:** `core/web/src/mynd/overlays/`
  - `index.ts` — the slug → overlay registry + `getOverlay(slug)`
  - `<slug>.tsx` — per-product overlay (e.g. `grc.tsx`)
- **Contract (framework-agnostic):** [`types.ts`](./types.ts) in this directory
  documents the `ProductOverlay` shape.

The landing page (`core/web/src/mynd/components/ProductLanding.tsx`) calls
`getOverlay(slug).extendDashboard?.(slug)` to render overlay widgets.

## Contract

```ts
export interface ProductOverlay {
  /** Extra cards/widgets injected into the product dashboard/landing. */
  extendDashboard?: (slug: string) => React.ReactNode[];
}
```

Keep overlays declarative and small. If an overlay grows past a few hundred
lines, that signals the feature belongs in a shared `web/src/components`
component instead.
