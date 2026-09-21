# Local development (no Docker)

Everything in this project runs natively on Windows/macOS/Linux. Docker is never required
locally; it is only an optional deployment packaging option, added in a later stage.

## 1. Prerequisites

- [uv](https://docs.astral.sh/uv/) — installs and pins the right Python version for you.
- **PostgreSQL 16+**, installed natively (e.g. the EDB installer on Windows, `brew install
  postgresql` on macOS, your distro's package on Linux).

## 2. First-time setup

```bash
uv sync                     # installs every workspace package (ml, security-core, backend)
cp .env.example .env        # then fill in the values below
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

## 3. Running the backend

```bash
cd backend
uv run uvicorn app.main:app --reload
```

Swagger UI: <http://localhost:8000/docs>. Health checks: `GET /health/live`, `GET /health/ready`
(the latter fails if the model isn't loaded).

## 4. Running tests

```bash
uv run pytest                          # everything (ml, security-core, backend)
uv run pytest backend/tests            # backend only - needs TEST_DATABASE_URL and a trained model
uv run pytest ml/tests libs/security-core/tests   # no external services needed
```

`backend/tests/conftest.py` truncates every table in `TEST_DATABASE_URL` before each test - it
deliberately refuses to run if that variable is unset, rather than silently falling back to the
dev database.

## 5. Common tasks

| Task | Command |
|---|---|
| New migration after changing a model | `cd backend && uv run alembic revision --autogenerate -m "..."` |
| Lint | `uv run ruff check .` |
| Format | `uv run ruff format .` |
| Type-check | `uv run mypy` |
| Score a URL from the CLI (no backend needed) | `uv run copilot-ml predict "https://example.com"` |
