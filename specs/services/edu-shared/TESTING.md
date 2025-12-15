# Service Testing Strategy

`edu-shared` currently has minimal dedicated automated tests in this repo.

## Test Matrix
| Layer | Tools | Scope | Owner |
| --- | --- | --- | --- |
| Unit | `pytest` (recommended) | DB model helpers, schema validation, Key Vault source mapping | Backend |
| Integration | Docker Compose (recommended) | DB migrations + basic CRUD against Postgres | Backend |

## Scenarios
- Settings load from Key Vault when available.
- Settings fall back to env vars when Key Vault is unavailable.
- Queue task payload examples conform to `edu_shared.schemas.queue` shapes.

## Environments
- Local dev: Docker Compose Postgres + Azurite.
- CI: currently not defined in repo; add as needed.

## Quality Gates
- Lint/format: `ruff` (repo root).
- Add unit tests before widening the public surface area.
