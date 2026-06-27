# ai.myndlabs.tech — mynd Core

One shared AI platform (forked from [Onyx](https://github.com/onyx-dot-app/onyx))
serving multiple vertical products from a single deployment at
**`ai.myndlabs.tech/<product-slug>`**, with shared auth and per-product
isolation.

```
ai.myndlabs.tech/eng     mynd Engineering     — codebases, CI logs, runbooks
ai.myndlabs.tech/grc     mynd ComplianceVault — evidence, controls, audit
ai.myndlabs.tech/sales   mynd SalesAI         — pipeline, accounts, deals
ai.myndlabs.tech/support mynd SupportFlow     — ticket deflection, agent assist
ai.myndlabs.tech/people  mynd PeopleOps       — HR policies, onboarding
ai.myndlabs.tech/sre     mynd SRE Command     — incidents, alerts, runbooks
```

## What's here

| Path | What |
| --- | --- |
| `core/` | Fork of Onyx (CE + EE) — the platform. Onyx logic is untouched. |
| `core/backend/mynd/` | **The Mynd Labs layer**: product routing, per-product sessions + audit, user/org LLM credentials, config loader. Mounts into Onyx via one line. |
| `config/<slug>/` | Per-product definition (branding, connectors, agents, RBAC) — **zero code to add a product**. |
| `overlay/` | Thin optional product-specific frontend code. |
| `ops/` | CI, deploy (Cloud Run), observability, DNS. |
| `ARCHITECTURE.md` | How the plan maps onto the repo + design decisions. |
| `LICENSE` / `LICENSE-NOTES.md` | MIT for Mynd work; **important caveats** on Onyx EE licensing. |

## Core ideas

- **Shared identity, wrapped not replaced.** Onyx CE/EE owns auth (email/SSO,
  RBAC). The mynd layer only adds per-product session tracking + audit logging.
- **Products are config.** A new vertical is a `config/<slug>/` directory; the
  routing middleware and config loader discover it automatically.
- **Bring-your-own LLM keys.** Credentials resolve **user → org → system**;
  users add keys (or OAuth) per product, with a platform key as fallback.
  Secrets are KMS-encrypted at rest.
- **Per-product isolation.** Index namespacing, scoped connectors, and optional
  document-level RBAC keep one product's data out of another's.

## Quickstart (development)

The platform runs as the Onyx stack plus the mynd layer:

```bash
# 1) Onyx services (Postgres, Redis, Vespa, model server, web). See core/README.md
#    and core/deployment for the upstream dev setup.
# 2) Apply migrations (includes mynd_shared):
cd core/backend && alembic upgrade head
# 3) Validate product config:
MYND_CONFIG_DIR="$(git rev-parse --show-toplevel)/config" \
  python -c "from mynd.platform_config.config_loader import list_product_slugs as l; print(l())"
```

The mynd layer auto-registers on app startup via `register_mynd()` in
`onyx/main.py`. See `core/backend/mynd/README.md` for the module map and
`ARCHITECTURE.md` for the full design.

## Licensing — read this

The Mynd-authored code is MIT. The fork under `core/` includes Onyx's `ee`
(Enterprise) directories, which upstream licenses under the **Onyx Enterprise
License, not MIT**. This repo keeps those upstream license files intact and does
not restamp them. See [`LICENSE-NOTES.md`](./LICENSE-NOTES.md) before relying on
the EE code.
