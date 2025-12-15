# Service Data Models

`edu-shared` defines canonical persistence models and typed message schemas that are shared by backend services.

## Schema Inventory



| Name | Type | Owner | Source of Truth | Version |
| --- | --- | --- | --- | --- |
| `users` | Postgres table | `edu-shared` | `edu_shared.db.models.User` | N/A |
| `projects` | Postgres table | `edu-shared` | `edu_shared.db.models.Project` | N/A |
| `documents` | Postgres table | `edu-shared` | `edu_shared.db.models.Document` | N/A |
| `document_segments` | Postgres table | `edu-shared` | `edu_shared.db.models.DocumentSegment` | N/A |
| `chats` | Postgres table | `edu-shared` | `edu_shared.db.models.Chat` | N/A |
| `flashcard_groups` | Postgres table | `edu-shared` | `edu_shared.db.models.FlashcardGroup` | N/A |
| `flashcards` | Postgres table | `edu-shared` | `edu_shared.db.models.Flashcard` | N/A |
| `flashcard_progress` | Postgres table | `edu-shared` | `edu_shared.db.models.FlashcardProgress` | N/A |
| `quizzes` | Postgres table | `edu-shared` | `edu_shared.db.models.Quiz` | N/A |
| `quiz_questions` | Postgres table | `edu-shared` | `edu_shared.db.models.QuizQuestion` | N/A |
| `notes` | Postgres table | `edu-shared` | `edu_shared.db.models.Note` | N/A |
| `mind_maps` | Postgres table | `edu-shared` | `edu_shared.db.models.MindMap` | N/A |
| `study_sessions` | Postgres table | `edu-shared` | `edu_shared.db.models.StudySession` | N/A |
| `practice_records` | Postgres table | `edu-shared` | `edu_shared.db.models.PracticeRecord` | N/A |
| `user_usage` | Postgres table | `edu-shared` | `edu_shared.db.models.UserUsage` | N/A |
| `QueueTaskMessage` | Queue message | `edu-shared` | `edu_shared.schemas.queue` | N/A |

## Detailed Schemas



### `DocumentSegment`

- **Purpose**: Stores searchable chunks and optional embeddings for RAG.
- **Storage**: Postgres table `document_segments`.
- **Key fields**:
  - `document_id`: FK to `documents`.

  - `content`: text chunk.
  - `embedding_vector`: pgvector `Vector(3072)` (nullable until embedded).



### `QueueTaskMessage`


- **Purpose**: Canonical async task envelope between `edu-api` producers and `edu-worker` consumers.
- **Storage**: Azure Storage Queue message (base64-encoded JSON payload).
- **Example**:

```json
{ "type": "document_processing", "data": { "document_id": "...", "project_id": "...", "user_id": "..." } }
```
