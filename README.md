# Student Housing Application Processing System

Internal operations platform that converts student housing `.docx` applications into structured group records and Excel exports.

The **database is the source of truth**. Word documents are immutable inputs; Excel workbooks are generated projections. Deterministic Python logic owns validation, group numbering, and writes. An LLM may assist extraction later but never writes to the database or allocates group numbers.

**Plain-English master overview (for everyone):** [`MASTER_OVERVIEW.md`](MASTER_OVERVIEW.md).

Architecture and scope (local builder notes): `cursor-docs/PROJECT_OVERVIEW.md`, `cursor-docs/SYSTEM_ARCHITECTURE.md`, `cursor-docs/CURRENT_STATUS.md`.

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
2. `SUPABASE_ANON_KEY` — anon/public key (Settings → API; safe for the browser)
3. `SUPABASE_SERVICE_ROLE_KEY` — service_role key (Settings → API; **server-only**)
4. `SUPABASE_JWT_SECRET` — legacy JWT Secret (Settings → API; **server-only**; used for HS256 tokens)
5. `DATABASE_URL` — Postgres URI (Database → Connection string), using the `psycopg` driver prefix:

```bash
DATABASE_URL=postgresql+psycopg://postgres.[ref]:[PASSWORD]@aws-0-[region].pooler.supabase.com:6543/postgres
SUPABASE_URL=https://YOUR_PROJECT.supabase.co
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
SUPABASE_JWT_SECRET=your-jwt-secret
AUTH_DISABLED=false
```

Then migrate and run:

```bash
uv sync --extra dev
uv run alembic upgrade head
uv run uvicorn housing_processor.main:app --reload
```

Leave Supabase keys empty, keep the default SQLite `DATABASE_URL`, and set `AUTH_DISABLED=true` for local offline work (only honored when `ENVIRONMENT=local` and SQLite).

Schema DDL:

- Domains: [`scripts/sql/001_supabase_schema.sql`](scripts/sql/001_supabase_schema.sql)
- Auth profiles + RLS: [`scripts/sql/002_supabase_auth_rls.sql`](scripts/sql/002_supabase_auth_rls.sql)

Prefer Alembic:

```bash
uv run alembic upgrade head
```

### Staff authentication (sign in + sign up)

The UI is soft-gated: pages load without forcing a login redirect. The navbar shows **Log in** / **Sign up** when logged out, and email + **Log out** when signed in. Sessions persist via Supabase Auth (browser storage) so every page recognizes the same login. `/api/v1/*` still requires a Bearer JWT.

API token verification supports **both** modern asymmetric tokens (ES256/RS256 via `{SUPABASE_URL}/auth/v1/.well-known/jwks.json`) and legacy **HS256** tokens signed with `SUPABASE_JWT_SECRET`. No Dashboard algorithm change is required.

1. In Supabase Dashboard → **Authentication** → settings, **enable** “Allow new users to sign up” (public email/password sign-up).
2. Optionally disable email confirmation for local testing, or leave it on (the UI will ask users to confirm email when no session is returned after sign-up).
3. New Auth users get a `staff_profiles` row via trigger (`is_active = true`). Backfill is in `002_supabase_auth_rls.sql`.
4. Browse `http://127.0.0.1:8000/` without signing in (nav shows Log in / Sign up). Open `/login.html` or `/login.html?mode=signup` from the navbar.
5. Smoke checks:
   - Unauthenticated `GET /api/v1/groups` → **401** (UI shows “Sign in to view…” instead of redirecting)
   - Sign up / sign in → session recognized across pages; list/upload work
   - Failed sign-in with no matching account → UI switches to **Sign up**
   - `/health/live` and `/api/v1/public-config` stay public

RLS is defense-in-depth for direct Supabase/PostgREST access. FastAPI still uses a privileged `DATABASE_URL` and bypasses RLS; API security is JWT verification + `staff_profiles.is_active`.

**Never commit `.env`.** Rotate keys if they are ever exposed.
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
