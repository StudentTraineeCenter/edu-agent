#!/usr/bin/env bash
set -euo pipefail

ACR_NAME="$(terraform output -raw acr_name)"
REPO_NAME="$(terraform output -raw acr_repository_api)"
TAG="${TAG:-latest}"
DOCKERFILE_PATH="${DOCKERFILE_PATH:-../server/Dockerfile}"
CONTEXT_DIR="${CONTEXT_DIR:-../server}"

if [[ -z "$ACR_NAME" ]]; then
  echo "ERROR: ACR_NAME is not set. Please export it (from Terraform output) or set in the script."
  exit 1
fi

# Full registry login server (Azure ACR)
REGISTRY="${ACR_NAME}.azurecr.io"
IMAGE="${REGISTRY}/${REPO_NAME}:${TAG}"

echo "➤ Azure login"
az account show > /dev/null 2>&1 || az login

echo "➤ Ensure you’re logged in to ACR: $REGISTRY"
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

exit 0