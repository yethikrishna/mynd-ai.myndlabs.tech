# Free public deployment — Oracle Cloud Always Free

Deploy the entire mynd Core stack (Onyx + the mynd layer + all products) on a
**$0-forever** Oracle Cloud "Always Free" ARM VM, served publicly over HTTPS on
your own domain. Infrastructure is Terraform; the VM self-builds and starts the
stack on first boot.

```
Terraform ──> Oracle A1 VM (4 CPU / 24 GB, free) ──> Docker Compose
                                                      (Onyx + mynd, built from
                                                       source so the mynd layer
                                                       is baked in)
                                                      └─ nginx + Let's Encrypt
You add an A record at your registrar ──────────────> https://ai.myndlabs.tech
```

All six products are served from the one box at `…/eng`, `…/grc`, `…/sales`,
`…/support`, `…/people`, `…/sre`. (One free VM = shared mode. Standalone
per-product deployment is possible too — see the bottom.)

---

## Read this first — the honest caveats

- **It needs a credit card to sign up** for Oracle Cloud (Always Free is not
  charged, but signup requires a card). The A1 shape itself is free forever.
- **A1 capacity can be scarce.** "Out of host capacity" on `terraform apply`
  is common in busy regions — retry, or try a different `region`. This is an
  Oracle limitation, not a bug here.
- **ARM (arm64).** The free shape is ARM. The stack is **built from source on
  the VM** (Onyx images + our mynd layer) so it's native arm64. Postgres, Redis,
  OpenSearch, MinIO, nginx all ship arm64. The optional `code-interpreter`
  service may be amd64-only — if it fails to start, the rest still runs; comment
  it out of `docker-compose.prod.yml` if it bothers you (it only powers the
  code-execution feature).
- **First boot takes 10–30 min** (building the web + backend images on ARM, then
  the model servers download embedding models). Watch:
  `ssh ubuntu@<ip>` then `tail -f /var/log/mynd-deploy.log`.
- **RAM:** the full stack uses ~10–14 GB of the 24 GB. Comfortable. If you ever
  run it on a smaller box, swap in `docker-compose.onyx-lite.yml`.
- **No GPU / no LLM cost required.** Embeddings run on CPU locally. Users/admins
  add their own OpenAI/Anthropic keys in each product's Model Settings (the mynd
  BYO-key UI), or you set a platform key in Onyx admin.

---

## Steps

### 1. Oracle setup (one time)
1. Create a free Oracle Cloud account: https://www.oracle.com/cloud/free/
2. Console → your profile → **API keys** → **Add API key** → download the
   private key (`.pem`), note the **fingerprint**.
3. Note your **tenancy OCID**, **user OCID**, and **region** (console → profile
   / region menu).

### 2. Configure
```bash
cd ops/deploy/free/oracle
cp terraform.tfvars.example terraform.tfvars
# edit terraform.tfvars: OCI ids, region, ssh_public_key, domain, email
```

### 3. Apply
```bash
terraform init
terraform apply
# note the public_ip output
```
If you hit "out of host capacity", re-run apply (capacity frees up) or change
`region`.

### 4. Point DNS (at your registrar)
Add an **A record** for your domain → the `public_ip` from the output:
```
ai.myndlabs.tech     A   <public_ip>
www.ai.myndlabs.tech A   <public_ip>   (optional)
```
The VM polls for this; once it resolves, Let's Encrypt issues the cert
automatically. No port-forwarding needed (it's a public IP; 80/443 are opened
by the Terraform security list).

### 5. Done
Visit `https://ai.myndlabs.tech`. The **first account you sign up becomes the
admin**. Product agents are auto-seeded. Add LLM keys per product under
`/<slug>/settings/models`.

---

## Day-2

```bash
ssh ubuntu@<public_ip>
cd /opt/mynd/core/deployment/docker_compose
COMPOSE="docker compose --env-file .env \
  -f docker-compose.prod.yml \
  -f /opt/mynd/ops/deploy/free/docker-compose.mynd.override.yml"

$COMPOSE ps                 # status
$COMPOSE logs -f api_server # logs
# update to latest code:
cd /opt/mynd && git pull && cd core/deployment/docker_compose && $COMPOSE up -d --build
```

Migrations run automatically on `api_server` start (`alembic upgrade head`),
including the `mynd_shared` schema.

### Turning on retrieval isolation
Off by default. To enable per-product document isolation: bind connectors to
products (`PUT /api/product/<slug>/connectors/<cc_pair_id>`), re-index them, then
set `MYND_RETRIEVAL_ISOLATION=true` in `.env` and `$COMPOSE up -d`.

---

## Standalone per-product deployment (optional)

To run a product as its **own** app (its own VM + domain), set in
`terraform.tfvars`:
```hcl
mynd_product = "eng"
domain       = "eng.myndlabs.tech"
```
The backend is pinned via `MYND_PRODUCT`. For the frontend to serve the product
at `/`, the web image must be **built** with `NEXT_PUBLIC_MYND_PRODUCT=eng` (add
it as a build arg on `web_server` in the override) and add the `/ -> /eng`
rewrite from `ops/deploy/README.md`. One VM per product (each uses the full free
allotment, so this means one Oracle tenancy per product or a paid box per extra
product).

---

## Cost

| Item | Cost |
| --- | --- |
| Oracle A1 VM (4 CPU / 24 GB) | **$0** (Always Free) |
| 100 GB boot volume | $0 (within 200 GB free) |
| Egress | $0 (within 10 TB/mo free) |
| TLS (Let's Encrypt) | $0 |
| LLM usage | your own API keys (or platform key) |

Everything except LLM tokens is free. If A1 capacity is a recurring problem, a
Hetzner CX22 (8 GB, ~€4/mo) runs the same Compose stack — see `ops/deploy`.
