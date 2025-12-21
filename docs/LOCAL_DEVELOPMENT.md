# Local Development Guide

This guide covers how to set up and run EduAgent locally for development.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Quick Start](#quick-start)
3. [Detailed Setup](#detailed-setup)
4. [Project Structure](#project-structure)
5. [Development Workflow](#development-workflow)
6. [Troubleshooting](#troubleshooting)
7. [Environment Variables Reference](#environment-variables-reference)

## Prerequisites

- Python 3.12+ (for server)
- Node.js 18+ and pnpm (for web frontend)
- Docker and Docker Compose (for PostgreSQL database)
- Azure credentials (for Azure services):
  - Azure OpenAI endpoint and API key
  - Azure Storage connection string
  - Azure Content Understanding endpoint and key
- Supabase credentials (for authentication):
  - Supabase project URL
  - Supabase anon key (for frontend)
  - Supabase service role key (for backend)
  - Supabase JWT secret (for backend)

## Quick Start

```bash
# 1. Start backend stack (API, worker, Postgres, Azurite)
docker-compose up --build api worker db azurite

# 2. Set up database schema (separate terminal, one-time)
# 2. Set up database schema (separate terminal, one-time)
uv run alembic upgrade head

# 3. Start web frontend (in a new terminal)
cd src/edu-web
pnpm install
pnpm dev
```

The application will be available at:

- API (via docker-compose): `http://localhost:8000`
- Web: `http://localhost:3000`

## Detailed Setup

### Step 1: Start Local Stack (API, Worker, DB, Azurite)

The application uses:

- PostgreSQL with pgvector (database)
- Azure Storage emulator (Azurite) for queues/blobs
- FastAPI API (`src/edu-api`)
- Background worker (`src/edu-worker`)

Start everything with Docker Compose:

```bash
docker-compose up --build api worker db azurite
```

Verify services are running:

```bash
docker-compose ps
```

You should see `api`, `worker`, `db`, and `azurite` containers.

### Step 2: Set Up Database Schema

Run database migrations to create the schema:

```bash
# Run Alembic migrations
uv run alembic upgrade head
```

This creates all necessary tables including:

- Users
- Projects
- Documents and Document Segments
- Chats
- Quizzes and Quiz Questions
- Flashcard Groups and Flashcards
- Study Attempts
- User Usage

### Step 3: Configure Server Environment

The application supports two configuration modes:

#### Option 1: Azure Key Vault (Production)

For production deployments, configure Azure Key Vault and set only:

```bash
# Azure Key Vault (required)
AZURE_KEY_VAULT_URI=https://your-key-vault.vault.azure.net/

# Usage Limits (optional, defaults shown)
MAX_CHAT_MESSAGES_PER_DAY=100
MAX_FLASHCARD_GENERATIONS_PER_DAY=100
MAX_QUIZ_GENERATIONS_PER_DAY=100
MAX_DOCUMENT_UPLOADS_PER_DAY=100
```

All other Azure service credentials are automatically retrieved from Key Vault using these secret names:

- `database-url`
- `azure-openai-api-key`
- `azure-openai-endpoint`
- `azure-openai-default-model`
- `azure-openai-chat-deployment`
- `azure-openai-embedding-deployment`
- `azure-openai-api-version`
- `azure-storage-connection-string`
- `azure-storage-input-container-name`
- `azure-storage-output-container-name`
- `azure-document-intelligence-endpoint`
- `azure-document-intelligence-key`
- `azure-cu-endpoint`
- `azure-cu-key`
- `azure-cu-analyzer-id`
- `supabase-url`
- `supabase-service-role-key`
- `supabase-jwt-secret`

#### Option 2: Environment Variables (Local Development)

For local development, you can set individual environment variables instead of using Key Vault:

```bash
# Database
DATABASE_URL=postgresql+psycopg2://postgres:postgres@localhost:5432/postgres

# Azure OpenAI (required)
AZURE_OPENAI_ENDPOINT=https://your-openai-endpoint.openai.azure.com/
AZURE_OPENAI_API_KEY=your-api-key
AZURE_OPENAI_DEFAULT_MODEL=gpt-4o
AZURE_OPENAI_EMBEDDING_DEPLOYMENT=text-embedding-3-large
AZURE_OPENAI_CHAT_DEPLOYMENT=gpt-4o
AZURE_OPENAI_API_VERSION=2024-06-01

# Azure Storage (required)
AZURE_STORAGE_CONNECTION_STRING=DefaultEndpointsProtocol=https;AccountName=...
AZURE_STORAGE_INPUT_CONTAINER_NAME=input
AZURE_STORAGE_OUTPUT_CONTAINER_NAME=output

# Azure Content Understanding (required)
AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT=https://your-cu-endpoint.cognitiveservices.azure.com/
AZURE_DOCUMENT_INTELLIGENCE_KEY=your-cu-key
AZURE_CU_ENDPOINT=https://your-cu-endpoint.cognitiveservices.azure.com/
AZURE_CU_KEY=your-cu-key
AZURE_CU_ANALYZER_ID=prebuilt-documentAnalyzer

# Supabase (required)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
SUPABASE_JWT_SECRET=your-jwt-secret

# Usage Limits (optional, defaults shown)
MAX_CHAT_MESSAGES_PER_DAY=100
MAX_FLASHCARD_GENERATIONS_PER_DAY=100
MAX_QUIZ_GENERATIONS_PER_DAY=100
MAX_DOCUMENT_UPLOADS_PER_DAY=100
```

**Note:** The server uses `python-dotenv` to load environment variables from `.env` files automatically. If `AZURE_KEY_VAULT_URI` is set, the application will attempt to fetch secrets from Key Vault first, falling back to environment variables if a secret is not found.

### Step 4: Start the API Server (without Docker, optional)

If you prefer to run the API directly (outside Docker):

```bash
uv run --package edu-api python src/edu-api/main.py
```

The API will be available at `http://localhost:8000`.

**API Endpoints:**

- Scalar UI (OpenAPI docs): `http://localhost:8000/`
- OpenAPI schema: `http://localhost:8000/openapi.json`
- Health check: `http://localhost:8000/health`

### Step 5: Set Up Web Frontend

```bash
cd src/edu-web

# Install dependencies
pnpm install

# Create .env file or set environment variables
cat > .env << EOF
VITE_SERVER_URL=http://localhost:8000
VITE_SUPABASE_URL=https://your-project.supabase.co
VITE_SUPABASE_ANON_KEY=your-anon-key
EOF

# Start development server
pnpm dev
```

The web application will be available at `http://localhost:3000`

The development server includes:

- Hot Module Replacement (HMR) for instant updates
- Fast refresh for React components
- Source maps for debugging

### Step 6: Generate TypeScript Types (Optional)

To generate TypeScript types from the OpenAPI schema:

```bash
cd web

# Make sure API server is running on localhost:8000
pnpm gen:types
```

This generates types from `http://localhost:8000/openapi.json` to `src/integrations/api/types.ts`

**Note:** Run this whenever the API schema changes to keep types in sync.

## Project Structure

```
edu-agent/
├── src/
│   ├── edu-api/        # FastAPI backend (public API)
│   ├── edu-worker/     # Background worker (queue/AI processing)
│   ├── edu-web/        # React frontend (Vite + TanStack)
│   ├── shared/         # Shared models, DB session, Key Vault helpers, etc.
│   └── eduagent-vibecode/
├── deploy/             # Deployment configurations
├── docker-compose.yaml # Local stack (api, worker, db, azurite)
└── docs/               # Documentation
```

## Development Workflow

### Making Changes

1. **Backend Changes:**

   - Primary API: edit Python files in `src/edu-api/`
   - Worker: edit Python files in `src/edu-worker/`
   - Run migrations if database schema changes: `alembic revision --autogenerate -m "description"`

2. **Frontend Changes:**

   - Edit TypeScript/React files in `src/edu-web/src/`
   - Changes are hot-reloaded automatically
   - Regenerate types if API changes: `pnpm gen:types`

3. **Database Changes:**

   - Modify models in `src/shared/db/src/edu_db/models.py`
   - Generate migration: `uv run alembic revision --autogenerate -m "description"`
   - Apply migration: `uv run alembic upgrade head`

### Running Tests

```bash
# Backend tests (if available)
cd server
pytest

# Frontend tests
cd web
pnpm test
```

### Code Formatting

```bash
# Backend (using ruff)
cd server
ruff format .
ruff check .

# Frontend
cd web
pnpm format
pnpm lint
```

## Troubleshooting

### Database Issues

**Database connection failed**

- Verify Docker container is running: `docker-compose ps`
- Check database credentials in `.env`
- Verify port 5432 is not in use by another service
- Check database logs: `docker-compose logs db`

**Migration errors**

- Ensure database is running
- Check migration files are up to date: `alembic current`
- Try downgrading and upgrading: `alembic downgrade -1 && alembic upgrade head`

### API Server Issues

**API server won't start**

- Check all required environment variables are set
- Verify Python version: `python --version` (should be 3.11+)
- Check dependencies: `pip install -r requirements.txt`
- Check for port conflicts: `lsof -i :8000`

**Import errors**

- Ensure virtual environment is activated
- Reinstall dependencies: `pip install -r requirements.txt --force-reinstall`
- Check Python path: `which python`

**Azure service errors**

- Verify Azure credentials are correct
- Check network connectivity
- Verify service endpoints are correct
- Ensure you have proper Azure permissions

### Web Frontend Issues

**Web frontend won't start**

- Verify Node.js version: `node --version` (should be 18+)
- Install dependencies: `pnpm install`
- Check environment variables in `.env`
- Check for port conflicts: `lsof -i :3000`

**API connection errors**

- Verify API server is running on `http://localhost:8000`
- Check `VITE_SERVER_URL` in `.env` matches API server URL
- Check browser console for CORS errors
- Verify API server CORS configuration

**Type errors**

- Regenerate types: `pnpm gen:types`
- Ensure API server is running when generating types
- Check TypeScript version compatibility

### Docker Issues

**Docker container won't start**

- Check Docker is running: `docker ps`
- Check container logs: `docker-compose logs db`
- Verify docker-compose.yaml syntax
- Try rebuilding: `docker-compose up -d --build db`

**Port already in use**

- Find process using port: `lsof -i :5432` (or `:8000`, `:3000`)
- Stop conflicting service or change port in configuration

## Environment Variables Reference

### Server (API) Environment Variables

The application uses Azure Key Vault for secure credential management. In production, only the Key Vault URI and usage limits need to be set as environment variables. All other credentials are retrieved from Key Vault.

#### Required Environment Variables (Production)

| Variable                            | Description                 | Required | Default |
| ----------------------------------- | --------------------------- | -------- | ------- |
| `AZURE_KEY_VAULT_URI`               | Azure Key Vault URI         | Yes\*    | -       |
| `MAX_CHAT_MESSAGES_PER_DAY`         | Daily chat message limit    | No       | 100     |
| `MAX_FLASHCARD_GENERATIONS_PER_DAY` | Daily flashcard limit       | No       | 100     |
| `MAX_QUIZ_GENERATIONS_PER_DAY`      | Daily quiz limit            | No       | 100     |
| `MAX_DOCUMENT_UPLOADS_PER_DAY`      | Daily document upload limit | No       | 100     |

\* Required for production. For local development, you can set individual environment variables instead.

#### Key Vault Secret Names

When using Key Vault, the following secrets are expected:

| Secret Name                            | Description                     |
| -------------------------------------- | ------------------------------- |
| `database-url`                         | PostgreSQL connection string    |
| `azure-openai-api-key`                 | Azure OpenAI API key            |
| `azure-openai-endpoint`                | Azure OpenAI endpoint URL       |
| `azure-openai-default-model`           | Default OpenAI model            |
| `azure-openai-chat-deployment`         | Chat model deployment name      |
| `azure-openai-embedding-deployment`    | Embedding model deployment      |
| `azure-openai-api-version`             | OpenAI API version              |
| `azure-storage-connection-string`      | Azure Storage connection string |
| `azure-storage-input-container-name`   | Input blob container name       |
| `azure-storage-output-container-name`  | Output blob container name      |
| `azure-document-intelligence-endpoint` | Document Intelligence endpoint  |
| `azure-document-intelligence-key`      | Document Intelligence API key   |
| `azure-cu-endpoint`                    | Content Understanding endpoint  |
| `azure-cu-key`                         | Content Understanding API key   |
| `azure-cu-analyzer-id`                 | Content Understanding analyzer  |
| `supabase-url`                         | Supabase project URL            |
| `supabase-service-role-key`            | Supabase service role key       |
| `supabase-jwt-secret`                  | Supabase JWT secret             |

#### Local Development Environment Variables

For local development (when Key Vault is not used), you can set these environment variables directly:

| Variable                               | Description                     | Required | Default                   |
| -------------------------------------- | ------------------------------- | -------- | ------------------------- |
| `DATABASE_URL`                         | PostgreSQL connection string    | Yes      | -                         |
| `AZURE_OPENAI_ENDPOINT`                | Azure OpenAI endpoint URL       | Yes      | -                         |
| `AZURE_OPENAI_API_KEY`                 | Azure OpenAI API key            | Yes      | -                         |
| `AZURE_OPENAI_DEFAULT_MODEL`           | Default OpenAI model            | No       | gpt-4o                    |
| `AZURE_OPENAI_CHAT_DEPLOYMENT`         | Chat model deployment name      | Yes      | -                         |
| `AZURE_OPENAI_EMBEDDING_DEPLOYMENT`    | Embedding model deployment      | Yes      | -                         |
| `AZURE_OPENAI_API_VERSION`             | OpenAI API version              | No       | 2024-06-01                |
| `AZURE_STORAGE_CONNECTION_STRING`      | Azure Storage connection string | Yes      | -                         |
| `AZURE_STORAGE_INPUT_CONTAINER_NAME`   | Input blob container name       | No       | input                     |
| `AZURE_STORAGE_OUTPUT_CONTAINER_NAME`  | Output blob container name      | No       | output                    |
| `AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT` | Document Intelligence endpoint  | Yes      | -                         |
| `AZURE_DOCUMENT_INTELLIGENCE_KEY`      | Document Intelligence API key   | Yes      | -                         |
| `AZURE_CU_ENDPOINT`                    | Content Understanding endpoint  | Yes      | -                         |
| `AZURE_CU_KEY`                         | Content Understanding API key   | Yes      | -                         |
| `AZURE_CU_ANALYZER_ID`                 | Content Understanding analyzer  | No       | prebuilt-documentAnalyzer |
| `SUPABASE_URL`                         | Supabase project URL            | Yes      | -                         |
| `SUPABASE_SERVICE_ROLE_KEY`            | Supabase service role key       | Yes      | -                         |
| `SUPABASE_JWT_SECRET`                  | Supabase JWT secret             | Yes      | -                         |

### Web Frontend Environment Variables

| Variable                 | Description          | Required |
| ------------------------ | -------------------- | -------- |
| `VITE_SERVER_URL`        | API server URL       | Yes      |
| `VITE_SUPABASE_URL`      | Supabase project URL | Yes      |
| `VITE_SUPABASE_ANON_KEY` | Supabase anon key    | Yes      |

**Note:** All `VITE_*` variables are exposed to the browser. Do not include sensitive information.

**Note:** All `VITE_*` variables are exposed to the browser. Do not include sensitive information.

## Additional Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [React Documentation](https://react.dev/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [Alembic Documentation](https://alembic.sqlalchemy.org/)
- [Vite Documentation](https://vitejs.dev/)

## Support

For issues or questions:

- Check application logs
- Review error messages in browser console (for frontend)
- Check server logs (for backend)
- Contact: richard.amare@studentstc.cz
