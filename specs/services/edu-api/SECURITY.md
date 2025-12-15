# Service Security Notes

Aligns with dev-only environment assumptions; secrets should come from Key Vault in Azure.

## Threat Model Snapshot
| Asset | Threat | Mitigation |
| --- | --- | --- |
| Supabase JWT secret | Secret leakage → auth bypass | Store in Key Vault, restrict RBAC, avoid committing secrets |
| User data (projects/docs/chats) | Unauthorized access | JWT validation; scope queries by `user_id`/ownership in services |
| Document files in Blob | Data exposure | Use private containers; store only blob names in DB; RBAC/connection string secret |
| Azure OpenAI usage | Abuse / cost blowup | Per-user usage limits; backend-controlled prompt/tooling |

## Controls Checklist
- **Authentication/authorization**
  - Bearer token auth; JWT decoded with HS256 and `audience="authenticated"`.
  - User identity derived from `sub` claim.
- **Secrets handling**
  - Settings load from Key Vault settings source; local `.env` supported.
- **Data classification & encryption**
  - TLS for HTTP.
  - At-rest encryption is provided by managed services (Postgres/Storage/Key Vault).
- **Input validation**
  - Pydantic validation + explicit file type allow-list for uploads.

## Testing & Monitoring
- Monitor auth failures (401) and rate limit responses (429).
- Track spikes in `/documents/upload` and generation endpoints.

## Exceptions
- Dev-only: CORS is currently wide open (`allow_origins=["*"]`). Tighten before any multi-tenant/public exposure.
