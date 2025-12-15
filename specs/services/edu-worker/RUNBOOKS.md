# Service Runbooks

Operational procedures for `edu-worker`.

## On-Call Quick Reference
- **Queue name**: defaults to `ai-generation-tasks`.
- **Local stack**: `docker-compose up --build api worker db azurite`.

## Common Incidents

### Queue backlog growing
**Symptoms**:
- Messages accumulate; generation/document processing slow.

**Diagnosis**:
- Check worker logs for errors.
- Check Azure AI dependency throttling.
- Confirm DB is reachable.

**Mitigation**:
- Increase worker replicas (Container Apps scale) in dev if supported.
- Reduce concurrency if hitting rate limits.

### Poison message / repeated failures
**Symptoms**:
- Same message reprocessed repeatedly.

**Diagnosis**:
- Identify task type and payload fields from logs.
- Validate referenced DB IDs exist.

**Mitigation**:
- Fix underlying data issue and re-enqueue a corrected message.
- Consider adding dead-lettering strategy (future improvement).

### Document processing fails
**Symptoms**:
- Document stays `failed`.

**Diagnosis**:
- Verify CU analyzer id and keys.
- Check blob exists in `input` container.

**Mitigation**:
- Restore missing blobs.
- Re-enqueue `DOCUMENT_PROCESSING` after fixing credentials.

## Maintenance Tasks

### Rotating secrets (dev)
1. Update Key Vault secrets.
2. Restart worker revision.
