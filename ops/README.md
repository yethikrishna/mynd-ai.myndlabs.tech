# ops/

Infrastructure and operational config for the single mynd Core deployment that
serves every product under `ai.myndlabs.tech/<slug>`.

| Dir | Contents |
| --- | --- |
| `ci/` | Lint, type-check, tests, license scan, container build/deploy |
| `deploy/` | Container + Cloud Run service definition, example env |
| `observability/` | Logging / metrics / tracing conventions |
| `dns/` | DNS + SSL setup for `ai.myndlabs.tech` |

## Deployment model

One container (forked Onyx + the `mynd` layer + bundled `config/`), one Cloud
Run service, routed by path. All products share auth and the platform; data is
isolated per product/org (see `/ARCHITECTURE.md` §8). Scaling is horizontal via
Cloud Run.

## Postgres schemas

| Schema | Owner |
| --- | --- |
| Onyx CE tables | upstream Onyx (Community) |
| Onyx EE tables | upstream Onyx (Enterprise — see licensing notes) |
| `mynd_shared` | the mynd layer (sessions, audit, LLM credentials) |
