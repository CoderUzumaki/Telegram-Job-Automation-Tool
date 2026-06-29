# API Contract

REST JSON + HTMX HTML routes. All persistence via `MessageRepository`.

## Authentication

HTTP Basic Auth on all routes. Credentials from `DASHBOARD_USER` / `DASHBOARD_PASS` in `.env`.  
Default bind: `127.0.0.1`.

## REST endpoints

| Method | Path | Purpose | Owner |
|--------|------|---------|-------|
| GET | `/api/health` | Observability metrics | Read-only |
| GET | `/api/inbox` | `review_state=inbox`, sorted by score DESC | Read |
| GET | `/api/messages/{id}` | Detail view JSON | Read |
| POST | `/api/messages/{id}/approve` | Approve + trigger export | Review |
| POST | `/api/messages/{id}/reject` | Reject | Review |
| POST | `/api/messages/{id}/retry` | Reset processing for failed message | Review |
| POST | `/api/exports/{id}/retry` | Retry failed export | Export |
| GET | `/api/history` | Approved + rejected, paginated | Read (defer separate page MVP) |
| GET | `/api/skipped` | `auto_skipped`, paginated | Read (defer page MVP) |
| GET | `/api/settings/profile` | Get profile setting | Settings |
| PUT | `/api/settings/profile` | Update profile (increments version) | Settings |
| GET | `/api/settings/filter-rules` | Get filter rules | Settings |
| PUT | `/api/settings/filter-rules` | Update filter rules | Settings |
| GET | `/api/settings/score-threshold` | Get threshold | Settings |
| PUT | `/api/settings/score-threshold` | Update threshold | Settings |

No public CRUD on `messages`. No GraphQL.

## Health response fields (MVP)

```json
{
  "last_telegram_sync_at": "2026-06-29T10:00:00Z",
  "telegram_connected": true,
  "messages_ingested_24h": 42,
  "inbox_count": 12,
  "processing_pending_count": 3,
  "processing_error_count": 1,
  "parser_match_rate_7d": 0.87,
  "export_failed_count": 0
}
```

## HTMX HTML routes

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/` | Inbox master-detail |
| GET | `/history` | Archive (defer MVP — inbox tabs enough) |
| GET | `/settings` | Profile + filter rules + threshold |
| GET | `/health` | Status page (optional; JSON may suffice) |

## HTMX interaction patterns

| Action | Pattern |
|--------|---------|
| Select message in list | `hx-get="/api/messages/{id}"` → swap `#detail-panel` |
| Approve | `hx-post="/api/messages/{id}/approve"` → remove from list + toast |
| Reject | `hx-post="/api/messages/{id}/reject"` → remove from list |
| Retry processing | `hx-post="/api/messages/{id}/retry"` |
| Retry export | `hx-post="/api/exports/{id}/retry"` |
| Save settings | `hx-put` to settings endpoint → swap form confirmation |

Partial templates returned for HTMX swaps; full page on direct navigation.

## Inbox list item fields (display)

- Company, Role (from extraction)
- Relevance score (badge)
- Posted time (relative)
- Parser matched indicator (subtle)
- Link count

## Detail panel fields

- All extraction fields with source badge (parser / llm)
- Tags
- Relevance score + reason
- Raw text (collapsible)
- Links list (clickable, external)
- Approve / Reject buttons
- Export status if approved

## Related

- [design-system.md](./design-system.md)
- [architecture-freeze-v3.1.md](./architecture-freeze-v3.1.md)
