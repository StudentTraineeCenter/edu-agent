# Service Deployment Plan

Dev-only deployment; provisioned and wired via Terraform.

References:
- `../../../docs/AZURE_DEPLOYMENT.md`
- `../../../deploy/azure/terraform/`

## Pipelines
- **Build**: `deploy/azure/build.py --container edu-worker` uses ACR Tasks to build/push container images.
- **Deploy**: Terraform applies the updated image tag for the worker container app.

## Environments
| Environment | Branch/Artifact | Purpose | Approvals |
| --- | --- | --- | --- |
| dev | `master` + `latest` image tags | Background processing for dev | N/A |

## Release Steps
1. Ensure infra exists (`terraform apply`).
2. Build/push image (`python build.py --container edu-worker`).
3. If tag changed, re-apply Terraform.
4. Verify by enqueueing a small task and observing logs.

## Infrastructure
- Azure Container Apps (worker)
- Azure Storage Queue (task intake)
- Azure Blob Storage (document blobs)
- Azure AI services (Content Understanding + OpenAI)
- Postgres (Supabase) for persisted results
- Log Analytics + Application Insights
