# Shared Library Public Surface

This document captures the intended stable surface of `edu-shared` as consumed by `edu-api` and `edu-worker`.

## Source of Truth
- Package root: `src/edu-shared/src/edu_shared/`

## Intended stable modules
- `edu_shared.db.*`
  - `edu_shared.db.models` (SQLAlchemy ORM models)
  - `edu_shared.db.session` (`init_db`, `get_db`, session factory)
- `edu_shared.schemas.*`
  - DTOs used by API responses and worker task payloads
  - `edu_shared.schemas.queue` is the canonical async task contract
- `edu_shared.services.*`
  - Domain services (projects, documents, chats, quizzes, flashcards, notes, mind maps, search, usage)
- `edu_shared.exceptions`
  - Shared exception types used by API exception handlers
- `edu_shared.keyvault`
  - Key Vault helpers and `KeyVaultSettingsSource`

## Compatibility expectations
- Changes to `edu_shared.db.models` and `edu_shared.schemas.queue` should be treated as breaking unless both `edu-api` and `edu-worker` are updated in lockstep.
