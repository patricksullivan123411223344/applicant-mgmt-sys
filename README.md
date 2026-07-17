# Student Housing Application Processing System

Internal operations platform that converts student housing `.docx` applications into structured group records and Excel exports.

The **database is the source of truth**. Word documents are immutable inputs; Excel workbooks are generated projections. Deterministic Python logic owns validation, group numbering, and writes. An LLM may assist extraction later but never writes to the database or allocates group numbers.

Architecture and scope: see [`cursor-docs/PROJECT_OVERVIEW.md`](cursor-docs/PROJECT_OVERVIEW.md) and [`cursor-docs/SYSTEM_ARCHITECTURE.md`](cursor-docs/SYSTEM_ARCHITECTURE.md).

**What’s built vs what’s left:** [`cursor-docs/CURRENT_STATUS.md`](cursor-docs/CURRENT_STATUS.md).

## Phase 1 (current)

Deterministic MVP scaffolding:

- Manual DOCX upload API
- Local file archival and SQLite persistence
- Domain / application / infrastructure layer boundaries
- Stub extraction, matching, Excel, and review paths

## Setup

Requires Python 3.12+ and [uv](https://docs.astral.sh/uv/).

```bash
uv sync --extra dev
cp .env.example .env
mkdir -p data/storage
```

## Supabase (Option 1)

Persistence still uses SQLAlchemy. From the **same** Supabase project, set:

1. `SUPABASE_URL` — Project URL (Settings → API)
2. `SUPABASE_SERVICE_ROLE_KEY` — service_role key (Settings → API; server-only)
3. `DATABASE_URL` — Postgres URI (Database → Connection string), using the `psycopg` driver prefix:

```bash
DATABASE_URL=postgresql+psycopg://postgres.[ref]:[PASSWORD]@aws-0-[region].pooler.supabase.com:6543/postgres
SUPABASE_URL=https://YOUR_PROJECT.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
```

Then migrate and run:

```bash
uv sync --extra dev
uv run alembic upgrade head
uv run uvicorn housing_processor.main:app --reload
```

Leave the Supabase keys empty and keep the default SQLite `DATABASE_URL` for local offline work.

Schema DDL (Postgres/Supabase) matching PROJECT_OVERVIEW domains lives at [`scripts/sql/001_supabase_schema.sql`](scripts/sql/001_supabase_schema.sql). Prefer applying with Alembic:

```bash
uv run alembic upgrade head
```

## Database migrations

```bash
uv run alembic upgrade head
```

## Run the API and UI

```bash
uv run uvicorn housing_processor.main:app --reload
```

Then open:

- UI: `http://127.0.0.1:8000/`
- Liveness: `http://127.0.0.1:8000/health/live`
- Readiness: `http://127.0.0.1:8000/health/ready`
- API docs: `http://127.0.0.1:8000/docs`
- API base: `/api/v1`

The vanilla frontend lives in [`frontend/`](frontend/) and is served by the same uvicorn process.

## Process an application (command-triggered)

```bash
uv run python scripts/process_application.py <application-id>
```

## Tests

```bash
uv run pytest
```

## Package layout

```text
frontend/             # HTML/CSS/JS ops UI (served at /)
src/housing_processor/
  presentation/   # FastAPI routes, Streamlit (later)
  application/    # Use cases, commands, DTOs
  domain/         # Framework-free entities and policies
  infrastructure/ # DB, DOCX, Excel, storage, LLM adapters
  observability/  # Structured logging
```
