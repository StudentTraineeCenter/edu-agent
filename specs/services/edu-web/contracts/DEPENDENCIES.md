# External Contracts

## edu-api
- **Base URL**: `VITE_SERVER_URL`
- **Schema**: runtime OpenAPI at `http://localhost:8000/openapi.json` for local dev.
- **Auth**: `Authorization: Bearer <supabase_access_token>`.
- **Client generation**: `pnpm gen:client` regenerates `src/integrations/api/client.ts`.

## Supabase Auth
- **Client**: `@supabase/supabase-js`.
- **Config**: `VITE_SUPABASE_URL`, `VITE_SUPABASE_ANON_KEY`.
- **Token source**: `supabase.auth.getSession()` → `session.access_token`.
