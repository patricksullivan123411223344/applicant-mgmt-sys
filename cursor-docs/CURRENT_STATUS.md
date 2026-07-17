# What We’ve Built — Current Status

**Last updated:** July 17, 2026  
**Project:** Student Housing Application Processing System (`housing_processor`)

This note is a plain-language snapshot of the codebase as it stands today: what works, how it’s organized, and what still needs to be done. Detailed design lives in [`PROJECT_OVERVIEW.md`](PROJECT_OVERVIEW.md) and [`SYSTEM_ARCHITECTURE.md`](SYSTEM_ARCHITECTURE.md).

---

## One-sentence summary

We have a **working scaffold**: upload a `.docx`, store it, record it in Supabase (or local SQLite), and run a process pipeline that ends in “needs review.” Real field extraction, group assignment, Excel export, and staff review UI are **not finished yet**.

---

## How to run it

```bash
uv sync --extra dev
uv run alembic upgrade head   # or stamp head if schema was applied via SQL
uv run uvicorn housing_processor.main:app --reload
```

| URL | What it is |
| --- | --- |
| [http://127.0.0.1:8000/](http://127.0.0.1:8000/) | Ops UI (upload + health) |
| [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs) | Swagger API docs |
| [http://127.0.0.1:8000/health/live](http://127.0.0.1:8000/health/live) | Liveness |
| [http://127.0.0.1:8000/health/ready](http://127.0.0.1:8000/health/ready) | DB + storage readiness |

---

## Architecture (how the pieces fit)

The app is a **modular monolith** with clear layers. The database is the source of truth; Word files are inputs; Excel will be a generated output.

```text
Browser (frontend/)
    │
    ▼
FastAPI  presentation/api   ← HTTP only; no business rules
    │
    ▼
Application handlers        ← use cases (ingest, process)
    │
    ├── Domain              ← entities, statuses, match types (no FastAPI/SQLAlchemy)
    │
    └── Infrastructure      ← Postgres/SQLite, DOCX, Excel, storage, optional Supabase client
```

**Important invariants already encoded:**

- Domain logic does not import FastAPI or SQLAlchemy.
- LLMs (when enabled later) may propose extraction; they do not write to the DB or assign group numbers.
- Group numbers are allocated by the database (`SEQUENCE` on Postgres), never `MAX(n)+1` in Python.
- Ambiguous matches are allowed to become `review_required`.

Composition root: [`src/housing_processor/bootstrap.py`](../src/housing_processor/bootstrap.py).

---

## What’s on disk

| Area | Location |
| --- | --- |
| Backend package | `src/housing_processor/` |
| Ops UI | `frontend/` (HTML / CSS / JS) |
| Design docs | `cursor-docs/` |
| SQL mirror for Supabase | `scripts/sql/001_supabase_schema.sql` |
| Process CLI | `scripts/process_application.py` |
| Tests | `tests/` (smoke tests today) |
| Config | `.env` / `.env.example` |

---

## What works today

### Upload and storage

- Staff can upload a `.docx` from the UI or `POST /api/v1/applications`.
- File is hashed (SHA-256); duplicates are detected.
- Original file is archived under local storage (`STORAGE_ROOT`).
- An `applications` row is created with status `received`.

### Processing pipeline (orchestration only)

- `POST /api/v1/applications/{id}/reprocess` (or the CLI) runs the process handler.
- Status moves through extraction → matching and currently lands on **`review_required`**.
- DOCX **text** is read with `python-docx`.
- Field mapping, identity matching, and group attachment are **stubs** (they defer to human review).

### Database

- Full Phase-oriented schema is applied (Supabase Postgres via session pooler, or local SQLite).
- Tables include applications, applicants, groups, members, pending roommate refs, properties, preferences, reviews, audit, outbox, excel export history.
- Alembic revisions: `0001_initial`, `0002_postgres_domains` (stamped on Supabase if SQL was applied manually).

### Frontend

- System live/ready/version indicators.
- DOCX upload with JSON result (including duplicate handling).
- Links to API docs and health endpoints.

### Tooling

- Python 3.12+, `uv`, FastAPI, SQLAlchemy 2, Alembic, Pydantic, openpyxl, python-docx.
- Optional Supabase API client when `SUPABASE_URL` + service role key are set (persistence still uses `DATABASE_URL` + SQLAlchemy).

---

## What’s stubbed or incomplete

| Capability | Status |
| --- | --- |
| Deterministic field extraction from DOCX | Stub — returns empty / placeholder applicant |
| Identity resolution (email/phone) | Stub — always “new / review” |
| Automatic group matching | Stub — always `REVIEW_REQUIRED` |
| Creating review queue rows | Not wired in process path |
| Manual attach / create group APIs | Mostly `501 Not Implemented` |
| Group number allocation in process flow | Sequence exists; not used yet |
| Excel export API | Accepts request but does not write a real workbook |
| Excel renderer | Code exists; not connected to the export endpoint |
| List endpoints (apps, groups, reviews) | Return empty pages |
| Auth / roles | Fixed “dev” actor only |
| LLM extraction | Disabled (`LLM_ENABLED=false`); no-op adapter |
| Audit / outbox writes on ingest/process | Models exist; not written on the happy path |
| Streamlit dashboard | Package placeholder only |
| Background job queue | Sync / in-process only |

---

## API cheat sheet

**Useful now**

- `POST /api/v1/applications` — upload
- `GET /api/v1/applications/{id}` — fetch one
- `POST /api/v1/applications/{id}/reprocess` — run pipeline
- `GET /health/live`, `GET /health/ready`
- `GET /api/v1/system/version`

**Scaffold / empty list**

- `GET /api/v1/applications|applicants|groups|reviews|exports`

**Explicitly not implemented (`501`)**

- Correct extracted data, most group mutations, review resolve/dismiss, export download, etc.

Full shapes: Swagger at `/docs` and architecture §11.

---

## Delivery phases — progress

From [`PROJECT_OVERVIEW.md`](PROJECT_OVERVIEW.md):

### Phase 1 — Deterministic MVP

| Item | Progress |
| --- | --- |
| Manual DOCX upload | Done |
| Original-file archival | Done |
| Duplicate-file detection | Done |
| Deterministic field extraction | Not done |
| Database (SQLite / Postgres) | Done |
| Manual group selection / correction | Not done |
| Permanent sequential group numbering | Schema only |
| Excel with grouped rows + bold contacts | Renderer only |

### Phase 2 — Intelligent matching

Schema placeholders exist. Scoring, pending-roommate logic, LLM extraction, and a real review queue are **not built**.

### Phase 3 — Operational hardening

Auth, real background workers, audit UI, backups, metrics, regression fixtures — **not started**.

### Phase 4 — Integrations

Email ingest, Barefoot CRM, alerts — **not started**.

---

## Suggested next work (in order)

Finish Phase 1 before investing in LLM matching:

1. **Deterministic DOCX extraction** — map known labels/tables into `ExtractedApplicationContract`.
2. **Persist extracted / validated applicants** and create **review items** when review is required.
3. **Manual group APIs + UI** — attach to existing group or create group (allocating `nextval('group_number_seq')`).
4. **Wire Excel export** — build projection from DB, call `OpenpyxlExcelRenderer`, store file, download endpoint.
5. **List views** — applications and groups in the frontend for day-to-day ops.
6. Then Phase 2: identity resolution, roommate references, scoring, optional LLM assist.

---

## Docs still missing

Architecture recommended these follow-ups; only the overview and architecture files exist so far:

- `REQUIREMENTS.md`, `DATABASE_SCHEMA.md`, `DOCX_EXTRACTION_PIPELINE.md`
- `IDENTITY_AND_GROUP_MATCHING.md`, `LLM_INTEGRATION.md`, `EXCEL_EXPORT_SPEC.md`
- `REVIEW_DASHBOARD.md`, `SECURITY_AND_PRIVACY.md`, `TESTING_STRATEGY.md`, `IMPLEMENTATION_ROADMAP.md`

---

## Bottom line

**Foundation is in place:** layered backend, Supabase-ready schema, upload path, process orchestration, and a small ops UI.

**Phase 1 product outcomes are not:** staff still cannot rely on the system to extract fields, assign group numbers, resolve reviews, or produce the Excel workbook from the database.

Treat this repo as a **build-ready scaffold**, not a finished operations tool, until the Phase 1 checklist above is closed.
