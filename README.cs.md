# EduAgent

<div align="center">

**Vzdělávací platforma s umělou inteligencí pro vytváření interaktivních výukových materiálů**

[![Python](https://img.shields.io/badge/Python-3.12+-blue.svg)](https://www.python.org/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.7+-blue.svg)](https://www.typescriptlang.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.117+-green.svg)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-19-blue.svg)](https://react.dev/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Language: English](https://img.shields.io/badge/Language-English-lightgrey.svg)](README.md)
[![Jazyk: Čeština](https://img.shields.io/badge/Jazyk-Čeština-blue.svg)](README.cs.md)

[Funkce](#-funkce) • [Rychlý start](#-rychlý-start) • [Dokumentace](#-dokumentace) • [Příspěvky](#-příspěvky)

</div>

---

EduAgent je špičková vzdělávací platforma založená na umělé inteligenci, navržená tak, aby změnila způsob, jakým se učíte. Kombinací pokročilého RAG (Retrieval-Augmented Generation) s proaktivními AI agenty poháněnými **LangGraph** promění EduAgent statické dokumenty v dynamického, osobního tutora. Nahrajte své studijní materiály a zažijte nový způsob studia s automaticky generovanými kvízy, kartičkami (flashcards), myšlenkovými mapami a **Personalizovaným studijním plánem**, který se přizpůsobí vašemu tempu učení pomocí principů **Active Recall** (aktivní vybavování) a **Adaptive Learning** (adaptivní učení).

## Obsah

- [Funkce](#-funkce)
- [Technologický zásobník](#-technologický-zásobník)
- [Pilotní hodnocení](#-pilotní-hodnocení)
- [Požadavky](#-požadavky)
- [Rychlý start](#-rychlý-start)
- [Instalace](#-instalace)
- [Konfigurace](#-konfigurace)
- [Struktura projektu](#-struktura-projektu)
- [Vývoj](#-vývoj)
- [API Dokumentace](#-api-dokumentace)
- [Roadmapa](#-roadmapa)
- [Dokumentace](#-dokumentace)
- [Příspěvky](#-příspěvky)
- [Licence](#-licence)
- [Podpora](#-podpora)

## ✨ Funkce

- **📂 Projektové učení** - Organizujte kurzy do zaměřených projektů obsahujících všechny vaše dokumenty, chaty a studijní pomůcky generované AI.
- **🧠 Personalizované studijní plány** - AI identifikuje vaše slabá místa na základě výkonu (zaměřuje se na témata s úspěšností < 70 %) a vygeneruje učební plán na míru, který vám pomůže látku ovládnout.
- **🤖 Proaktivní AI tutor (LangGraph)** - Chatujte s inteligentním agentem, který používá **vzor ReAct** k proaktivnímu generování kvízů, kartiček a poznámek během konverzace.
- **📄 Chytré zpracování dokumentů** - Nahrávání PDF, DOCX, TXT a RTF souborů přetažením. Poháněno **Azure Content Understanding** pro robustní extrakci textu a sémantickou segmentaci.
- **🔍 Sémantické vyhledávání a RAG** - Pokládejte otázky založené na vašich konkrétních materiálech. Používá **pgvector** pro vysoce přesné vyhledávání s citacemi zdrojů.
- **📝 Automatizované kvízy** - Generujte testy s výběrem odpovědí z jakéhokoli dokumentu. Systém vás oznámkuje, vysvětlí odpovědi a sleduje váš pokrok.
- **🎴 Kartičky (Flashcards)** - Okamžitě proměňte hustý text v kartičky. Ideální pro zapamatování definic a klíčových pojmů.
- **🗺️ Interaktivní myšlenkové mapy** - Vizualizujte propojení mezi tématy pomocí myšlenkových map generovaných AI, které vám pomohou pochopit širší souvislosti.
- **🔐 Zabezpečení podnikové úrovně** - Postaveno na Supabase Auth, Azure Key Vault pro správu infrastrukturních tajemství a Azure limitech využití pro ochranu dat a kontrolu nákladů.

## 🏗️ Technologický zásobník

### Backend

- **[FastAPI](https://fastapi.tiangolo.com/)** - Moderní, rychlý Python webový framework
- **[LangGraph](https://www.langchain.com/langgraph)** - Orchestrace autonomních AI agentů s možností volání nástrojů
- **[PostgreSQL](https://www.postgresql.org/)** - Relační databáze s Alembic migracemi a rozšířením **pgvector**
- **[Azure OpenAI](https://azure.microsoft.com/en-us/products/ai-services/openai-service)** - Schopnosti LLM (GPT-4o, text-embedding-3-large)
- **[Azure Content Understanding](https://azure.microsoft.com/en-us/products/ai-services/document-intelligence)** - Zpracování dokumentů a extrakce textu
- **[Azure Blob Storage](https://azure.microsoft.com/en-us/products/storage/blobs)** - Úložiště souborů
- **[Azure Key Vault](https://azure.microsoft.com/en-us/products/key-vault)** - Správa infrastrukturních tajemství
- **[Supabase](https://supabase.com/)** - Autentizace a autorizace

### Frontend

- **[React 19](https://react.dev/)** - UI knihovna
- **[TypeScript](https://www.typescriptlang.org/)** - Typová bezpečnost
- **[Vite](https://vitejs.dev/)** - Buildovací nástroj a dev server
- **[TanStack Router](https://tanstack.com/router)** - Typově bezpečný routing
- **[Effect Atom](https://github.com/tim-smart/effect-atom)** - Správa stavu a načítání dat
- **[TailwindCSS](https://tailwindcss.com/)** - Utility-first CSS framework
- **[Radix UI](https://www.radix-ui.com/)** - Přístupné komponenty

## 📊 Pilotní hodnocení

EduAgent byl validován prostřednictvím pilotní studie s 15 testovacími dotazy napříč různými typy dokumentů:

- **93% úspěšnost vyhledávání**: Vysoká přesnost při hledání relevantního kontextu.
- **0 % halucinací**: Přísné ukotvení v dokumentech poskytnutých uživatelem.
- **< 150 ms latence**: Efektivní výkon vektorového vyhledávání v PostgreSQL.

## 📋 Požadavky

Než začnete, ujistěte se, že máte nainstalované následující:

- **Python 3.12+** - [Stáhnout Python](https://www.python.org/downloads/)
- **Node.js 18+** - [Stáhnout Node.js](https://nodejs.org/)
- **pnpm** - `npm install -g pnpm`
- **Docker & Docker Compose** - [Instalovat Docker](https://docs.docker.com/get-docker/)
- **Terraform** - [Instalovat Terraform](https://developer.hashicorp.com/terraform/install)
- **Azure a Supabase** - Zajištěno pomocí Terraformu:
  - Moduly Terraformu nastaví:
    - **Azure AI Foundry**: Hub, projekt a nasazení modelů (GPT-4o, text-embedding-3-small)
    - **Azure Storage**: Účet s Blob kontejnery a frontou úkolů
    - **Azure Key Vault**: Bezpečná správa tajemství s RBAC
    - **Azure Container Registry**: Soukromý registr pro obrazy kontejnerů
    - **Azure Container Apps**: Serverless hosting pro API a Worker služby
    - **Azure App Service**: Linux hosting pro webový frontend
    - **Azure Monitor**: Log Analytics a Application Insights pro sledování
    - **Supabase**: Spravovaný projekt s nakonfigurovanou databází a autentizací
  - Viz [dokumentace infrastruktury](docs/AZURE_DEPLOYMENT.md) pro instrukce k nastavení.

## 🚀 Rychlý start

Spusťte EduAgent lokálně pomocí Dockeru pro backend a Vite pro frontend:

```bash
# Klonování repozitáře
git clone https://github.com/StudentTraineeCenter/edu-agent.git
cd edu-agent

# Spuštění backendu (API, worker, Postgres, Azurite)
docker-compose up --build api worker db azurite

# V samostatném terminálu spusťte DB migrace (jednorázově)
# Ujistěte se, že DATABASE_URL je správně nastavena pro váš lokální Postgres
export DATABASE_URL="postgresql+psycopg2://postgres:postgres@localhost:5432/postgres"
alembic upgrade head

# V novém terminálu spusťte webový frontend
cd src/edu-web
pnpm install
pnpm dev
```

Navštivte `http://localhost:3000` pro webovou aplikaci a `http://localhost:8000` pro API.

## 📦 Instalace

### Nastavení backendu (API + Worker)

Python služby využívají **uv workspace** s `pyproject.toml` + `uv.lock`.

```bash
cd edu-agent

# Instalace uv, pokud jej ještě nemáte (viz https://docs.astral.sh/uv/)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Instalace všech závislostí (api, worker, shared)
uv sync

# Spuštění databázových migrací (DATABASE_URL musí být nastaveno)
export DATABASE_URL="postgresql+psycopg2://postgres:postgres@localhost:5432/postgres"
alembic upgrade head

# Spuštění API lokálně (bez Dockeru)
cd src/edu-api
uv run python main.py

# Volitelně: v jiném terminálu spusťte worker lokálně
cd src/edu-worker
uv run python main.py
```

### Nastavení frontendu

```bash
cd src/edu-web

# Instalace závislostí
pnpm install

# Generování TypeScript typů z OpenAPI schématu (volitelně)
pnpm gen:client
```

## ⚙️ Konfigurace

### Backendové proměnné prostředí

Backend můžete konfigurovat buď přes **Azure Key Vault** (doporučeno pro produkci), nebo přes lokální proměnné prostředí / `.env` soubory (doporučeno pro lokální vývoj).

```env
# Azure Key Vault (produkce)
AZURE_KEY_VAULT_URI=

# Limity využití (volitelné, zobrazeny výchozí hodnoty)
MAX_DOCUMENT_UPLOADS_PER_DAY=5
MAX_QUIZ_GENERATIONS_PER_DAY=10
MAX_FLASHCARD_GENERATIONS_PER_DAY=10
MAX_CHAT_MESSAGES_PER_DAY=50
```

Pro lokální vývoj můžete přeskočit Key Vault a nastavit jednotlivé proměnné přímo:

```env
# Azure Key Vault (lokální)
AZURE_KEY_VAULT_URI=

# Limity využití (volitelné, zobrazeny výchozí hodnoty)
MAX_DOCUMENT_UPLOADS_PER_DAY=5
MAX_QUIZ_GENERATIONS_PER_DAY=10
MAX_FLASHCARD_GENERATIONS_PER_DAY=10
MAX_CHAT_MESSAGES_PER_DAY=50
```

**Poznámka:** Backend používá `python-dotenv`, takže `.env` soubory v kořenovém adresáři projektu fungují správně. Viz [Průvodce lokálním vývojem](./docs/LOCAL_DEVELOPMENT.md) pro kompletní seznam.

### Frontendové proměnné prostředí

Vytvořte soubor `.env` v adresáři `src/edu-web/`:

```env
VITE_SERVER_URL=http://localhost:8000
VITE_SUPABASE_URL=
VITE_SUPABASE_ANON_KEY=
```

Podrobné pokyny ke konfiguraci naleznete v [Průvodci lokálním vývojem](./docs/LOCAL_DEVELOPMENT.md).

## 📁 Struktura projektu

```
edu-agent/
├── src/
│   ├── edu-api/            # FastAPI backend (veřejné API)
│   ├── edu-worker/         # Background worker (fronta/AI zpracování)
│   ├── edu-web/            # React frontend (Vite + TanStack)
│   ├── eduagent-vibecode/  # Vibecoded UI
│   └── shared/
│       ├── ai/             # Sdílená AI logika a utility
│       ├── core/           # Sdílená jádrová logika (pomocné funkce, errory)
│       ├── db/             # Sdílené DB modely, schémata, migrace
│       └── queue/          # Sdílená fronta a typy zpráv
├── deploy/
│   └── azure/              # Azure Terraform + ACR build nástroje
├── docs/                   # Dokumentace (funkce, vývoj, soukromí atd.)
├── alembic.ini             # Konfigurace Alembic mířící na src/shared/db/src/edu_db/alembic
├── docker-compose.yaml     # Lokální stack (api, worker, db, azurite)
├── pyproject.toml          # Definice uv workspace
├── uv.lock                 # Uzamčený graf závislostí
└── ruff.toml               # Konfigurace lintování/formátování backendu
```

## 🔧 Vývoj

### Vývoj backendu

```bash
# Z kořene repozitáře

# Vytvoření nové databázové migrace
alembic revision --autogenerate -m "popis"

# Použití migrací
alembic upgrade head

# Spuštění API pomocí uv
cd src/edu-api
uv run python main.py
```

### Vývoj frontendu

```bash
cd src/edu-web

# Spuštění vývojového serveru
pnpm dev

# Build pro produkci
pnpm build

# Spuštění linteru
pnpm lint

# Formátování kódu
pnpm format

# Typová kontrola
pnpm type-check

# Generování TypeScript typů z OpenAPI schématu
pnpm gen:client
```

### Kvalita kódu

Backend i frontend používají nástroje pro lintování a formátování:

- **Backend**: Ruff (konfigurováno v `ruff.toml`, spouští se přes `ruff format .` a `ruff check .`)
- **Frontend**: ESLint + Prettier (konfigurováno v `src/edu-web/`)

## 📚 API Dokumentace

Jakmile běží backend server, dokumentace API je dostupná na:

- **Scalar UI (OpenAPI docs)**: `http://localhost:8000/`
- **Health Check**: `http://localhost:8000/health`
- **OpenAPI Schéma**: `http://localhost:8000/openapi.json`

## 🗺️ Roadmapa

- [ ] **Podpora audia/videa**: Automatická transkripce a analýza přednášek.
- [ ] **Pokročilé Spaced Repetition**: Sofistikované algoritmy pro dlouhodobé zapamatování.
- [ ] **AI generované prezentace**: Přeměna materiálů projektu do strukturovaných slidů.
- [ ] **Kolaborativní projekty**: Studium s vrstevníky ve sdíleném prostředí s AI.

## 📖 Dokumentace

Kompletní dokumentace je k dispozici v adresáři `docs/`:

- **[Funkce](./docs/FEATURES.md)** - Detailní přehled funkcí a možností platformy
- **[Lokální vývoj](./docs/LOCAL_DEVELOPMENT.md)** - Průvodce nastavením a vývojem (Docker + uv workspace)
- **[Nasazení na Azure](./docs/AZURE_DEPLOYMENT.md)** - Instrukce pro produkční nasazení na Azure (pomocí `deploy/azure`)

## 🤝 Příspěvky

Příspěvky jsou vítány! Neváhejte poslat Pull Request.

1. Forkněte repozitář
2. Vytvořte větev pro svou funkci (`git checkout -b feature/uzasna-funkce`)
3. Commitněte své změny (`git commit -m 'Přidání úžasné funkce'`)
4. Pushněte do větve (`git push origin feature/uzasna-funkce`)
5. Otevřete Pull Request

### Pokyny pro vývoj

- Dodržujte stávající styl kódu a konvence
- Pište jasné commit zprávy
- Přidávejte testy pro nové funkce, pokud je to možné
- Aktualizujte dokumentaci podle potřeby
- Ujistěte se, že všechny kontroly linteru procházejí

## 📄 Licence

Tento projekt je licencován pod licencí MIT - podrobnosti naleznete v souboru [LICENSE](LICENSE).

## 💬 Podpora

- **Dokumentace**: Podívejte se do adresáře [docs](./docs/)
- **Problémy**: [GitHub Issues](https://github.com/StudentTraineeCenter/edu-agent/issues)

---

<div align="center">

Vyrobeno s ❤️ pro studenty a učitele

[⬆ Zpět nahoru](#eduagent)

</div>

