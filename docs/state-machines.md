# State Machines

Three **orthogonal** state dimensions. Never combine into one `status` field.

## Processing state (pipeline worker owns)

```
pending → processing → ready
                    ↘ error → pending (retry under cap)
                              ↘ error (cap exceeded = dead letter)
```

| Value | Meaning |
|-------|---------|
| `pending` | Awaiting or retrying pipeline |
| `processing` | Worker claimed |
| `ready` | Parse + filter + score complete |
| `error` | Stage failed; may retry |

**Retry caps:** 3 attempts per stage (`parser_attempts`, `llm_attempts`)  
**Backoff:** 30s → 2m → 10m  
**Dead letter:** `processing_state=error` when stage cap exceeded  
**Manual retry:** UI resets failed stage counter → `pending`

Retry does **not** clear `review_state` if user already decided.

## Review state (pipeline sets initial; user sets final)

| Value | Set by | Meaning |
|-------|--------|---------|
| `none` | Default | Pipeline not finished |
| `inbox` | Pipeline | `ready` + filter passed + score ≥ threshold |
| `auto_skipped` | Pipeline | Filter failed or score below threshold |
| `approved` | User (FastAPI) | Accepted for export |
| `rejected` | User (FastAPI) | Dismissed |

User can override `auto_skipped → inbox` via skipped list (MVP: separate route; toggle post-MVP).

## Export state (FastAPI export flow owns)

| Value | Meaning |
|-------|---------|
| `none` | Not approved or not yet exported |
| `pending` | Approved, export in flight |
| `exported` | Sheet row written |
| `failed` | Sheets API failed — retry button |

**Approve flow:**
```
review_state = approved → export_state = pending → write Sheets → exported | failed
```

Export failures are independent: `approved` + `export_state=failed` stays approved.

**Export cap:** 5 attempts (`export_attempts`)

## Component write matrix

| State column | Telethon | Pipeline | FastAPI review | FastAPI export |
|--------------|----------|----------|----------------|----------------|
| `processing_state` | insert `pending` only | ✅ | ❌ | ❌ |
| `review_state` | ❌ | inbox, auto_skipped | approved, rejected | ❌ |
| `export_state` | ❌ | ❌ | triggers pending | exported, failed |

## Related

- [agent-guidelines.md](./agent-guidelines.md)
- [architecture-freeze-v3.1.md](./architecture-freeze-v3.1.md)
