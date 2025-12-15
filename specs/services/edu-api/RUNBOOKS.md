# Service Runbooks

This document contains dev-ops procedures for `edu-api`.

## On-Call Quick Reference
- **Health endpoint**: `GET /health`
- **OpenAPI**: `GET /openapi.json`
- **Local stack**: `docker-compose up --build api worker db azurite`

## Common Incidents

### 401 Authentication failures
**Symptoms**:
- Many 401 responses.

**Diagnosis**:
- Verify `supabase_jwt_secret` is configured (Key Vault / env).
- Confirm client sends `Authorization: Bearer <token>`.

**Mitigation**:
- Restore secret in Key Vault.
- Restart API container app.

### 429 Usage limit exceeded
**Symptoms**:
- Requests fail with 429.

**Diagnosis**:
- Inspect usage counters in DB (`user_usage`).
- Confirm configured limits in settings.

**Mitigation**:
- Increase limits for dev or reset usage data for test users.

### Document upload succeeds but never processes
**Symptoms**:
- `documents.status` stays `uploaded`.

**Diagnosis**:
- Check Storage Queue has messages.
- Check `edu-worker` logs for processing errors.
- Verify Azurite/Azure Storage connectivity.

**Mitigation**:
- Restart worker.
- Re-enqueue processing task if needed.

## Maintenance Tasks

### Rotating secrets (dev)
1. Update Key Vault secret value.
2. Restart `edu-api` container app revision.

### Rebuilding OpenAPI client (frontend)
- Run `pnpm gen:client` in `src/edu-web` while API is running locally.
