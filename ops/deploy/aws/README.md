# AWS deployment

Two paths:

- **`k8s/`** — **EKS (Kubernetes)**: deploy the **mynd-backend API first** with
  Onyx's Helm chart + a thin mynd overlay. Start here if you want Kubernetes.
- **This dir (EC2 + Terraform)** — a single VM running the whole stack via
  Docker Compose. Simpler/cheaper for an all-in-one box.

---

# AWS single-VM deployment (EC2 + Terraform)

Deploy the whole mynd Core stack (Onyx + the mynd layer + all products) on a
single AWS EC2 instance, served publicly over HTTPS on your domain. Same
self-building approach as the Oracle module — Terraform creates the box, the box
builds and runs everything.

> ⚠️ **AWS is not free for this.** The 12-month free tier is a `t2.micro`
> (1 GB RAM) — far too small for OpenSearch + two model servers + Postgres + the
> app. You pay for a real instance. If you want **$0**, use the Oracle Always
> Free module in `../free/oracle`. This module is the option for when you want
> AWS specifically and will pay for it.

```
Terraform ──> EC2 t4g (ARM, 16 GB) + Elastic IP + Security Group
                 └─ cloud-init: Docker → clone → build (arm64) → Let's Encrypt → up
You add an A record at your registrar ──> https://ai.myndlabs.tech
```

## Cost (rough, us-east-1, on-demand)

| Item | ~Monthly |
| --- | --- |
| `t4g.xlarge` (4 vCPU / 16 GB) | ~$98 on-demand • ~$30 Spot |
| `t4g.large` (2 vCPU / 8 GB) + `onyx-lite` | ~$49 on-demand • ~$15 Spot |
| 100 GB gp3 EBS | ~$8 |
| Elastic IP (attached) | $0 |
| Egress | first 100 GB/mo free, then ~$0.09/GB |
| LLM usage | your own API keys |

**Cheapest sane setup:** `t4g.large` + `use_spot = true` + the `onyx-lite`
compose ≈ **$20–25/mo**. Spot can be interrupted; the root EBS volume and the
Elastic IP persist, so it restarts in place.

## Prerequisites
- AWS account + credentials in your shell (`aws configure`, SSO, or env vars).
- The default VPC in your region (every account has one unless you deleted it).

## Steps
```bash
cd ops/deploy/aws
cp terraform.tfvars.example terraform.tfvars
# edit: region, instance_type, ssh_public_key, domain, email (+ use_spot if you like)

terraform init
terraform apply          # prints the Elastic IP
```
Then, at your registrar, add an **A record** for your domain → the Elastic IP.
Once it resolves, TLS provisions automatically and the app comes up at
`https://<domain>`. **First signup becomes admin.** Watch progress with
`ssh ubuntu@<eip>` → `tail -f /var/log/mynd-deploy.log`.

## Notes
- **ARM (t4g/Graviton):** images are built from source on the box, native arm64,
  so the mynd layer is baked in. The optional `code-interpreter` container may be
  amd64-only; if it won't start, the rest runs fine.
- **Cheaper RAM:** for `t4g.large` (8 GB), switch the compose to
  `docker-compose.onyx-lite.yml` in `cloud-init` (edit `/opt/mynd-deploy.sh`'s
  `COMPOSE` line) to drop the heavier services.
- **Managed datastores (optional, costs more):** for production you can move
  Postgres to RDS and search to Amazon OpenSearch Service and point the app at
  them via `.env` (`POSTGRES_HOST`, `OPENSEARCH_HOST`). Not needed to start.
- **Standalone per-product:** set `mynd_product = "eng"` and a per-product
  `domain`; see `../README.md` (free) and `ARCHITECTURE.md §4a`.
- This module reuses the Oracle module's `cloud-init.yaml.tftpl` and the shared
  `../free/docker-compose.mynd.override.yml`, so behavior matches across clouds.

> Authored without `terraform` available in this environment — not
> `validate`-checked. The HCL is conventional; review `terraform plan` before
> apply.
