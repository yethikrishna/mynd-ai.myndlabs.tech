# mynd-backend on AWS EKS (API first)

Deploy **just the backend API** on EKS using Onyx's Helm chart + a thin mynd
overlay. "API first" = the chart's **lite** profile: PostgreSQL only — no vector
DB, Redis, model servers, or celery. Core chat/API works; RAG search is added
later by turning the vector DB back on.

```
build-and-push.sh ──> ECR (mynd-backend = Onyx backend + mynd layer + config)
                                   │
helm install (values-lite + values-mynd) ──> EKS
   └─ api-server pod (runs `alembic upgrade head`, incl. mynd_shared)
   └─ PostgreSQL (cloudnative-pg subchart)
```

> Not free: EKS control plane ≈ $73/mo + nodes (one `t3.large`/`t4g.large` is
> plenty for API-first). If cost is the priority, use `../../free/oracle`.

## Prerequisites
- `aws`, `kubectl`, `helm`, `eksctl`, `docker` (with buildx) installed and AWS creds configured.
- An EKS cluster + a node group. Quick start:
  ```bash
  eksctl create cluster --name mynd --region us-east-1 \
    --nodes 1 --node-type t3.large --managed
  ```

## 1. Build + push the image
```bash
export AWS_REGION=us-east-1
# PLATFORM=linux/arm64 if your node group is Graviton (t4g/m7g)
ops/deploy/aws/k8s/build-and-push.sh
# prints the ECR image, e.g. <acct>.dkr.ecr.us-east-1.amazonaws.com/mynd-backend:latest
```
Put that repo into `values-mynd.yaml` → `api.image.repository`.

## 2. Namespace + secret
```bash
kubectl create namespace mynd
KEY=$(openssl rand 32 | base64 | tr '+/' '-_')
kubectl -n mynd create secret generic mynd-secrets \
  --from-literal=MYND_LOCAL_ENCRYPTION_KEY="$KEY"
```

## 3. Fetch chart deps + install
```bash
helm dependency build ./core/deployment/helm/charts/onyx

helm upgrade --install mynd ./core/deployment/helm/charts/onyx \
  --namespace mynd \
  -f ./core/deployment/helm/charts/onyx/values-lite.yaml \
  -f ./ops/deploy/aws/k8s/values-mynd.yaml \
  --set api.image.repository=<ACCOUNT>.dkr.ecr.<REGION>.amazonaws.com/mynd-backend
```

## 4. Verify the API
```bash
kubectl -n mynd get pods            # api-server + postgres should become Ready
kubectl -n mynd logs deploy/mynd-api-server -f   # watch alembic + startup

# smoke test without an ingress:
kubectl -n mynd port-forward svc/mynd-api-server 8080:8080
curl -s localhost:8080/health
curl -s localhost:8080/api/config            # mynd: lists product slugs
```

## 5. Seed product agents (once)
```bash
kubectl -n mynd exec deploy/mynd-api-server -- python -m mynd.products.seed
```

## 6. Go public (when ready)
Enable an ingress in `values-mynd.yaml` (AWS Load Balancer Controller → ALB, or
ingress-nginx), then point a DNS record at the load balancer. For the full
product experience (search + indexing + frontend), drop `values-lite.yaml`,
re-enable `vectorDB`, deploy the `webserver`, and point celery/web images at the
same registry pattern.

## Notes
- **Image arch must match nodes.** Default build is `linux/amd64`; set
  `PLATFORM=linux/arm64` for Graviton node groups.
- **Migrations** run in the api container automatically (`alembic upgrade head`).
- **Config** is baked into the image (`/app/config`), so no ConfigMap mount is
  needed; `MYND_CONFIG_DIR=/app/config` is set via `api.extraEnv`.
- **Prod secrets:** prefer AWS KMS via IRSA — set `MYND_KMS_PROVIDER=aws` +
  `MYND_AWS_KMS_KEY_ID` and attach an IAM role to the service account instead of
  the local Fernet secret.
- **Managed datastores:** to use RDS / Amazon OpenSearch / ElastiCache instead
  of the in-cluster subcharts, disable them in values and set the corresponding
  `configMap` host/credentials env.
