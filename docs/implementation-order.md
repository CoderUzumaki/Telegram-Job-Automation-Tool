# Implementation Order

Frozen build sequence. **Do not skip gates.**

## Step 1 — Repo + migrations + repository tests

**Deliverables:**
- `pyproject.toml` with dependencies
- `app/db/migrations/001_initial.sql`
- `app/db/connection.py`
- `app/db/repository.py` — full MessageRepository contract
- `app/models/extraction.py`, `message.py`
- `tests/test_repository.py` — in-memory SQLite

**Gate:** Repository tests pass; schema matches [database-schema.md](./database-schema.md)

---

## Step 2 — Telethon login + backfill + links

**Deliverables:**
- `scripts/login.py` — OTP flow
- `scripts/backfill.py` — batch 100, interruptible
- `app/ingest/telethon_client.py`
- `app/ingest/link_extractor.py`
- `tests/test_links.py`

**Gate:** 50 real messages in DB with links extracted

---

## Step 3 — Parser + golden tests ⚠️ SHIP BLOCKER

**Deliverables:**
- `app/parsing/channel_parser.py` — `PARSER_VERSION` constant
- `tests/fixtures/posts/*.txt` — 10+ real posts
- `tests/test_parser.py` — golden assertions on `Extraction`

**Gate:** All golden parser tests pass  
**Blocked on:** User sample posts

**Rule:** Do not start Step 5 until this gate passes.

---

## Step 4 — Pipeline worker + filter + LLM

**Deliverables:**
- `app/pipeline/queue.py` — startup + idle recovery
- `app/pipeline/worker.py`
- `app/pipeline/keyword_filter.py`
- `app/pipeline/llm_scorer.py`
- `tests/test_filter.py`, `test_llm_scorer.py`

**Gate:** Messages reach `review_state=inbox` or `auto_skipped`

---

## Step 5 — HTMX inbox + approve/reject

**Deliverables:**
- `app/main.py` — lifespan hooks (listener + worker)
- `app/api/inbox.py`, `messages.py`
- `app/templates/` — base, inbox
- `app/static/style.css`

**Gate:** End-to-end triage without Sheets export

---

## Step 6 — Sheets export + CSV fallback

**Deliverables:**
- `app/export/sheets.py`
- `app/export/csv_export.py`
- Approve flow triggers export

**Gate:** Approve one post → appears in Sheet or CSV

---

## Step 7 — Settings UI + health endpoint

**Deliverables:**
- `app/api/settings.py`, `health.py`
- Settings template
- Seed bootstrap from `config/seed/`

**Gate:** Profile/rules editable; `/api/health` returns metrics

---

## Step 8 — README + backup docs

**Deliverables:**
- Root `README.md` — setup, run, re-auth, backup
- `.env.example`

**Gate:** New user can follow README to first approve

---

## Parallel work allowed

| Can run in parallel with | Task |
|--------------------------|------|
| Step 1 | Docs, `.env.example` draft |
| Step 2 | Design mockups (Stitch/v0) — no code |
| Step 4 | Export module scaffolding (mocked Sheets) |

## Not allowed

- HTMX UI before parser golden tests pass
- Parser patterns in database
- Raw SQL outside `repository.py`
- Redis/Celery/Docker for MVP
