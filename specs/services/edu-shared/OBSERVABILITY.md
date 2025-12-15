# Service Observability Plan

`edu-shared` provides logging and shared primitives used by `edu-api` and `edu-worker`.

## Metrics
| Metric | Purpose | Target | Dashboard |
| --- | --- | --- | --- |
| N/A | Library-only | N/A | N/A |

## Logs
- Shared code should emit structured logs at appropriate levels and avoid logging secrets or full document contents.
- Prefer logging identifiers (`project_id`, `document_id`, `task_type`) over payload bodies.

## Traces
- No direct tracing instrumentation is defined in this package.

## Alerts
| Alert | Condition | Severity | Channel | Runbook |
| --- | --- | --- | --- | --- |
| N/A | Library-only | N/A | N/A | N/A |

## Specification by Example
- Given Key Vault is unavailable, settings fall back to env vars and the host service continues to start (where env vars are present).
