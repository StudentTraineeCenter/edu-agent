# Service Deployment Plan

Dev-only deployment; provisioned via Terraform.

References:
- `../../../docs/AZURE_DEPLOYMENT.md`
- `../../../deploy/azure/terraform/`

## Pipelines
- **Build**: `pnpm build` (Vite build + TypeScript).
- **Container image**: built and pushed via `deploy/azure/build.py --container edu-web`.
- **Deploy**: wired by Terraform to a Linux Web App (SPA served via nginx).

## Environments
| Environment | Branch/Artifact | Purpose | Approvals |
| --- | --- | --- | --- |
| dev | `master` + `latest` image tag | Dev web UI | N/A |

## Release Steps
1. Ensure infra exists (`terraform apply`).
2. Build/push image (`python build.py --container edu-web`).
3. Verify `VITE_SERVER_URL` points to the deployed API URL.
4. Verify sign-in and basic navigation.

## Infrastructure
- Linux Web App hosting the built SPA image
- App settings for runtime configuration (Vite build-time envs are injected during build)
