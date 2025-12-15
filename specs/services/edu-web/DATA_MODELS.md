# Service Data Models

`edu-web` owns UI state and uses generated API client types.

## Schema Inventory
| Name | Type | Owner | Source of Truth | Version |
| --- | --- | --- | --- | --- |
| UI route state | TypeScript types | edu-web | TanStack Router routes | N/A |
| API client types | TypeScript types (generated) | edu-web | `pnpm gen:client` output | N/A |
| Supabase session | JSON | Supabase | Supabase JS client | N/A |

## Detailed Schemas

### Runtime environment
Source: `src/env.ts`.
- `VITE_SERVER_URL` (base URL for `edu-api`)
- `VITE_SUPABASE_URL`
- `VITE_SUPABASE_ANON_KEY`

### API types
- Generated file: `src/integrations/api/client.ts`.
- Regeneration requires `edu-api` running locally at `http://localhost:8000`.

### Streaming payloads
- Streaming endpoints provide incremental updates; the SPA consumes them via `fetch()` streaming.
