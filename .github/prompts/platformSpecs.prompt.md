Based on user input create platform specifications for whole project in folder `specs/platform/` using following templates #tool:fetch :
- Architecture: https://raw.githubusercontent.com/tkubica12/gh-copilot-constitution/refs/heads/main/specs-template/platform/ARCHITECTURE.md
- Data models: https://raw.githubusercontent.com/tkubica12/gh-copilot-constitution/refs/heads/main/specs-template/platform/DATA_MODELS.md
- Deployment: https://raw.githubusercontent.com/tkubica12/gh-copilot-constitution/refs/heads/main/specs-template/platform/DEPLOYMENT.md
- Security: https://raw.githubusercontent.com/tkubica12/gh-copilot-constitution/refs/heads/main/specs-template/platform/SECURITY.md
- Observability: https://raw.githubusercontent.com/tkubica12/gh-copilot-constitution/refs/heads/main/specs-template/platform/OBSERVABILITY.md
- Testing: https://raw.githubusercontent.com/tkubica12/gh-copilot-constitution/refs/heads/main/specs-template/platform/TESTING.md

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