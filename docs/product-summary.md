# Product Summary — Telegram Job Radar

## One-liner

A local-first personal tool that ingests job posts from a private Telegram channel, parses and scores them automatically, and presents a triage inbox where you approve relevant jobs for export to Google Sheets — without manually copying URLs or retyping fields.

## Problem

The user monitors a **private Telegram job channel** where:

- Posts cannot be copied easily
- Messaging is not allowed
- Volume is high (~100 posts/day)
- Each post contains labeled fields (Company, Role, Batch, etc.) plus application URLs

Current workflow wastes time scanning every post and manually typing URLs into a spreadsheet.

## Solution

```
Telegram channel → ingest + parse → keyword filter → LLM score → inbox triage → Sheets/CSV export
```

The user runs one local Python process. Approved jobs land in Google Sheets (or CSV fallback) with parsed fields and clickable links already filled in.

## Target user

Single user. Personal productivity tool. Runs on their machine. Not multi-tenant SaaS.

## Core user journey

1. **Setup** — Configure Telegram session, channel, job profile, filter rules
2. **Ingest** — New channel posts appear automatically (or via backfill)
3. **Triage** — Inbox shows ≤30 relevant posts/day sorted by relevance score
4. **Review** — Master-detail view: scan parsed fields, links, score reason
5. **Decide** — Approve (export) or reject
6. **Export** — Approved row written to Google Sheet; CSV if OAuth blocked

## Success criteria (MVP)

1. No manual URL typing for approved jobs
2. Inbox shows filtered subset (~≤30 relevant/day), not raw firehose
3. Approve → Sheet/CSV in under 5 seconds
4. Parser match rate visible; degraded mode catches non-template posts
5. Processing errors recoverable without data loss

## Minimum shippable product

> User runs one command → messages appear in local inbox with parsed fields + clickable links → user approves → row lands in Sheets or CSV.

## Explicitly out of scope (v3)

- Postgres, Redis, Celery, Docker
- React SPA / Next.js frontend
- Full-text search, embeddings, resume matching
- Multi-channel or multi-user
- Cloud deploy
- Link visit/applied CRM tracking
- Normalized company/role database tables

## Key product decisions (frozen)

| Decision | Choice |
|----------|--------|
| Telegram access | MTProto user session (Telethon), not Bot API |
| Source of truth | SQLite (local file) |
| Export sink | Google Sheets (+ CSV fallback) |
| Parser location | Code (`channel_parser.py`), not database |
| UI stack | FastAPI + Jinja2 + HTMX |
| Process model | Single Python process, in-process asyncio queue |
| Human in loop | Approve/reject before export |

## Related docs

- [architecture-freeze-v3.1.md](./architecture-freeze-v3.1.md)
- [implementation-order.md](./implementation-order.md)
- [design-system.md](./design-system.md)
