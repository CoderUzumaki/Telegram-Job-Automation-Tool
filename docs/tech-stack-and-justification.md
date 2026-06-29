# Tech Stack & Justification

## Stack at a glance

| Layer | Technology | Version policy |
|-------|------------|----------------|
| Language | Python 3.11+ | Modern typing, asyncio |
| Telegram | Telethon | MTProto user session |
| Web framework | FastAPI | Async-native, OpenAPI |
| Templates | Jinja2 | Server-rendered HTML |
| Interactivity | HTMX | Partial page updates, no build step |
| Database | SQLite (WAL mode) | Local-first, single file |
| ORM | None — raw SQL via repository | Explicit ownership boundaries |
| Validation | Pydantic v2 | Extraction model, settings, LLM contracts |
| Config | pydantic-settings + `.env` | Secrets never in DB |
| LLM | Provider TBD (OpenAI-compatible) | Score + gap-fill only |
| Export | Google Sheets API + CSV | Sheets primary, CSV fallback |
| Testing | pytest | Golden fixtures, mocked LLM |
| CI | GitHub Actions | pytest on push |
| Package manager | uv or pip via `pyproject.toml` | Standard Python packaging |

## Justification by layer

### Telethon (not Bot API)

Private channels often block bots. User session access matches how the user already reads the channel. Trade-off: session file management and re-auth on expiry — mitigated via
health endpoint + `scripts/login.py`.

### SQLite (not Postgres)

- Single user, single process
- ~110k messages over 3 years is trivial for SQLite
- Local-first: copy `.db` file to backup
- WAL mode handles concurrent read (FastAPI) + write (ingest/worker)
- Postgres deferred until multi-process cloud deploy

### In-process asyncio.Queue (not Redis/Celery)

- One machine, one process
- Queue recovery via DB scan on startup + idle
- No operational overhead
- Graceful shutdown finishes in-flight work

### Parser in code (not DB-stored regex)

- Version controlled
- Golden test fixtures block ship
- `PARSER_VERSION` per message enables drift detection
- Runtime regex editing rejected — untested production patterns

### FastAPI + HTMX (not React SPA)

| Option | Verdict |
|--------|---------|
| FastAPI + HTMX | **Selected** — one process, no npm, master-detail natural |
| FastAPI + React SPA | Rejected MVP — build step for little gain |
| Next.js | Rejected — wrong scale, two services |

Alpine.js only if a specific interaction needs it. No component library required for MVP.

### Three state columns (not one status field)

v2 mistake: linear `pipeline_status` mixed processing, triage, and export. v3 uses orthogonal `processing_state`, `review_state`, `export_state` so failures in one dimension don't corrupt others.

### MessageRepository boundary

All SQL in `app/db/repository.py`. Method names encode ownership (ingest vs pipeline vs review vs export). Prevents components from writing forbidden columns.

## Rejected technologies

| Technology | Why rejected |
|------------|--------------|
| Redis | No distributed queue needed |
| Celery | Overkill for single process |
| Docker | Personal local tool; add later if needed |
| Postgres | Scale not justified |
| Bot API | Can't access private channel |
| Parser regex in DB | Untestable, no version control |
| FTS (MVP) | Inbox is small; defer to v1.1 |
| GraphQL | REST + HTMX sufficient |
| Separate dead_letter table | Column on messages enough for MVP |

## Environment variables (`.env`)

| Variable | Purpose |
|----------|---------|
| `TELEGRAM_API_ID` | Telegram app credentials |
| `TELEGRAM_API_HASH` | Telegram app credentials |
| `TELEGRAM_SESSION_PATH` | Path to `.session` file |
| `TELEGRAM_CHANNEL` | Target channel username/ID |
| `LLM_API_KEY` | Scoring provider |
| `LLM_MODEL` | Model name |
| `DATABASE_PATH` | SQLite file location |
| `DASHBOARD_USER` | HTTP Basic Auth username |
| `DASHBOARD_PASS` | HTTP Basic Auth password |
| `GOOGLE_SHEETS_*` | OAuth / spreadsheet ID (export) |
| `HOST` | Default `127.0.0.1` |
| `PORT` | Default `8000` |

## Security posture

| Asset | Control |
|-------|---------|
| Telegram `.session` | `.gitignore`, chmod 600, never log |
| API keys | `.env` only |
| SQLite file | User home dir, not repo |
| Dashboard | HTTP Basic Auth, localhost bind default |
| Logs | Never INFO-log `raw_text` (PII) |

## Performance expectations

| Metric | Target |
|--------|--------|
| Inbox query | Partial index on `review_state = 'inbox'` — always small |
| Approve → export | < 5 seconds |
| Daily ingest | ~100 posts/day |
| 3-year storage | ~110k messages, ~200MB disk |

## Related docs

- [architecture-freeze-v3.1.md](./architecture-freeze-v3.1.md)
- [design-system.md](./design-system.md) — UI implementation of HTMX choice
- [database-schema.md](./database-schema.md)
