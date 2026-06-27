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

## Stack

- **Cloud Run** — the Core container, all paths `/*`.
- **Cloud SQL (Postgres)** — schemas: Onyx CE, Onyx EE, `mynd_shared`.
- **Redis** — sessions + retrieval cache.
- **GCS / MinIO** — documents + artifacts.
- **HTTPS LB + Google-managed cert** — `ai.myndlabs.tech` → LB → Cloud Run.
