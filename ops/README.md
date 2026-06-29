# ops/

Infrastructure and operational config for the single mynd Core deployment that
serves every product under `ai.myndlabs.tech/<slug>`.

| Dir | Contents |
| --- | --- |
| `ci/` | Lint, type-check, tests, license scan, container build/deploy |
| `deploy/` | Container + Cloud Run service definition, example env |
| `deploy/free/` | **Free public hosting** — Oracle Always Free VM via Terraform (start here) |
| `deploy/aws/` | AWS EC2 (Graviton/ARM) via Terraform — paid, ~$20–100/mo |
| `deploy/aws/k8s/` | AWS EKS (Kubernetes) — mynd-backend API via Onyx Helm chart + mynd overlay |
| `observability/` | Logging / metrics / tracing conventions |
| `dns/` | DNS + SSL setup for `ai.myndlabs.tech` |

> **Just want it live for free?** See [`deploy/free/README.md`](deploy/free/README.md):
> Terraform → a $0 Oracle Always-Free VM → the whole stack on your domain.

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
