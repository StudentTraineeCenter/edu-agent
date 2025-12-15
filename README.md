# EduAgent

<div align="center">

**AI-powered educational platform for creating interactive learning experiences**

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.7+-blue.svg)](https://www.typescriptlang.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.117+-green.svg)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-19-blue.svg)](https://react.dev/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

[Features](#-features) • [Quick Start](#-quick-start) • [Documentation](#-documentation) • [Contributing](#-contributing)

</div>

---

EduAgent helps students study course materials through intelligent document processing, interactive AI chat, and automatically generated study aids. Upload your documents, chat with an AI tutor, and get personalized quizzes and flashcards—all powered by Azure AI services.

## Table of Contents

- [Features](#-features)
- [Tech Stack](#-tech-stack)
- [Prerequisites](#-prerequisites)
- [Quick Start](#-quick-start)
- [Installation](#-installation)
- [Configuration](#-configuration)
- [Project Structure](#-project-structure)
- [Development](#-development)
- [API Documentation](#-api-documentation)
- [Documentation](#-documentation)
- [Contributing](#-contributing)
- [License](#-license)
- [Support](#-support)

## ✨ Features

- **📂 Project-Based Workspaces** - Organize everything into projects that group documents, chats, quizzes, flashcards, notes, mind maps, and practice history
- **📄 Document Pipeline** - Upload PDF, DOCX, TXT, and RTF, process them via Azure Content Understanding, and chunk + embed them into PostgreSQL pgvector
- **🔍 RAG-Powered Semantic Search** - Query your own materials with vector search and filtering by project/document
- **💬 AI Chat Tutor** - Chat with an AI that uses RAG over your project documents and can call tools for quizzes, flashcards, notes, and more
- **📝 Auto-Generated Quizzes** - Generate and regenerate MCQ quizzes from any project or document with answer checking and attempt tracking
- **🎴 Smart Flashcards** - Create flashcard groups from documents or quizzes, with simple progress tracking per flashcard
- **📝 AI-Generated Notes** - Turn dense readings into structured summaries and study notes per project/document
- **🗺️ Mind Maps** - Build AI-generated concept maps that visualize the relationships inside a project’s materials
- **🎯 Adaptive Practice Sessions** - Run study sessions that mix flashcards and quizzes, with practice records and basic analytics
- **🔐 Supabase Auth + Usage Limits** - Supabase-backed authentication with per-user daily limits for chats, generations, and uploads

## 🏗️ Tech Stack

### Backend

- **[FastAPI](https://fastapi.tiangolo.com/)** - Modern, fast Python web framework
- **[PostgreSQL](https://www.postgresql.org/)** - Relational database with Alembic migrations and pgvector extension
- **[Azure OpenAI](https://azure.microsoft.com/en-us/products/ai-services/openai-service)** - LLM capabilities for chat, quizzes, flashcards, notes, mind maps, and study plans
- **[Azure Content Understanding](https://azure.microsoft.com/en-us/products/ai-services/document-intelligence)** - Document processing and text extraction
- **[Azure Blob Storage](https://azure.microsoft.com/en-us/products/storage/blobs)** - File storage
- **[Supabase](https://supabase.com/)** - Authentication and authorization

### Frontend

- **[React 19](https://react.dev/)** - UI library
- **[TypeScript](https://www.typescriptlang.org/)** - Type safety
- **[Vite](https://vitejs.dev/)** - Build tool and dev server
- **[TanStack Router](https://tanstack.com/router)** - Type-safe routing
- **[TanStack Query](https://tanstack.com/query)** - Data fetching and caching
- **[TailwindCSS](https://tailwindcss.com/)** - Utility-first CSS framework
- **[Radix UI](https://www.radix-ui.com/)** - Accessible component primitives

## 📋 Prerequisites

Before you begin, ensure you have the following installed:

- **Python 3.12+** - [Download Python](https://www.python.org/downloads/)
- **Node.js 18+** - [Download Node.js](https://nodejs.org/)
- **pnpm** - `npm install -g pnpm`
- **Docker & Docker Compose** - [Install Docker](https://docs.docker.com/get-docker/)
- **Terraform** - [Install Terraform](https://developer.hashicorp.com/terraform/install)
- **Azure and Supabase** - Provisioned via Terraform:
  - Terraform modules will set up:
    - Azure OpenAI
    - Azure Content Understanding (AI Foundry)
    - Azure Blob Storage
    - Supabase project with authentication enabled
  - See [infrastructure documentation](docs/AZURE_DEPLOYMENT.md) for setup instructions

## 🚀 Quick Start

Get EduAgent running locally using Docker for the backend and Vite for the frontend:

```bash
# Clone the repository
git clone https://github.com/StudentTraineeCenter/edu-agent.git
cd edu-agent

# Start backend stack (API, worker, Postgres, Azurite)
docker-compose up --build api worker db azurite

# In a separate terminal, run DB migrations (one-time)
# Make sure DATABASE_URL is set correctly for your local Postgres
export DATABASE_URL="postgresql+psycopg2://postgres:postgres@localhost:5432/postgres"
alembic upgrade head

# In a new terminal, start the web frontend
cd src/edu-web
pnpm install
pnpm dev
```

Visit `http://localhost:3000` for the web app and `http://localhost:8000` for the API.

## 📦 Installation

### Backend Setup (API + Worker)

The Python services use a **uv workspace** with `pyproject.toml` + `uv.lock`.

```bash
cd edu-agent

# Install uv if you don't have it yet (see https://docs.astral.sh/uv/)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install all workspace dependencies (api, worker, shared)
uv sync

# Run database migrations (DATABASE_URL must be set)
export DATABASE_URL="postgresql+psycopg2://postgres:postgres@localhost:5432/postgres"
alembic upgrade head

# Start API locally (without Docker)
cd src/edu-api
uv run python main.py

# Optional: in another terminal, start the worker locally
cd src/edu-worker
uv run python main.py
```

### Frontend Setup

```bash
cd src/edu-web

# Install dependencies
pnpm install

# Generate TypeScript types from OpenAPI schema (optional)
pnpm gen:types
```

## ⚙️ Configuration

### Backend Environment Variables

You can configure the backend either via **Azure Key Vault** (recommended for production) or via local environment variables / `.env` files (recommended for local dev).

```env
# Azure Key Vault (production)
AZURE_KEY_VAULT_URI=

# Usage Limits (optional, defaults shown)
MAX_DOCUMENT_UPLOADS_PER_DAY=5
MAX_QUIZ_GENERATIONS_PER_DAY=10
MAX_FLASHCARD_GENERATIONS_PER_DAY=10
MAX_CHAT_MESSAGES_PER_DAY=50
```

For local development, you can skip Key Vault and set individual environment variables directly:

```env
# Azure Key Vault (local)
AZURE_KEY_VAULT_URI=

# Usage Limits (optional, defaults shown)
MAX_DOCUMENT_UPLOADS_PER_DAY=5
MAX_QUIZ_GENERATIONS_PER_DAY=10
MAX_FLASHCARD_GENERATIONS_PER_DAY=10
MAX_CHAT_MESSAGES_PER_DAY=50
```

**Note:** The backend uses `python-dotenv`, so `.env` files at the project root work fine for local dev. See [Local Development Guide](./docs/LOCAL_DEVELOPMENT.md) for the full list and details.

### Frontend Environment Variables

Create a `.env` file in the `src/edu-web/` directory:

```env
VITE_SERVER_URL=http://localhost:8000
VITE_SUPABASE_URL=
VITE_SUPABASE_ANON_KEY=
```

For detailed configuration instructions, see the [Local Development Guide](./docs/LOCAL_DEVELOPMENT.md).

## 📁 Project Structure

```
edu-agent/
├── src/
│   ├── edu-api/        # FastAPI backend (public API)
│   ├── edu-worker/     # Background worker (queue/AI processing)
│   ├── edu-web/        # React frontend (Vite + TanStack)
│   └── edu-shared/     # Shared DB models, agents, services, schemas
├── deploy/
│   └── azure/          # Azure Terraform + ACR build tooling
├── docs/               # Documentation (features, local dev, privacy, etc.)
├── alembic.ini         # Alembic config pointing at src/edu-shared/db/alembic
├── docker-compose.yaml # Local stack (api, worker, db, azurite)
├── pyproject.toml      # uv workspace definition
├── uv.lock             # Locked dependency graph
└── ruff.toml           # Backend linting/formatting configuration
```

## 🔧 Development

### Backend Development

```bash
# From repo root

# Create a new database migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Run API with uv (auto-respects workspace venv)
cd src/edu-api
uv run python main.py
```

### Frontend Development

```bash
cd src/edu-web

# Start development server
pnpm dev

# Build for production
pnpm build

# Run linter
pnpm lint

# Format code
pnpm format

# Run type checking
pnpm type-check

# Generate TypeScript types from OpenAPI schema
pnpm gen:types
```

### Code Quality

Both backend and frontend use linting and formatting tools:

- **Backend**: Ruff (configured in `ruff.toml`, run via `ruff format .` and `ruff check .`)
- **Frontend**: ESLint + Prettier (configured in `src/edu-web/`)

## 📚 API Documentation

Once the backend server is running, API documentation is available at:

- **Scalar UI (OpenAPI docs)**: `http://localhost:8000/`
- **Health Check**: `http://localhost:8000/health`
- **OpenAPI Schema**: `http://localhost:8000/openapi.json`

## 📖 Documentation

Comprehensive documentation is available in the `docs/` directory:

- **[Features](./docs/FEATURES.md)** - Detailed overview of platform features and capabilities
- **[Local Development](./docs/LOCAL_DEVELOPMENT.md)** - Complete setup and development guide (Docker + uv workspace)
- **[Azure Deployment](./docs/AZURE_DEPLOYMENT.md)** - Production deployment instructions for Azure (using `deploy/azure`)
- **[Privacy Policy](./docs/PRIVACY_POLICY.md)** - Privacy and data handling information

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Guidelines

- Follow the existing code style and conventions
- Write clear commit messages
- Add tests for new features when possible
- Update documentation as needed
- Ensure all linting checks pass

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 💬 Support

- **Documentation**: Check the [docs](./docs/) directory
- **Issues**: [GitHub Issues](https://github.com/StudentTraineeCenter/edu-agent/issues)

## 🙏 Acknowledgments

- Built with [uv](https://github.com/astral-sh/uv), [FastAPI](https://fastapi.tiangolo.com/), and [React](https://react.dev/)
- Powered by [Azure AI Services](https://azure.microsoft.com/en-us/products/ai-services)
- UI built with [Radix UI](https://www.radix-ui.com/) and [shadcn/ui](https://ui.shadcn.com/)

---

<div align="center">

Made with ❤️ for students and educators

[⬆ Back to Top](#eduagent)

</div>
