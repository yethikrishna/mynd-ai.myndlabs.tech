# mynd Core backend layer

This package is the **Mynd Labs layer** that wraps the forked Onyx backend. It
lives inside `core/backend/` so it can import Onyx primitives directly and mount
into the existing FastAPI app **without modifying Onyx's auth or RBAC logic**.

## Why it lives here (and not at `core/auth`, `core/llm_auth`, …)

The architecture plan describes these as conceptual top-level modules. To be
*runnable* they must be importable by the Onyx FastAPI process and able to
`import onyx...`. Placing them as a `mynd` package on the backend's existing
import path achieves that with a one-line, rebase-friendly diff against upstream
Onyx. See `/ARCHITECTURE.md` for the full conceptual→physical mapping.

## Layout

| Module | Responsibility |
| --- | --- |
| `mynd.db.models` | `mynd_shared` SQLAlchemy tables (sessions, audit, credentials) |
| `mynd.routing` | `ProductContextMiddleware` → `request.state.product_slug` |
| `mynd.platform_config` | Loads `config/<slug>/*.yaml` into typed `ProductConfig` |
| `mynd.auth` | Session tracking, audit logging, per-product RBAC resolution |
| `mynd.llm_auth` | User/org credentials, OAuth, KMS crypto, resolver (user→org→system) |
| `mynd.server.config_router` | `GET /api/config[/{slug}]` for the frontend |
| `mynd.integration` | `register_mynd(app)` — the single wiring point |

## Wiring

A single call in `onyx/main.py::get_application` (just before `return
application`) attaches everything:

```python
from mynd.integration import register_mynd
register_mynd(application)
```

## Migrations

`alembic/versions/a1b2c3d4e5f6_mynd_shared_schema.py` creates the `mynd_shared`
schema and tables. Idempotent (`IF NOT EXISTS`) so it is safe under Onyx's
per-tenant migration runs.

## Credential resolution precedence

`resolve_llm_credential(...)` returns the credential to use for inference:

1. **user** — `user_llm_credentials` (this user, product, provider, default)
2. **org** — `org_llm_credentials` (this org, product, provider, default)
3. **system** — defer to Onyx's admin-configured provider (`onyx.db.llm`)

The resolved `scope` is recorded in the audit log.

## Secrets

Credential payloads are envelope-encrypted via `mynd.llm_auth.crypto`
(GCP KMS / AWS KMS in prod, local Fernet for dev). Plaintext secrets are never
stored or returned by the API.
