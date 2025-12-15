# Service Runbooks

Operational procedures for `edu-web`.

## On-Call Quick Reference
- Local dev server: `pnpm dev` (port 3000)
- Requires API: `http://localhost:8000`

## Common Incidents

### SPA fails to start (env errors)
**Symptoms**:
- App crashes on startup due to missing env vars.

**Diagnosis**:
- Check `VITE_SERVER_URL`, `VITE_SUPABASE_URL`, `VITE_SUPABASE_ANON_KEY`.

**Mitigation**:
- Create/update `src/edu-web/.env`.

### API calls return 401
**Symptoms**:
- UI shows unauthorized errors.

**Diagnosis**:
- Verify user is signed in and session exists.
- Confirm API expects Supabase access token.

**Mitigation**:
- Sign out/in.
- Ensure API has correct `supabase_jwt_secret` configured.

### OpenAPI client generation fails
**Symptoms**:
- `pnpm gen:client` fails.

**Diagnosis**:
- Ensure API is running at `localhost:8000` and `GET /openapi.json` returns 200.

**Mitigation**:
- Start API (`docker-compose up api db azurite`).

## Maintenance Tasks

### Update generated API client
- From `src/edu-web`: run `pnpm gen:client`.
