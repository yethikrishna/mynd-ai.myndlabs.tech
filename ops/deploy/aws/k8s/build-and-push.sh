#!/usr/bin/env bash
# Build the mynd-backend image (Onyx backend + the mynd layer + product config
# baked in) and push it to ECR, for the EKS Helm deploy.
#
# Env:
#   AWS_REGION   (required)  e.g. us-east-1
#   ECR_REPO     (default mynd-backend)
#   TAG          (default latest)
#   PLATFORM     (default linux/amd64; use linux/arm64 for Graviton node groups)
set -euo pipefail

: "${AWS_REGION:?set AWS_REGION}"
ECR_REPO="${ECR_REPO:-mynd-backend}"
TAG="${TAG:-latest}"
PLATFORM="${PLATFORM:-linux/amd64}"

ROOT="$(git rev-parse --show-toplevel)"
ACCOUNT="$(aws sts get-caller-identity --query Account --output text)"
REG="$ACCOUNT.dkr.ecr.$AWS_REGION.amazonaws.com"
IMAGE="$REG/$ECR_REPO:$TAG"

# 1) Ensure the ECR repo exists + log in.
aws ecr describe-repositories --repository-names "$ECR_REPO" --region "$AWS_REGION" >/dev/null 2>&1 \
  || aws ecr create-repository --repository-name "$ECR_REPO" --region "$AWS_REGION" >/dev/null
aws ecr get-login-password --region "$AWS_REGION" | docker login --username AWS --password-stdin "$REG"

# 2) Build the Onyx backend image from source (this is where the mynd code, which
#    lives in core/backend/mynd, gets compiled in).
docker buildx build --platform "$PLATFORM" \
  -t onyx-backend-mynd:base \
  -f "$ROOT/core/backend/Dockerfile" "$ROOT/core/backend" --load

# 3) Layer the product config on top (Dockerfile.mynd copies config/ -> /app/config).
docker buildx build --platform "$PLATFORM" \
  --build-arg ONYX_BACKEND_IMAGE=onyx-backend-mynd:base \
  -t "$IMAGE" \
  -f "$ROOT/ops/deploy/Dockerfile.mynd" "$ROOT" --load

# 4) Push.
docker push "$IMAGE"
echo
echo "Pushed: $IMAGE"
echo "Set api.image.repository=$REG/$ECR_REPO and tag=$TAG in values-mynd.yaml"
