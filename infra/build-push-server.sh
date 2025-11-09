#!/usr/bin/env bash
set -euo pipefail

# Build and push API Docker image to Azure Container Registry
# Usage: ./build-push-server.sh [TAG] [DOCKERFILE_PATH] [CONTEXT_DIR]

ACR_NAME="$(terraform output -raw acr_name)"
REPO_NAME="$(terraform output -raw acr_repository_api)"
TAG="${1:-latest}"
DOCKERFILE_PATH="${2:-../server/Dockerfile}"
CONTEXT_DIR="${3:-../server}"

if [[ -z "$ACR_NAME" ]]; then
  echo "ERROR: ACR_NAME is not set. Please run 'terraform apply' first." >&2
  exit 1
fi

REGISTRY="${ACR_NAME}.azurecr.io"
IMAGE="${REGISTRY}/${REPO_NAME}:${TAG}"

echo "➤ Azure login"
az account show > /dev/null 2>&1 || az login

echo "➤ Logging in to ACR: $REGISTRY"
az acr login --name "$ACR_NAME"

echo "➤ Building Docker image: $IMAGE"
docker build \
  --platform linux/amd64 \
  --file "$DOCKERFILE_PATH" \
  --tag "$IMAGE" \
  "$CONTEXT_DIR"

echo "➤ Pushing image to registry"
docker push "$IMAGE"

echo "✅ Image pushed successfully: $IMAGE"
