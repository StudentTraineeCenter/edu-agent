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

- **📄 Document Processing** - Upload PDF, DOCX, TXT, and RTF files with automatic text extraction and semantic search
- **💬 AI Chat Tutor** - Interactive conversations with an AI assistant that understands your course materials
- **📝 Auto-Generated Quizzes** - AI-powered multiple-choice questions based on your documents
- **🎴 Smart Flashcards** - Automatically generated flashcard sets for efficient studying
- **📝 AI-Generated Notes** - Create comprehensive study notes from your documents with AI assistance
- **🗺️ Mind Maps** - Visual knowledge maps generated from your course materials
- **📋 Study Plans** - Personalized study plans based on your performance and progress
- **📊 Study Tracking** - Monitor your progress with detailed attempt tracking and analytics
- **🌐 Multi-language Support** - Study materials in multiple languages
- **🔐 Azure Entra ID Authentication** - Secure authentication and authorization
- **🔍 Semantic Search** - Vector-based search across your documents using PostgreSQL pgvector

## 🏗️ Tech Stack

### Backend

- **[FastAPI](https://fastapi.tiangolo.com/)** - Modern, fast Python web framework
- **[PostgreSQL](https://www.postgresql.org/)** - Relational database with Alembic migrations and pgvector extension
- **[Azure OpenAI](https://azure.microsoft.com/en-us/products/ai-services/openai-service)** - LLM capabilities for chat, quizzes, flashcards, notes, mind maps, and study plans
- **[Azure Content Understanding](https://azure.microsoft.com/en-us/products/ai-services/document-intelligence)** - Document processing and text extraction
- **[Azure Blob Storage](https://azure.microsoft.com/en-us/products/storage/blobs)** - File storage
- **[Azure Entra ID](https://azure.microsoft.com/en-us/products/entra/)** - Authentication and authorization

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

- **Python 3.11+** - [Download Python](https://www.python.org/downloads/)
- **Node.js 18+** - [Download Node.js](https://nodejs.org/)
- **pnpm** - `npm install -g pnpm`
- **Docker & Docker Compose** - [Install Docker](https://docs.docker.com/get-docker/)
- **Azure Account** - With the following services configured:
  - Azure OpenAI
  - Azure Content Understanding (Document Intelligence)
  - Azure Blob Storage
  - Azure Entra ID (App Registration)

## 🚀 Quick Start

Get EduAgent running locally in minutes:

```bash
# Clone the repository
git clone https://github.com/StudentTraineeCenter/edu-agent.git
cd edu-agent

# Start PostgreSQL database
docker-compose up -d db

# Set up backend
cd server
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
alembic upgrade head

# Configure environment variables (see Configuration section)
cp .env.example .env
# Edit .env with your Azure credentials

# Start API server
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# In a new terminal, set up frontend
cd web
pnpm install
pnpm dev
```

Visit `http://localhost:3000` to access the application.

## 📦 Installation

### Backend Setup

```bash
cd server

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run database migrations
alembic upgrade head
```

### Frontend Setup

```bash
cd web

# Install dependencies
pnpm install

# Generate TypeScript types from OpenAPI schema (optional)
pnpm gen:types
```

## ⚙️ Configuration

### Backend Environment Variables

Create a `.env` file in the `server/` directory:

```env
# Azure Key Vault (required for production)
# All other Azure service credentials are retrieved from Key Vault
AZURE_KEY_VAULT_URI=https://your-key-vault.vault.azure.net/

# Usage Limits (optional, defaults shown)
MAX_CHAT_MESSAGES_PER_DAY=100
MAX_FLASHCARD_GENERATIONS_PER_DAY=100
MAX_QUIZ_GENERATIONS_PER_DAY=100
MAX_DOCUMENT_UPLOADS_PER_DAY=100
```

**Note:** For local development, you can set individual environment variables instead of using Key Vault. The application will fall back to environment variables if Key Vault is not configured or if a secret is not found. See [Local Development Guide](./docs/LOCAL_DEVELOPMENT.md) for detailed configuration options.

### Frontend Environment Variables

Create a `.env` file in the `web/` directory:

```env
VITE_SERVER_URL=http://localhost:8000
VITE_AZURE_ENTRA_CLIENT_ID=your-client-id
VITE_AZURE_ENTRA_TENANT_ID=your-tenant-id
```

For detailed configuration instructions, see the [Local Development Guide](./docs/LOCAL_DEVELOPMENT.md).

## 📁 Project Structure

```
edu-agent/
├── server/                 # FastAPI backend
│   ├── api/               # API routes and endpoints
│   │   ├── v1/           # API version 1
│   │   │   └── endpoints/ # Individual endpoint modules
│   │   └── endpoints.py  # Main endpoint definitions
│   ├── core/             # Core business logic
│   │   ├── agents/       # AI agent implementations
│   │   └── services/     # Business logic services
│   ├── db/               # Database layer
│   │   ├── models.py     # SQLAlchemy models
│   │   └── alembic/      # Database migrations
│   └── schemas/          # Pydantic schemas
├── web/                   # React frontend
│   ├── src/
│   │   ├── components/   # Reusable React components
│   │   ├── features/     # Feature modules
│   │   ├── routes/       # Route definitions
│   │   └── integrations/ # API integration layer
│   └── public/           # Static assets
├── infra/                 # Infrastructure as Code
│   └── modules/          # Terraform modules
├── docs/                  # Documentation
│   ├── FEATURES.md       # Feature documentation
│   ├── LOCAL_DEVELOPMENT.md
│   ├── AZURE_DEPLOYMENT.md
│   └── PRIVACY_POLICY.md
└── docker-compose.yaml    # Local development services
```

## 🔧 Development

### Backend Development

```bash
cd server
source venv/bin/activate

# Run development server with auto-reload
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Create a new database migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Run tests (if available)
pytest
```

### Frontend Development

```bash
cd web

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

- **Backend**: Ruff (configured in `server/ruff.toml`)
- **Frontend**: ESLint + Prettier (configured in `web/`)

## 📚 API Documentation

Once the backend server is running, API documentation is available at:

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`
- **OpenAPI Schema**: `http://localhost:8000/openapi.json`

## 📖 Documentation

Comprehensive documentation is available in the `docs/` directory:

- **[Features](./docs/FEATURES.md)** - Detailed overview of platform features and capabilities
- **[Local Development](./docs/LOCAL_DEVELOPMENT.md)** - Complete setup and development guide
- **[Azure Deployment](./docs/AZURE_DEPLOYMENT.md)** - Production deployment instructions for Azure
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
- **Discussions**: [GitHub Discussions](https://github.com/StudentTraineeCenter/edu-agent/discussions)

## 🙏 Acknowledgments

- Built with [FastAPI](https://fastapi.tiangolo.com/) and [React](https://react.dev/)
- Powered by [Azure AI Services](https://azure.microsoft.com/en-us/products/ai-services)
- UI components from [Radix UI](https://www.radix-ui.com/)

---

<div align="center">

Made with ❤️ for students and educators

[⬆ Back to Top](#eduagent)

</div>
