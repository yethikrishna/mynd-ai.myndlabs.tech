# Deploy

Single container, single Cloud Run service, path-based product routing.

## Build

The container is the forked Onyx image plus the `mynd` package and the bundled
`config/`. The `mynd` backend code already lives inside `core/backend`, so it is
built into the standard Onyx backend image. To bundle the repo-root `config/`,
build the overlay image with the **repo root** as the build context:

```bash
# 1) Build Onyx backend + web as usual (core/backend/Dockerfile, core/web/Dockerfile)
# 2) Overlay the product config onto the backend image:
docker build -f ops/deploy/Dockerfile.mynd \
  --build-arg ONYX_BACKEND_IMAGE=<onyx-backend-image> \
  -t mynd-core-backend .
```

`Dockerfile.mynd` copies `config/` to `/app/config` and sets `MYND_CONFIG_DIR`.
Frontend overlay code is bundled in the web image (it lives under
`core/web/src/mynd`).

## Migrate

Run Alembic after deploy (includes the `mynd_shared` migration
`a1b2c3d4e5f6`):

```bash
alembic upgrade head
# multi-tenant (cloud):
alembic -n schema_private upgrade head
```

## Apply

```bash
gcloud run services replace ops/deploy/cloudrun-service.yaml
```

## Deployment topologies

The same image runs in two modes:

### A) Shared (default) — `ai.myndlabs.tech/<slug>`
One service serves all products by path. `cloudrun-service.yaml`. No
`MYND_PRODUCT`.

### B) Standalone per-product — each product is its own app
Set `MYND_PRODUCT=<slug>` (and `NEXT_PUBLIC_MYND_PRODUCT=<slug>` for the web
build). The entire service is pinned to that product: every request — including
Onyx's own `/api` calls — is scoped to it, with its own domain, scaling, and
(optionally) its own database. Deploy one service per product
(`mynd-core-eng`, `mynd-core-grc`, …) using
`cloudrun-service-per-product.yaml`.

To serve the product at the domain root (`/` instead of `/<slug>`), add a Next
rewrite gated on the env var (single-product builds only):

```js
// next.config.js — rewrites()
async rewrites() {
  const p = process.env.NEXT_PUBLIC_MYND_PRODUCT;
  return p ? [{ source: "/", destination: `/${p}` }] : [];
}
```

Same codebase, same image — the env var is the only difference between "one app
with six products" and "six separately deployed apps."

## Stack

- **Cloud Run** — the Core container, all paths `/*`.
- **Cloud SQL (Postgres)** — schemas: Onyx CE, Onyx EE, `mynd_shared`.
- **Redis** — sessions + retrieval cache.
- **GCS / MinIO** — documents + artifacts.
- **HTTPS LB + Google-managed cert** — `ai.myndlabs.tech` → LB → Cloud Run.
