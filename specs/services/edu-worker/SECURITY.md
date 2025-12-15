# Service Security Notes

## Threat Model Snapshot
| Asset | Threat | Mitigation |
| --- | --- | --- |
| Queue messages | spoofing / tampering | restrict access to storage account; keep connection string in Key Vault |
| Document blobs | data exposure | private containers; RBAC and secret management |
| Azure AI credentials | cost/abuse | managed identity where possible; Key Vault for secrets |
| DB writes | injection / corruption | ORM parameterization; validate payload types |

## Controls Checklist
- **Authentication/authorization**: no end-user auth; relies on infra-level auth (connection strings / managed identity).
- **Secrets**: Key Vault settings source; avoid hard-coded secrets.
- **Data handling**: avoid logging raw extracted document contents.

## Testing & Monitoring
- Alert on repeated processing failures of the same message.
- Monitor queue backlog growth.

## Exceptions
- At-least-once queue delivery means tasks may run more than once.
