# Service Security Notes

## Threat Model Snapshot
| Asset | Threat | Mitigation |
| --- | --- | --- |
| Supabase anon key | misuse | anon keys are intended to be public; rely on Supabase policies |
| User session token | XSS/token theft | avoid injecting untrusted HTML; use safe rendering; keep deps updated |
| API calls | leaking PII via logs | avoid logging document content and tokens in client console |

## Controls Checklist
- **Auth**: Supabase handles credential exchange; SPA uses `access_token` for API calls.
- **Secrets**: no private secrets in SPA.
- **Input handling**: validate/escape user-provided content in UI.

## Testing & Monitoring
- Run dependency audits and keep packages patched.

## Exceptions
- Dev-only assumptions; production-grade CSP and hardening not currently specified.
