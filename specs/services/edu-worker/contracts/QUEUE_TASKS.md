# Queue Task Contract

`edu-worker` consumes Azure Storage Queue messages produced by `edu-api`.

## Transport
- **Queue**: Azure Storage Queue (dev may use Azurite).
- **Encoding**: JSON payload is Base64 encoded before enqueue.

## Schema
Source of truth: `src/edu-shared/src/edu_shared/schemas/queue.py`.

### Envelope
```json
{
  "type": "flashcard_generation",
  "data": { /* typed per task */ }
}
```

### Task types
- `flashcard_generation`
- `quiz_generation`
- `note_generation`
- `mind_map_generation`
- `document_processing`
- `chat_title_generation`

### Example: document processing
```json
{
  "type": "document_processing",
  "data": {
    "document_id": "<uuid>",
    "project_id": "<uuid>",
    "user_id": "<uuid>"
  }
}
```

### Example: chat title generation
```json
{
  "type": "chat_title_generation",
  "data": {
    "chat_id": "<uuid>",
    "project_id": "<uuid>",
    "user_id": "<uuid>",
    "user_message": "...",
    "ai_response": "..."
  }
}
```

## Compatibility notes
- Delivery is at-least-once; consumers must tolerate duplicates.
- Payload ids must reference existing DB rows where required (e.g. `quiz_id`, `group_id`, `note_id`).
