# Service Testing Strategy

## Test Matrix
| Layer | Tools | Scope | Owner |
| --- | --- | --- | --- |
| Unit | (limited) | Service-layer functions and DTO validation | edu-api/edu-shared |
| Integration | manual / local docker-compose | API ↔ Postgres ↔ Azurite | edu-api |
| Contract | OpenAPI schema generation | API surface stability | edu-api + edu-web |

## Scenarios
- Upload document and observe async processing triggered via queue.
- Create quiz/flashcards/notes and validate generation (queued + streaming endpoints).
- Auth flow: invalid token returns 401; missing secret returns 500.

## Environments
- **Local**: `docker-compose up --build api worker db azurite`.
- **Dev Azure**: provisioned with Terraform; logs in App Insights.

## Quality Gates
- Lint/format: ruff (repo-level configuration).
- Frontend contract sanity: `pnpm gen:client` requires API running locally.
