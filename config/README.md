# Product configuration

Each subdirectory defines one vertical product served at
`ai.myndlabs.tech/<slug>`. **Adding a product is a config-only change** — no
code required. Drop a new `<slug>/` directory with the files below and it is
discovered automatically (see `mynd.platform_config.config_loader` and
`mynd.routing.product_router`).

## Files per product

| File | Purpose | Exposed to browser? |
| --- | --- | --- |
| `product.yaml` | Name, slug, branding, enabled connectors/providers, feature flags | Yes (via `GET /api/config/<slug>`) |
| `rbac.yaml` | Product roles mapped onto Onyx EE RBAC primitives | No |
| `agents.yaml` | Agent templates available in the product | No |
| `connectors.yaml` | Connector scopes + data filters (isolation) | No |

Only the `public_dict()` subset of `product.yaml` is shipped to the frontend;
RBAC, agent, and connector internals stay server-side.

## Current products

| Slug | Product | Focus |
| --- | --- | --- |
| `eng` | mynd Engineering | Codebases, CI logs, runbooks |
| `grc` | mynd ComplianceVault | Evidence, controls, audit readiness |
| `sales` | mynd SalesAI | Pipeline, accounts, deal intelligence |
| `support` | mynd SupportFlow | Ticket deflection, agent assist |
| `people` | mynd PeopleOps | HR policies, onboarding |
| `sre` | mynd SRE Command | Incidents, alerts, runbooks |

## Validation

The loader resolves this directory via `MYND_CONFIG_DIR` (containers/tests) or
relative to the repo root. To validate locally:

```bash
MYND_CONFIG_DIR=$(pwd)/config python -c \
  "from mynd.platform_config.config_loader import list_product_slugs as l; print(l())"
```
