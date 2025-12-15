# Service Deployment Plan

`edu-shared` is a shared Python package and is not deployed independently.

## Pipelines
- Built as part of the backend images (API/worker) via the monorepo Python workspace (`pyproject.toml`, `uv.lock`).
- Release cadence is coupled to the images that vendor this library.

## Environments
| Environment | Branch/Artifact | Purpose | Approvals |
| --- | --- | --- | --- |
| dev | `master` branch images | Development only | N/A |

## Release Steps
1. Update code under `src/edu-shared/src/edu_shared`.
2. Rebuild `edu-api` / `edu-worker` images (local Docker or Azure ACR task build).
3. Deploy via Terraform under `deploy/azure/terraform`.

## Infrastructure
None directly. This library provides helpers for:
- SQLAlchemy DB access
- Azure Key Vault secret loading
- Azure Storage Queue/Blob integrations
- Azure OpenAI embeddings + PGVector search
