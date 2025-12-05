#!/usr/bin/env bash
set -euo pipefail

# Build and push Web Docker image to Azure Container Registry
# Usage: ./build-push-web.sh [TAG] [DOCKERFILE_PATH] [CONTEXT_DIR]

ACR_NAME="$(terraform output -raw acr_name)"
REPO_NAME="$(terraform output -raw acr_repository_web)"
TAG="${1:-latest}"
DOCKERFILE_PATH="${2:-../web/Dockerfile}"
CONTEXT_DIR="${3:-../web}"

SERVER_URL="$(terraform output -raw app_server_url)"
SUPABASE_URL="$(terraform output -raw supabase_api_url)"

# Note: Supabase anon key is sensitive and should be retrieved from Key Vault or environment
# For build scripts, you may need to pass it as an environment variable or retrieve from Key Vault
SUPABASE_ANON_KEY="${SUPABASE_ANON_KEY:-}"

if [[ -z "$ACR_NAME" ]]; then
  echo "ERROR: ACR_NAME is not set. Please run 'terraform apply' first." >&2
  exit 1
fi

if [[ -z "$SUPABASE_ANON_KEY" ]]; then
  echo "ERROR: SUPABASE_ANON_KEY is not set. Please set it as an environment variable:" >&2
  echo "  export SUPABASE_ANON_KEY='your-anon-key'" >&2
  echo "Or retrieve it from Key Vault:" >&2
  echo "  export SUPABASE_ANON_KEY=\$(az keyvault secret show --vault-name <vault-name> --name supabase-anon-key --query value -o tsv)" >&2
  exit 1
fi

REGISTRY="${ACR_NAME}.azurecr.io"
IMAGE="${REGISTRY}/${REPO_NAME}:${TAG}"

echo "➤ Azure login"
az account show > /dev/null 2>&1 || az login

echo "➤ Logging in to ACR: $REGISTRY"
az acr login --name "$ACR_NAME"

echo "➤ Building Docker image: $IMAGE"
# Note: VITE_* variables must be build args since Vite replaces them at build time
# SUPABASE_ANON_KEY must be set as environment variable before running this script
docker build \
  --platform linux/amd64 \
  --file "$DOCKERFILE_PATH" \
  --tag "$IMAGE" \
  --build-arg VITE_SERVER_URL="https://${SERVER_URL}" \
  --build-arg VITE_SUPABASE_URL="${SUPABASE_URL}" \
  --build-arg VITE_SUPABASE_ANON_KEY="${SUPABASE_ANON_KEY}" \
  "$CONTEXT_DIR"

echo "➤ Pushing image to registry"
docker push "$IMAGE"

echo "✅ Image pushed successfully: $IMAGE"
