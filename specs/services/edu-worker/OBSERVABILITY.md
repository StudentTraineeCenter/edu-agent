# Service Observability Plan

## Metrics
| Metric | Purpose | Target | Dashboard |
| --- | --- | --- | --- |
| `queue.messages.received` | workload volume | N/A | Log Analytics |
| `queue.message.processing.duration` | latency per task | N/A | Log Analytics |
| `queue.message.failures` | error rate | low | Log Analytics |
| `queue.backlog.depth` | capacity planning | stable | Azure Storage metrics |

## Logs
- Current output uses `rich.console` plus some standard logging.
- Include fields where possible: `task_type`, `project_id`, `document_id`, `chat_id`.

## Traces
- Consider OpenTelemetry for calls to Azure AI + DB operations if needed.

## Alerts
| Alert | Condition | Severity | Channel | Runbook |
| --- | --- | --- | --- | --- |
| Queue backlog growing | depth increasing for N minutes | Medium | Dev ops | `RUNBOOKS.md` |
| Repeated task failures | same message fails repeatedly | High | Dev ops | `RUNBOOKS.md` |

## Specification by Example
- Given backlog increases while CPU is low, inspect Azure AI dependency throttling or DB latency.
