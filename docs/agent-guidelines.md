# Agent Guidelines

Instructions for AI agents working on Telegram Job Radar.

## Before you code

1. Read [implementation-status.md](./implementation-status.md) — don't redo completed work
2. Read [architecture-freeze-v3.1.md](./architecture-freeze-v3.1.md) — frozen decisions are not suggestions
3. Confirm your task's step in [implementation-order.md](./implementation-order.md) and its gate
4. If task touches UI and parser golden tests don't pass → **stop and warn user**

## Ownership boundaries (critical)

| Component | May write | Must NEVER write |
|-----------|-----------|------------------|
| Telethon ingest | New rows: `raw_text`, links, `processing_state=pending` | `processing_state` beyond insert, `review_state`, `export_state`, `extraction` |
| Pipeline worker | `processing_state`, `extraction`, `filter_passed`, `relevance_*`, `review_state` (inbox/auto_skipped), parser fields, processing errors/retries | `review_state` approved/rejected, `export_state` |
| FastAPI (approve/reject) | `review_state`, `reviewed_at` | `processing_state`, `extraction` |
| FastAPI (export) | `export_state`, `sheet_row_id`, `exported_at`, `export_attempts`, export errors | `processing_state`, parser/LLM retry counters |

**All DB access** goes through `MessageRepository` in `app/db/repository.py`. No raw SQL elsewhere.

## Code conventions

- Use Pydantic `Extraction` model in pipeline — never raw dicts
- Bump `PARSER_VERSION` when parser patterns change; add golden test
- Never INFO-log `raw_text`
- Parser regex lives in `channel_parser.py` only
- Settings in DB; secrets in `.env`
- Match existing file layout from architecture spec

## Testing requirements

| Change type | Required tests |
|-------------|----------------|
| Parser change | Golden fixture + bump `PARSER_VERSION` |
| Filter change | Unit tests in `test_filter.py` |
| Repository change | Integration test in `test_repository.py` |
| LLM merge logic | Mocked test in `test_llm_scorer.py` |

CI runs pytest without Telegram/LLM network calls.

## Graceful shutdown

On SIGINT/SIGTERM:
1. Stop Telegram events
2. Set shutdown flag on worker queue
3. Finish current pipeline/export
4. Commit and close SQLite
5. Exit

Coordinate via Uvicorn lifespan hooks in `app/main.py`.

## Queue recovery (two triggers)

1. **Startup** — `list_pending_for_recovery()` → enqueue
2. **Idle** — when queue empty, scan again before sleep

## When updating docs

| Change | Update |
|--------|--------|
| Completed task | `implementation-status.md` |
| Architecture decision | `architecture-freeze-v3.1.md` + version bump |
| New API endpoint | `api-contract.md` |
| Schema change | `database-schema.md` + new migration SQL |

## Common mistakes to avoid

- Single `status` column instead of three state dimensions
- Storing parser regex in `settings` table
- Building React/Next.js frontend for MVP
- Adding Redis/Celery "for scalability"
- Starting UI before parser golden tests
- Overwriting parser extraction values with LLM enrichments

## MessageRepository method reference

See [architecture-freeze-v3.1.md](./architecture-freeze-v3.1.md#messagerepository-contract-frozen) for the full contract.

## Questions to ask the user

- Before parser work: "Do you have sample posts for fixtures?"
- Before export: "What Google Sheet columns do you want?"
- Before LLM integration: "Which provider/model?"

Do not ask about frozen architecture decisions unless user explicitly wants to unfreeze.
