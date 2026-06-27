# mynd Core — Architecture

mynd Core is a fork of [Onyx](https://github.com/onyx-dot-app/onyx) that serves
multiple vertical AI products from a single deployment at
`ai.myndlabs.tech/<product-slug>`, with shared auth and per-product isolation.

This document is the source of truth for **how the plan maps onto the actual
repository**, and records the deliberate deviations and why.

## 1. Repository layout (as built)

```
mynd-ai.myndlabs.tech/
├── core/                      # Fork of onyx-dot-app/onyx (CE + EE)
│   ├── backend/               # Onyx FastAPI backend
│   │   ├── onyx/              # Onyx CE (MIT)
│   │   ├── ee/                # Onyx EE (Onyx Enterprise License — see LICENSE-NOTES)
│   │   ├── alembic/versions/  # + a1b2c3d4e5f6_mynd_shared_schema.py
│   │   └── mynd/              # ★ the Mynd Labs layer (new code)
│   │       ├── routing/       # product-slug middleware
│   │       ├── auth/          # session tracking, audit, RBAC resolution
│   │       ├── llm_auth/      # user/org credentials, OAuth, crypto, resolver
│   │       ├── platform_config/  # loads /config into typed objects
│   │       ├── server/        # /api/config router
│   │       ├── db/            # mynd_shared SQLAlchemy models
│   │       └── integration.py # register_mynd(app) — single wiring point
│   ├── web/                   # Onyx Next.js frontend (Opal design system)
│   └── ...                    # rest of upstream Onyx (cli, deployment, docs…)
├── config/                    # Per-product config (YAML, zero code)
│   ├── eng/ grc/ sales/ support/ people/ sre/
├── overlay/                   # Thin optional product-specific frontend code
├── ops/                       # ci / deploy / observability / dns
├── LICENSE                    # MIT (Mynd original work)
├── LICENSE-NOTES.md           # Onyx fork + EE licensing caveats
└── ARCHITECTURE.md            # this file
```

## 2. Plan → physical mapping (and deviations)

The plan describes `core/auth`, `core/llm_auth`, `core/platform_config` as
top-level sibling directories. We instead placed them in **one importable
`mynd` package inside `core/backend/`**:

| Plan (conceptual) | Built (physical) | Why |
| --- | --- | --- |
| `core/auth/` | `core/backend/mynd/auth/` | Must `import onyx.*` and mount into the Onyx FastAPI app |
| `core/llm_auth/` | `core/backend/mynd/llm_auth/` | Same — runs in the backend process |
| `core/platform_config/` | `core/backend/mynd/platform_config/` | Loads repo-root `config/` |
| `core/backend/routing/product_router.py` | `core/backend/mynd/routing/product_router.py` | Grouped with the rest of the layer |
| `core/connectors`, `core/agents`, `core/enterprise` | already inside Onyx (`backend/onyx/connectors`, `backend/ee`) | Don't fragment upstream structure |

**Rationale:** keeping all new backend code in a single `mynd` package (a) lets
it import Onyx primitives directly, (b) reduces the upstream diff to a *single
line* in `onyx/main.py`, and (c) makes rebasing onto new Onyx releases trivial.
`config/`, `overlay/`, and `ops/` have no import constraints and follow the plan
layout literally.

## 3. How the layer attaches to Onyx

There are exactly **two** small upstream edits, both guarded and rebase-friendly:

1. `onyx/main.py::get_application()` — one call before `return application`:

   ```python
   from mynd.integration import register_mynd
   register_mynd(application)
   ```

   `register_mynd` (idempotent) installs the product-context middleware and
   mounts the config / credential / oauth routers.

2. `onyx/llm/factory.py::llm_from_provider()` — one call at the top:

   ```python
   from mynd.llm_auth.credential_injection import maybe_override_provider
   llm_provider = maybe_override_provider(llm_provider)
   ```

   A no-op for the system scope; substitutes a user/org BYO credential when one
   applies to the current request.

**Onyx's own auth, RBAC, chat, RAG, and connectors are otherwise untouched.**

### Threading context without signature changes

The product slug (from the URL) and the authenticated user/org are placed on
request-scoped `ContextVar`s (`mynd.context`). The middleware sets the slug; the
`bind_request_context` dependency sets user/org and records the product session.
Because FastAPI runs the dependency, endpoint, and Onyx's synchronous DB/LLM
calls in the same task, deep Onyx code (the LLM factory) reads these vars
**without any Onyx function signature changing**.

## 4. Request flow

```
GET ai.myndlabs.tech/eng/api/...                 (Onyx auth runs as usual)
        │
        ▼
ProductContextMiddleware  ──▶  request.state.product_slug = "eng"
        │
        ▼
handler  ──▶  resolve_llm_credential(user→org→system)
         ──▶  log_product_action(... product_slug, llm_credential_scope ...)
```

## 5. Shared auth, per-product isolation

- **Identity:** owned entirely by Onyx CE/EE (email/password, SSO/OIDC/SAML,
  RBAC). The mynd layer never authenticates a user itself.
- **Augmentation:** `mynd_shared.product_sessions` (per-product session
  tracking) and `mynd_shared.product_audit_logs` (per-product audit trail).
- **RBAC:** `mynd.auth.rbac` maps Onyx's base role + `config/<slug>/rbac.yaml`
  to a concrete capability set. It only narrows/maps — never grants beyond Onyx.
- **Data isolation (§8 of the plan):** RAG indices namespaced by
  `product_slug` + `org_id`; connector scopes/filters per `config/<slug>`;
  document-level gating enabled only for products that set it (grc, people).

## 6. LLM credentials

Three scopes, resolved in precedence order **user → org → system**:

1. `mynd_shared.user_llm_credentials` — BYO key / OAuth, set in the product UI.
2. `mynd_shared.org_llm_credentials` — org-wide keys.
3. Onyx's existing admin-configured providers (`onyx.db.llm`) — the fallback.

Secrets are envelope-encrypted (`mynd.llm_auth.crypto`: GCP/AWS KMS in prod,
Fernet locally) and never returned by the API. OAuth providers use the callback
`https://ai.myndlabs.tech/oauth/callback/<provider>`; a Celery task
(`mynd.llm_auth.token_refresh`, scheduled via `mynd.celery_schedule`) refreshes
tokens nearing expiry. Resolution + injection happen in
`mynd.llm_auth.credential_injection` at the `llm_from_provider` hook, and the
resolved scope is recorded on the audit log.

### Data isolation (`mynd.isolation`)

- `index_namespace(slug, org_id, source)` / `retrieval_filter(slug, org_id)` —
  namespace RAG indices and AND a metadata filter into every retrieval, so one
  product/org's documents never surface in another's (combined with Onyx ACLs,
  never the sole gate).
- `connector_isolation` — a product may only use connectors enumerated in its
  `connectors.yaml`, with the declared scopes/filters; `assert_connector_allowed`
  enforces it.

## 7. Adding a product

Config-only: create `config/<new-slug>/{product,rbac,agents,connectors}.yaml`.
The slug is discovered automatically by the config loader and routing
middleware. Add an `overlay/<slug>-overlay.tsx` only if you need custom UI.

## 8. Frontend (`core/web/src/mynd`)

The Onyx **Opal** design system (`core/web/src/{refresh-components,layouts,
sections,views}`) is reused as-is; only content + accent color vary per product.

- `ProductProvider` / `useProduct()` fetch `GET /api/config/<slug>` and apply
  `--mynd-primary` to the product subtree.
- `[productSlug]/page.tsx` → `ProductLanding`: config-driven marketing page
  (hero, features, connectors, overlay widgets). Onyx static routes take
  precedence over the dynamic `[productSlug]` segment.
- `[productSlug]/settings/models/page.tsx` → `ModelSettingsPage`: "platform
  defaults" vs "bring your own key" (user + org scopes), optional base URL for
  OpenAI-compatible/proxy/local endpoints, and OAuth "Connect" for providers
  that support it.
- `overlays/` — buildable product-overlay registry (the repo-root `/overlay`
  holds the contract; overlays live here because they use the `@/` alias).

> Build status: the frontend follows Onyx's conventions and primitives but was
> authored without a local `node_modules` (no `tsc`/Next build in this
> environment). Run `bun install && bunx tsc --noEmit` before shipping.

**Natural next increment:** point the product app shell (`/<slug>/app`) at the
slug so the sidebar surfaces the enabled agents/connectors from `config/<slug>`.
