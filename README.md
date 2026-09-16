# The Lenny Growth Assistant

A full-stack RAG (Retrieval-Augmented Generation) application designed for growth engineering, product strategy, and marketing insights. It answers user questions strictly based on knowledge retrieved from Lenny's Podcast and Newsletter transcripts, providing inline citations and dynamic artifacts.

## Features

- **Strict Source Grounding:** Refuses to hallucinate outside the retrieved transcript corpus.
- **Dual LLM Provider:** Seamlessly switch between Anthropic (Claude) and a local Ollama instance with zero code changes.
- **Sandboxed Artifact Viewer:** Renders generated Markdown and HTML content safely in an isolated iframe.
- **Server-Sent Events (SSE):** Provides a smooth, token-by-token streaming chat interface.
- **Robust Resilience:** Handles LLM timeouts and database disconnects gracefully without crashing.
- **Vector Search:** Uses `pgvector` and SentenceTransformers (`all-MiniLM-L6-v2`) for semantic context retrieval.

---

## Architecture Overview

- **Backend:** FastAPI (Python), SQLAlchemy, PostgreSQL with `pgvector`, and `bleach` for XSS sanitization.
- **Frontend:** React (TypeScript), Vite, Tailwind CSS (v4) utilizing strict CSS design tokens.
- **AI/LLM:** Integrates the `claude_agent_sdk` for Anthropic and direct HTTP stream processing for Ollama.

*See [`docs/architecture.md`](docs/architecture.md) for deeper backend flow designs and [`docs/design.md`](docs/design.md) for frontend visual tokens.*

---

## Prerequisites

- **Docker & Docker Compose** (for PostgreSQL/pgvector and Ollama, if running locally).
- **Python 3.10+** (tested on 3.14).
- **Node.js 18+** & **npm**.
- An Anthropic API Key (if using Claude).

---

## Installation

### 1. Database Setup
```bash
docker-compose up -d
```
This spins up a PostgreSQL instance with the `pgvector` extension enabled.

### 2. Backend Setup
```bash
cd backend
python -m venv venv
.\venv\Scripts\activate  # Windows
# source venv/bin/activate  # macOS/Linux

pip install -r requirements.txt
alembic upgrade head
```

### 3. Frontend Setup
```bash
cd frontend
npm install
```

---

## Environment Variables

Copy `.env.example` to `.env` in the root directory:

```env
# Database
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/lenny_db

# LLM Provider Configuration ('anthropic' or 'ollama')
LLM_PROVIDER=anthropic

# Anthropic 
ANTHROPIC_API_KEY=sk-ant-xxx

# Ollama 
OLLAMA_BASE_URL=http://host.docker.internal:11434
OLLAMA_MODEL=llama3.2:3b

# Resilience
LLM_TIMEOUT_SECONDS=30
```

---

## Running the Application

**Terminal 1: Start Backend**
```bash
cd backend
.\venv\Scripts\activate
uvicorn main:app --reload --port 8000
```

**Terminal 2: Start Frontend**
```bash
cd frontend
npm run dev
```

Visit `http://localhost:5173` in your browser.

---

## Ingestion 

To populate the vector database with transcripts:

```bash
cd ingestion
python ingest.py --refresh
```
*Note: Make sure your `.env` is properly sourced so `ingest.py` can connect to the database.*

---

## Tests

The backend uses `pytest` for unit and contract testing. The test suite uses mocked dependencies, allowing tests to run completely offline without the database or GPU.

```bash
cd backend
.\venv\Scripts\pytest tests/
```

Manual testing procedures (UI states, resilience degradation, etc.) are documented in [`docs/test_plan.md`](docs/test_plan.md).

---

## Troubleshooting

| Issue / Failure Mode | Cause / Mitigation |
|----------------------|-------------------|
| **Ollama Unreachable** | Ensure your Docker setup can reach the host (`host.docker.internal`). If running Ollama natively, change `OLLAMA_BASE_URL` to `http://localhost:11434`. The backend will gracefully return a JSON error instead of crashing. |
| **Port Conflicts** | The backend runs on `8000`, PostgreSQL on `5432`, and Vite on `5173`. Ensure these ports are free. |
| **Empty Responses (Out of Corpus)** | If the assistant always responds "I'm sorry, the transcripts don't cover this topic", ensure you have run the ingestion script (`python ingest.py`) and verified chunks in your database. |
| **Dropped DB Connection** | If PostgreSQL restarts, the backend will auto-retry the query once. If it remains down, you'll receive a `503 Service Unavailable` error bar in the UI. Restart the `docker-compose` stack. |
| **Missing API Keys** | If using Anthropic without a valid `ANTHROPIC_API_KEY`, the stream will yield an Auth Error. Check your `.env` file. |
