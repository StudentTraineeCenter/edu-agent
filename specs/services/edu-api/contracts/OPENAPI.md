# OpenAPI Contract (Runtime)

`edu-api` exposes an OpenAPI schema at runtime.

## Source of Truth
- Local dev: `http://localhost:8000/openapi.json`
- The API root `/` serves Scalar UI pointing at that OpenAPI URL.

## How to use
### Frontend client generation
The frontend includes a script that pulls `openapi.json` from the running API and generates a typed client:
- Script: `src/edu-web/package.json` → `gen:client`

Example (run from `src/edu-web`):
```bash
pnpm gen:client
```

## Auth
- Most endpoints require `Authorization: Bearer <supabase_access_token>`.

## Error format
Most error responses follow:
```json
{ "error": { "message": "...", "status_code": 400 } }
```
Validation errors may include an additional `details` array.
