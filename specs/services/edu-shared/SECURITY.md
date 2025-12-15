# Service Security Notes

This document covers security considerations unique to `edu-shared`.

## Threat Model Snapshot
| Asset | Threat | Mitigation |
| --- | --- | --- |
| Key Vault secrets | Unauthorized secret reads | Use managed identity (DefaultAzureCredential) + RBAC; do not embed secrets in code |
| DB credentials | Leakage in logs | Avoid logging connection strings; treat DB URL as secret |
| Queue payloads | Spoofed/invalid task payloads | Validate required ids exist before processing; tolerate duplicates (at-least-once delivery) |

## Controls Checklist
- **Authentication/authorization**: delegated to host services (`edu-api` verifies Supabase JWT). `edu-shared` only provides utilities.
- **Secrets handling**:
  - `KeyVaultSettingsSource` maps setting names from snake_case to Key Vault secret names (dash-case).
  - Falls back to env vars if Key Vault access fails.
- **Data classification**: DB rows and documents may contain user-provided educational content; avoid logging raw content.

## Testing & Monitoring
- Recommend adding unit tests for settings/secret name mapping and queue schema examples.

## Exceptions
None documented.
