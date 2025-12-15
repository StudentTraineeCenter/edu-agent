# Service Specs

Based on user input create service specifications `specs/services/,servicename.` using following templates #tool:fetch :

- Architecture: <https://raw.githubusercontent.com/tkubica12/gh-copilot-constitution/refs/heads/main/specs-template/services/service-sample/ARCHITECTURE.md>
- Data models: <https://raw.githubusercontent.com/tkubica12/gh-copilot-constitution/refs/heads/main/specs-template/services/service-sample/DATA_MODELS.md>
- Deployment: <https://raw.githubusercontent.com/tkubica12/gh-copilot-constitution/refs/heads/main/specs-template/services/service-sample/DEPLOYMENT.md>
- Security: <https://raw.githubusercontent.com/tkubica12/gh-copilot-constitution/refs/heads/main/specs-template/services/service-sample/SECURITY.md>
- Observability: <https://raw.githubusercontent.com/tkubica12/gh-copilot-constitution/refs/heads/main/specs-template/services/service-sample/OBSERVABILITY.md>
- Testing: <https://raw.githubusercontent.com/tkubica12/gh-copilot-constitution/refs/heads/main/specs-template/services/service-sample/TESTING.md>
- Runbooks: <https://raw.githubusercontent.com/tkubica12/gh-copilot-constitution/refs/heads/main/specs-template/services/service-sample/RUNBOOKS.md>

There will also be `contracts` folder created with contract specifications (depenging on what interface service uses - OpenAPI spec, gRPC spec, Async API spec, messages/consumers schemas, event schemas, etc.)

If clarification is needed, ask user questions before creating the specifications. Use following format:

```
Q1: <question 1>
Q2: <question 2>
...
```

Expect user to answer in format:

```
Q1: <answer 1>
Q2: <answer 2>
...
```

Iterate until all needed information is gathered and specs can be created.
