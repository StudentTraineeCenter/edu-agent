# Service Testing Strategy

## Test Matrix
| Layer | Tools | Scope | Owner |
| --- | --- | --- | --- |
| Unit | Vitest | component and utility tests | edu-web |
| Integration | Vitest + jsdom | API client adapters (mocked) | edu-web |
| Contract | OpenAPI client generation | API compatibility | edu-web + edu-api |

## Scenarios
- Auth: sign in → token present → API calls succeed.
- Streaming: generation streams render progressively.

## Environments
- **Local**: `pnpm dev` on port 3000.
- **API dependency**: local API at `http://localhost:8000`.

## Quality Gates
- `pnpm lint`, `pnpm test`, `pnpm build`.
