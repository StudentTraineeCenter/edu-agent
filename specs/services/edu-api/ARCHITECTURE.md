# Service Architecture Snapshot

Focused architecture for `edu-api` (FastAPI). For system-wide context see:
- `../../../docs/ARCHITECTURE.md`

## Context
- **Purpose**: Public HTTP API for EduAgent (projects, documents, chat, quizzes, flashcards, notes, mind maps, study sessions, usage, users).
- **Upstream callers**: `edu-web` SPA (browser), developers (local), potentially other clients.
- **Downstream dependencies**:
  - PostgreSQL (pgvector) via `edu_shared.db.*`
  - Azure Blob Storage (document files)
  - Azure Storage Queue (async tasks)
  - Supabase Auth (JWT validation with shared secret)
  - Azure OpenAI / AI Foundry (chat/generation flows; some also delegated to worker)

## Component Diagram
```mermaid
graph TD
  Web[edu-web SPA] -->|HTTPS| API[edu-api (FastAPI)]
  API -->|SQLAlchemy| DB[(PostgreSQL + pgvector)]
  API -->|upload/read| Blob[(Azure Blob Storage)]
  API -->|base64 JSON msg| Queue[(Azure Storage Queue)]
  Queue --> Worker[edu-worker]
  API -->|validate JWT| Supabase[Supabase Auth]
  API -->|LLM + embeddings| AOAI[Azure OpenAI]
```

## Data Flow
### Health & OpenAPI
- `/health` returns basic health payload.
- `/openapi.json` is served by FastAPI and used by the frontend client generator.
- `/` serves Scalar API reference UI.

### Document upload → async processing
1. Client uploads files to `POST /api/v1/projects/{project_id}/documents/upload`.
2. API validates file type and usage limits.
3. API uploads raw bytes to Blob `input` container.
4. API enqueues `DOCUMENT_PROCESSING` message to Azure Storage Queue.
5. Worker processes the document (Content Understanding → chunk → embeddings → pgvector).

### AI generation (quizzes/flashcards/notes/mind maps)
- API creates the resource, then either:
  - queues an async task to `edu-worker` (non-streaming “background” generation), or
  - streams progress/outputs from a streaming endpoint (e.g. `.../generate/stream`).

### Chat
- Chat CRUD is synchronous.
- Chat message completion is available via streaming endpoint `POST /api/v1/projects/{project_id}/chats/{chat_id}/messages/stream`.

## Cross-Cutting Concerns
- **Resilience**: queue-based async processing for document pipeline; worker retries via queue visibility timeout.
- **Rate limiting / quotas**: per-user per-day limits enforced by `UsageService` and custom `UsageLimitExceededError` handler.
- **Error model**: JSON `{ "error": { "message", "status_code", ... } }` for most errors (see exception handlers).
- **CORS**: currently permissive (`allow_origins=["*"]`) for development.
- **Secrets/config**: `pydantic-settings` with Key Vault settings source (dev Key Vault URI is currently hard-coded in settings source).
