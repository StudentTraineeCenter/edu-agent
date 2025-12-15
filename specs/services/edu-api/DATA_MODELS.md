# Service Data Models

This service primarily owns the **HTTP API contract** and uses shared DTOs and DB models from `edu-shared`.

## Schema Inventory
| Name | Type | Owner | Source of Truth | Version |
| --- | --- | --- | --- | --- |
| REST API (`/api/v1/...`) | HTTP (OpenAPI) | edu-api | Runtime OpenAPI | N/A |
| Error envelope | JSON | edu-api | `src/edu-api/exception_handlers.py` | N/A |
| Queue task message | JSON (base64 payload) | edu-shared | `src/edu-shared/src/edu_shared/schemas/queue.py` | N/A |
| Core DB models (User/Project/Document/...) | Postgres tables | edu-shared | `src/edu-shared/src/edu_shared/db/models.py` | Alembic |

## Detailed Schemas

### Error envelope
- **Purpose**: consistent API error responses.
- **Example**:
```json
{
  "error": {
    "message": "Resource not found",
    "status_code": 404
  }
}
```
- **Notes**: Some validation errors include `details` list.

### Authentication principal
- **Purpose**: identify the caller.
- **Source**: Supabase JWT (`Authorization: Bearer <token>`).
- **Key fields used**:
  - `sub` (Supabase user id)
  - `email`
  - `user_metadata.name` / `user_metadata.full_name`

### Document pipeline records
- **Purpose**: track uploaded docs and processing/indexing state.
- **Storage**: Postgres tables (see `edu-shared` models): `documents`, `document_segments`.
- **Key fields**:
  - `documents.status` (e.g. uploaded/processed/indexed/failed)
  - `document_segments.embedding_vector` (pgvector `vector(3072)`)

### Async queue task
- **Purpose**: delegate expensive operations (document processing and AI generation) to `edu-worker`.
- **Storage**: Azure Storage Queue message content (Base64 JSON).
- **Schema**: see `edu_shared.schemas.queue.QueueTaskMessage`.
