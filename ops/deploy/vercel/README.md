# Vercel deployment — the static marketing site

## What Vercel hosts (and what it can't)

Vercel serves the **public product marketing site**: an index plus one branded
page per product, generated from `config/<slug>/product.yaml`. Pure static
HTML — no backend, no secrets.

Vercel **cannot** host the rest of the platform, and it's worth being precise
about why:

- The **backend** (FastAPI + Celery + Postgres + OpenSearch + model servers) is
  a long-running stateful cluster — that's the EKS/VM deployment (`../aws`,
  `../free`).
- The **full app frontend** (`core/web`) relies on nginx proxying `/api/*` to
  the backend on the same origin (there is no general `/api` rewrite in
  `next.config.js`) and on same-origin cookie auth. Hosting it on Vercel only
  makes sense once the backend has a public URL — then add an `/api/:path*`
  rewrite to that origin and align cookie domains. Until then a Vercel deploy of
  the app would build fine and fail at login.

## Files

| File | Purpose |
| --- | --- |
| `generate_site.py` | Reads `config/*/product.yaml` → writes `site/` (index + per-product pages) |
| `site/` | The generated static site (committed, so git-triggered deploys need no build) |
| `/vercel.json` (repo root) | Static deploy: no build, `outputDirectory: ops/deploy/vercel/site` |
| `/.vercelignore` (repo root) | Uploads only the site — never the 68 MB Onyx fork |

Regenerate after editing product config:

```bash
python3 ops/deploy/vercel/generate_site.py
```

`MYND_APP_ORIGIN` (default `https://ai.myndlabs.tech`) sets where the "Open
app" CTAs point.

## Deploying

**Option A — git integration (recommended, zero CLI):**
1. vercel.com → Add New → Project → import `yethikrishna/mynd-ai.myndlabs.tech`.
2. Leave the root directory as the repo root — `vercel.json` does the rest
   (no build command, static output dir).
3. Every push deploys. Point `www.myndlabs.tech` (or a `mynd.vercel.app`
   subdomain) at the project in the Vercel dashboard.

**Option B — CLI (one-off):**
```bash
npm i -g vercel
vercel login          # or export VERCEL_TOKEN=...
vercel deploy --prod  # from the repo root
```

## Suggested domain split

| Domain | Serves | Host |
| --- | --- | --- |
| `www.myndlabs.tech` | this marketing site | Vercel |
| `ai.myndlabs.tech` | the full app (all products) | EKS / VM |
