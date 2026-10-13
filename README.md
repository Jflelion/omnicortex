# OmniCortex Backend

OmniCortex is a backend for a document intelligence platform. Users upload PDFs, the API extracts and indexes their content, and questions are answered with a local RAG pipeline (pgvector + Ollama) that returns the sources used.

## Stack

- FastAPI
- PostgreSQL 16 + pgvector (Docker)
- SQLAlchemy + Alembic
- Pydantic / pydantic-settings
- PyJWT + Passlib (bcrypt)
- PyMuPDF for text extraction
- Ollama: `nomic-embed-text` (embeddings) and `qwen2.5:3b` (generation)

## Features

- JWT authentication and role-based authorization (`admin`, `user`, `analyst`)
- Public registration (always assigned the `user` role)
- PDF upload with type and size validation
- Text extraction, chunking with overlap and background embedding generation
- Semantic search and hybrid retrieval (vector + keyword) with reranking
- `/documents/ask`: grounded answers with auditable sources
- Request IDs and per-stage timing of the RAG pipeline
- `503 Service Unavailable` when Ollama is down or times out

## Project Structure

```text
omnicortex/
├── app/
│   ├── ai/llm/           # LLM client (Ollama) and normalized response model
│   ├── core/             # config, security, JWT, permissions, exceptions
│   ├── database/         # session, seed, embed_chunks (re-index tool)
│   ├── models/           # SQLAlchemy models
│   ├── observability/    # logging, request ID, RAG tracing
│   ├── routers/          # auth, users, roles, documents
│   ├── schemas/          # Pydantic schemas
│   ├── services/         # extraction, chunking, embeddings, retrieval, RAG
│   └── main.py
├── alembic/              # migrations
├── docs/                 # architecture, decisions, changelog, roadmap
├── scripts/              # manual checks
├── tests/
├── docker-compose.yml
├── requirements.txt
├── requirements-dev.txt
├── .env.example
└── run.py
```

## Setup

### 1. Environment

```powershell
python -m venv venv
venv\Scripts\activate
pip install -r requirements-dev.txt
copy .env.example .env
```

Edit `.env` and set at least `DATABASE_URL` and `SECRET_KEY`. Every other value has a default (see `app/core/config.py`).

### 2. Database

```powershell
docker compose up -d
alembic upgrade head
python -m app.database.seed
```

### 3. Ollama

```powershell
ollama pull nomic-embed-text
ollama pull qwen2.5:3b
```

### 4. Run the API

```powershell
python run.py
```

Swagger: http://127.0.0.1:8000/docs

## Usage Flow

1. Register with `POST /users/`.
2. Log in with `POST /auth/login` and use the token in Swagger `Authorize`.
3. Upload a PDF with `POST /documents/upload`. Embeddings are generated in the background after the response.
4. Ask with `POST /documents/ask` or search with `POST /documents/search`.

If Ollama was down during an upload, the chunks stay without embeddings. Index them later with:

```powershell
python -m app.database.embed_chunks
```

## API

### Auth

- `POST /auth/login`
- `GET /auth/me`

### Users

- `POST /users/` — public registration
- `GET /users/{user_id}` — admin
- `PUT /users/{user_id}` — admin (the only way to change a user's role)
- `PATCH /users/{user_id}/deactivate` — admin
- `PATCH /users/{user_id}/activate` — admin
- `DELETE /users/{user_id}` — admin

### Roles

- `POST /roles/` — admin
- `GET /roles/`

### Documents (owner only)

- `POST /documents/upload`
- `GET /documents/`
- `GET /documents/{document_id}`
- `GET /documents/{document_id}/chunks`
- `DELETE /documents/{document_id}`
- `POST /documents/search`
- `POST /documents/ask`

## Development Notes

- Alembic controls the schema. Do not use `Base.metadata.create_all()`.
- Create migrations with `alembic revision --autogenerate -m "message"`.
- Run tests with `pytest`.

## Roadmap

See [docs/ROADMAP.md](docs/ROADMAP.md).
