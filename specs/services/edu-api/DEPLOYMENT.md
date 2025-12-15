# Service Deployment Plan

Dev-only deployment; infrastructure is provisioned via Terraform.

References:
- `../../../docs/AZURE_DEPLOYMENT.md`
- `../../../deploy/azure/terraform/`

## Pipelines
- **CI** (expected): lint/format (ruff for Python, eslint/prettier for web), type checks.
- **CD** (dev):
  1. `terraform apply` provisions infra (ACR, Container Apps, Key Vault, Storage, App Insights, etc.).
  2. `deploy/azure/build.py` builds and pushes the API image via ACR Tasks.
  3. Terraform wires the pushed image into the API Container App.

## Environments
| Environment | Branch/Artifact | Purpose | Approvals |
| --- | --- | --- | --- |
| dev | `master` + `latest` image tags | Development environment | N/A |

## Release Steps
1. Preconditions
   - Terraform applied successfully.
   - Key Vault secrets present and RBAC configured.
2. Build and publish
   - From `deploy/azure/`: run `python build.py --container edu-api`.
3. Deploy
   - If tags or infra changed: re-run `terraform apply`.
4. Verify
   - Call `GET /health`.
   - Confirm `GET /openapi.json` is reachable.
5. Rollback
   - Re-deploy previous image tag via Terraform (update `acr_tag_api`) and `terraform apply`.

## Infrastructure
Service-specific infra dependencies (managed in Terraform):
- Azure Container Apps (API)
- Azure Container Registry (image hosting)
- Azure Storage Account (Blob + Queue)
- Azure Key Vault (secrets)
- Log Analytics + Application Insights
- PostgreSQL (via Supabase project in this repo’s Terraform)
