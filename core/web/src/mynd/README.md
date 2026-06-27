# mynd frontend layer

The product-aware frontend that sits on top of Onyx's Opal design system. Only
branding and content vary per product — layouts and components are shared.

## Modules

| File | Responsibility |
| --- | --- |
| `types.ts` | Shared types (mirrors backend config + credentials API) |
| `api.ts` | Fetchers for `/api/config` and `/api/llm-credentials` |
| `useProductSlug.ts` | Derives the active product slug from the URL |
| `ProductContext.tsx` | `ProductProvider` + `useProduct()`; fetches config, applies `--mynd-primary` |
| `components/ProductLanding.tsx` | Config-driven marketing/landing page |
| `components/ModelSettingsPage.tsx` | Platform-defaults vs BYO-key (+ OAuth) UI |
| `overlays/` | Buildable product-overlay registry (see repo-root `/overlay`) |

## Routes (`web/src/app/[productSlug]/`)

| Path | Renders |
| --- | --- |
| `/<slug>` | `ProductLanding` |
| `/<slug>/settings/models` | `ModelSettingsPage` |

`[productSlug]` is a dynamic segment; Onyx's static routes (`/admin`, `/chat`,
`/app`, …) take precedence, so only product slugs land here. The mynd backend
middleware applies the same reserved-prefix rules server-side.

## Theming

`ProductProvider` sets `--mynd-primary` from `config.branding.primary_color`.
Product surfaces use `style={{ background: "var(--mynd-primary)" }}` for accents
while inheriting all other design tokens from the shared theme.

## Remaining wiring

The product app shell itself (`/<slug>/app`) reuses Onyx's existing chat/app
views; pointing those at the product slug (sidebar, enabled agents/connectors
from config) is the natural next increment.
