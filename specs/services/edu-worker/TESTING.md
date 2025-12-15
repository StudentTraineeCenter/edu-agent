# Service Testing Strategy

## Test Matrix
| Layer | Tools | Scope | Owner |
| --- | --- | --- | --- |
| Unit | (limited) | processor logic, schema validation | edu-worker |
| Integration | local docker-compose | queue + azurite + db | edu-worker |
| E2E | manual | upload document → processed segments present | edu-api + edu-worker |

## Scenarios
- Process a `DOCUMENT_PROCESSING` task and confirm `documents.status` changes and `document_segments` are created.
- Process a generation task and confirm target rows are updated (quiz questions, flashcards, notes, mind maps).

## Environments
- **Local**: `docker-compose up --build api worker db azurite`.
- **Dev Azure**: provisioned via Terraform.

## Quality Gates
- Python lint/format via ruff at repo level.
