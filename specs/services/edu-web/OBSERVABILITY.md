# Service Observability Plan

## Metrics
| Metric | Purpose | Target | Dashboard |
| --- | --- | --- | --- |
| page load time | UX health | N/A | Browser tooling |
| API error rate (client-side) | detect regressions | low | Console / optional tooling |

## Logs
- Primary logs are browser console logs.
- Avoid logging tokens, extracted document content, or PII.

## Traces
- Not configured by default.

## Alerts
| Alert | Condition | Severity | Channel | Runbook |
| --- | --- | --- | --- | --- |
| SPA cannot reach API | repeated network errors | Medium | Dev ops | `RUNBOOKS.md` |

## Specification by Example
- Given users report blank pages, verify env vars and API reachability.
