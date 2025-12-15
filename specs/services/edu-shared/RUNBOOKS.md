# Service Runbooks

This document contains operational procedures relevant to code shipped via `edu-shared`.

## On-Call Quick Reference
- **Primary logs**: `edu-api` / `edu-worker` logs (this package does not run standalone).
- **Primary dashboards**: Application Insights / Log Analytics tied to the running services.

## Common Incidents

### Startup failure: "Database not initialized"
**Symptoms**:
- API/worker crashes with `RuntimeError: Database not initialized. You must call 'init_db(url)' on startup.`

**Diagnosis**:
- Confirm host service calls `edu_shared.db.session.init_db()` during startup/lifespan.

**Mitigation**:
- Add/fix startup initialization in the host service.

### Key Vault not reachable / secrets missing
**Symptoms**:
- Host service logs indicate missing configuration (e.g. DB URL, OpenAI endpoint).

**Diagnosis**:
- Check managed identity permissions and `AZURE_KEY_VAULT_URI` (and/or any configured Key Vault URI used by settings).

**Mitigation**:
- Ensure RBAC allows secret reads.
- For local dev, provide values via `.env`.

## Maintenance Tasks

### Updating shared contracts safely
1. If changing DB models: create Alembic migration and verify both `edu-api` and `edu-worker` remain compatible.
2. If changing queue message schemas: update producers and consumers together; keep backward compatibility when possible.
