# Deploy

Single container, single Cloud Run service, path-based product routing.

## Build

The container is the forked Onyx image plus the `mynd` package and the bundled
`config/`. Reuse Onyx's Docker build (`core/backend/Dockerfile`,
`core/web/Dockerfile`) and ensure:

- `config/` is copied to `/app/config` (or set `MYND_CONFIG_DIR`).
- `core/backend/mynd` is on the Python path (it already is — it lives inside
  the backend package root).

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
