# Service Data Models

`edu-worker` does not expose an HTTP API; its primary contracts are **queue messages** and **DB updates**.

## Schema Inventory
| Name | Type | Owner | Source of Truth | Version |
| --- | --- | --- | --- | --- |
| QueueTaskMessage | JSON (Base64 queue message) | edu-shared | `src/edu-shared/src/edu_shared/schemas/queue.py` | N/A |
| Document blobs | Binary + text | platform | Azure Storage containers (`input`, `output`) | N/A |
| Core DB models | Postgres tables | edu-shared | `src/edu-shared/src/edu_shared/db/models.py` | Alembic |

## Detailed Schemas

### QueueTaskMessage
- **Purpose**: identify task type and typed payload.
- **Shape**:
```json
{
  "type": "document_processing",
  "data": { "document_id": "...", "project_id": "...", "user_id": "..." }
}
```
- **Transport encoding**: JSON is Base64 encoded before being sent.

### Document output blobs
- **Original blob**: moved from `input` to `output` container under `{project_id}/{document_id}.{ext}`.
- **Processed content**: written as `{project_id}/{document_id}.contents.txt` in `output`.

### Document segments
- **Storage**: `document_segments` table.
- **Embedding**: `embedding_vector` uses pgvector `vector(3072)`.
