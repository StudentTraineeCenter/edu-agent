# Service Architecture Snapshot

Focused architecture for `edu-web` (React SPA). For system-wide context see:
- `../../../docs/ARCHITECTURE.md`

## Context
- **Purpose**: Browser UI for EduAgent (projects, docs, chat, quizzes, flashcards, notes, mind maps, study sessions).
- **Upstream**: end users (browser).
- **Downstream**:
  - `edu-api` over HTTP (`VITE_SERVER_URL`)
  - Supabase Auth (`VITE_SUPABASE_URL`, `VITE_SUPABASE_ANON_KEY`)

## Component Diagram
```mermaid
graph TD
  User --> Browser[Browser]
  Browser --> Web[edu-web (React SPA)]
  Web -->|HTTPS| API[edu-api]
  Web -->|Auth| Supabase[Supabase]
```

## Data Flow
### Authentication
1. User signs in via Supabase client.
2. SPA stores session and obtains `access_token`.
3. SPA attaches `Authorization: Bearer <access_token>` when calling `edu-api`.

### API client generation
- The SPA includes a script that fetches the running API’s `openapi.json` and generates a typed client:
  - `pnpm gen:client` → `src/integrations/api/client.ts`.

### Streaming generation/chat
- Some features use streaming endpoints (SSE/streaming fetch) e.g.:
  - chat message streaming
  - generation progress streaming for quizzes/flashcards/notes/mind maps

## Cross-Cutting Concerns
- **Caching**: TanStack Query caches requests and manages refetch.
- **Runtime env validation**: `src/env.ts` validates required `VITE_*` vars.
- **Security**: never store secrets in frontend; only Supabase anon key and public URLs.
