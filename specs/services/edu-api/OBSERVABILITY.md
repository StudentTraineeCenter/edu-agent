# Service Observability Plan

## Metrics
| Metric | Purpose | Target | Dashboard |
| --- | --- | --- | --- |
| `http.server.request.count` | request volume | N/A | App Insights |
| `http.server.duration` | latency tracking | N/A | App Insights |
| `http.responses.4xx/5xx` | error rates | low | App Insights |
| `usage.limit_exceeded.count` | quota enforcement | N/A | Custom query |

## Logs
- **Format**: Python logging + some `rich.console` output.
- **PII rules**: avoid logging raw document content, tokens, or full JWTs.
- **Key fields**: method/path/status_code/user_id (if available), exception type.

## Traces
- Recommend enabling OpenTelemetry instrumentation for FastAPI + SQLAlchemy if/when needed.

## Alerts
| Alert | Condition | Severity | Channel | Runbook |
| --- | --- | --- | --- | --- |
| High 5xx rate | 5xx > threshold | High | Dev ops | `../edu-api/RUNBOOKS.md` |
| Queue backlog | visible messages increasing | Medium | Dev ops | `../edu-worker/RUNBOOKS.md` |

## Specification by Example
- Given sustained 429s on generation endpoints, investigate `UsageService` limits and client retry behavior.
