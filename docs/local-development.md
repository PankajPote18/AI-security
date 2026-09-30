# Local development (no Docker)

Everything in this project runs natively on Windows/macOS/Linux. Docker is never required
locally; it is only an optional deployment packaging option, added in a later stage.

## 1. Prerequisites

- [uv](https://docs.astral.sh/uv/) — installs and pins the right Python version for you.
- **PostgreSQL 16+**, installed natively (e.g. the EDB installer on Windows, `brew install
  postgresql` on macOS, your distro's package on Linux).
- **Node.js 20+** (only needed for `frontend/`).

## 2. First-time setup

```bash
uv sync                     # installs every workspace package (ml, security-core, backend, rag-core, mcp-server)
cp .env.example .env        # then fill in the values below
cd frontend && npm install  # once, for the dashboard
```

### Database

Create a dedicated `copilot` role and the `copilot_dev`/`copilot_test` databases:

```powershell
# Windows (PowerShell)
.\infrastructure\scripts\setup-db.ps1
```

On macOS/Linux, run the equivalent `createuser`/`createdb` commands by hand (a `.sh` version of
the script is a good first contribution). Put the resulting connection strings and a generated
JWT secret into `.env`:

```
DATABASE_URL=postgresql+asyncpg://copilot:<password>@localhost:5432/copilot_dev
TEST_DATABASE_URL=postgresql+asyncpg://copilot:<password>@localhost:5432/copilot_test
JWT_SECRET_KEY=<python -c "import secrets; print(secrets.token_urlsafe(48))">
```

Apply migrations to both databases:

```bash
cd backend
DATABASE_URL=$DATABASE_URL uv run alembic upgrade head
DATABASE_URL=$TEST_DATABASE_URL uv run alembic upgrade head
```

(On Windows PowerShell, set `$env:DATABASE_URL = "..."` before each `alembic upgrade head`.)

### ML model

The backend needs a trained model artifact before it will start:

```bash
uv run copilot-ml data build
uv run copilot-ml train
```

This writes `ml/models/{phishing_url_model.joblib, metadata.json, background_sample.parquet}`
and `ml/reports/{data_card.md, model_card.md, metrics.json, figures/}`.

### LLM and threat intelligence (optional, but needed for reports and mode=deep)

`HF_TOKEN` (a free Hugging Face Inference Providers token) and `URLHAUS_AUTH_KEY` (a free
abuse.ch key) are both optional - everything degrades gracefully without them (report generation
returns `status="failed"` with a clear error rather than failing the analysis; threat intel
reports `status="unavailable"`). See `.env.example` for where to get each one and why the default
model is `openai/gpt-oss-120b` rather than the smaller `20b`.

## 3. Running the backend

```bash
cd backend
uv run uvicorn app.main:app --reload
```

Swagger UI: <http://localhost:8000/docs>. Health checks: `GET /health/live`, `GET /health/ready`
(the latter fails if the model isn't loaded). The knowledge base is auto-ingested into a local
Qdrant index (`.qdrant`) on startup - the first run takes a few seconds longer while it downloads
the embedding models; every run after is near-instant (see `rag_core.ingest_directory`).

The MCP server (`mcp-server/`) needs no separate process for normal use: `mode=deep` analyses
spawn it as a stdio subprocess on demand (see ADR-0005) and it exits when the analysis finishes.
To run it standalone - for MCP Inspector, or to point an external MCP host (e.g. Claude Desktop)
at it - use `uv run copilot-mcp` from the repo root; it keeps its own local Qdrant index
(`.qdrant-mcp`) so it never conflicts with the backend's.

## 4. Running the frontend

```bash
cd frontend
npm run dev
```

<http://localhost:5173>. The dev server proxies `/api` to `http://127.0.0.1:8000` (see
`vite.config.ts`) - start the backend first. `npm run build` produces `frontend/dist` for
deployment (see `docs/deployment.md`); `npm run lint` runs oxlint.

## 5. Running tests

```bash
uv run pytest                          # everything (ml, security-core, rag-core, mcp-server, backend)
uv run pytest backend/tests mcp-server/tests   # need TEST_DATABASE_URL and a trained model
uv run pytest ml/tests libs/security-core/tests libs/rag-core/tests evals/rag   # no external services needed
```

`backend/tests/conftest.py` truncates every table in `TEST_DATABASE_URL` before each test - it
deliberately refuses to run if that variable is unset, rather than silently falling back to the
dev database.

## 6. Common tasks

| Task | Command |
|---|---|
| New migration after changing a model | `cd backend && uv run alembic revision --autogenerate -m "..."` |
| Lint (Python) | `uv run ruff check .` |
| Format (Python) | `uv run ruff format .` |
| Type-check (Python) | `uv run mypy` |
| Lint (frontend) | `cd frontend && npm run lint` |
| Score a URL from the CLI (no backend needed) | `uv run copilot-ml predict "https://example.com"` |
| Search the knowledge base from the CLI | `uv run rag-core search "your query"` |
