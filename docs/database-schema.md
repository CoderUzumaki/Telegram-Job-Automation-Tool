# Database Schema Reference

Extracted from Architecture Freeze v3.1. Migrations live in `app/db/migrations/`.

## PRAGMA

```sql
PRAGMA journal_mode=WAL;
PRAGMA foreign_keys=ON;
```

## Table: `messages`

| Column | Type | Notes |
|--------|------|-------|
| `id` | INTEGER PK | |
| `channel_id` | TEXT | Dedup with message_id |
| `message_id` | INTEGER | Dedup with channel_id |
| `posted_at` | TIMESTAMP | From Telegram |
| `ingested_at` | TIMESTAMP | |
| `raw_text` | TEXT | Immutable after ingest |
| `extraction` | TEXT (JSON) | Merged parsed + field_sources |
| `parser_version` | INTEGER | From code constant |
| `parser_matched` | BOOLEAN | Drift metric |
| `filter_passed` | BOOLEAN | |
| `relevance_score` | INTEGER NULL | 0–100 |
| `relevance_reason` | TEXT NULL | |
| `profile_version_scored` | INTEGER NULL | Settings snapshot |
| `filter_rules_version_scored` | INTEGER NULL | Settings snapshot |
| `llm_schema_version` | INTEGER NULL | |
| `processing_state` | TEXT | `pending` \| `processing` \| `ready` \| `error` |
| `processing_error` | TEXT NULL | |
| `last_error_stage` | TEXT NULL | `parser` \| `filter` \| `llm` |
| `last_error_at` | TIMESTAMP NULL | |
| `parser_attempts` | INTEGER | Max 3 |
| `llm_attempts` | INTEGER | Max 3 |
| `review_state` | TEXT | `none` \| `inbox` \| `auto_skipped` \| `approved` \| `rejected` |
| `reviewed_at` | TIMESTAMP NULL | |
| `export_state` | TEXT | `none` \| `pending` \| `exported` \| `failed` |
| `export_error` | TEXT NULL | |
| `export_attempts` | INTEGER | Max 5 |
| `sheet_row_id` | TEXT NULL | |
| `exported_at` | TIMESTAMP NULL | |

## Table: `links`

| Column | Type | Notes |
|--------|------|-------|
| `id` | INTEGER PK | |
| `message_id` | INTEGER FK | → messages.id |
| `url` | TEXT | Normalized |
| `domain` | TEXT | Display/sort |
| `position` | INTEGER | Order in message |

`link_type`, `visited`, `applied` — deferred post-MVP.

## Table: `settings`

| Column | Type | Notes |
|--------|------|-------|
| `key` | TEXT PK | `profile`, `filter_rules`, `score_threshold` |
| `value_json` | TEXT | Document body |
| `version` | INTEGER | Incremented on every PUT |
| `updated_at` | TIMESTAMP | |

Bootstrap from `config/seed/*.json` on first run.

## Indexes

```sql
CREATE UNIQUE INDEX idx_messages_channel_msg ON messages(channel_id, message_id);
CREATE INDEX idx_messages_inbox ON messages(review_state, relevance_score DESC)
  WHERE review_state = 'inbox';
CREATE INDEX idx_messages_pipeline ON messages(processing_state)
  WHERE processing_state IN ('pending', 'error');
CREATE INDEX idx_messages_posted ON messages(posted_at DESC);
CREATE INDEX idx_links_message ON links(message_id);
```

## Extraction model (Pydantic)

```python
class ExtractedField(BaseModel):
    value: str | None = None
    source: Literal["parser", "llm", "manual"] | None = None

class Extraction(BaseModel):
    company: ExtractedField = Field(default_factory=ExtractedField)
    role: ExtractedField = Field(default_factory=ExtractedField)
    batch: ExtractedField = Field(default_factory=ExtractedField)
    stipend: ExtractedField = Field(default_factory=ExtractedField)
    location: ExtractedField = Field(default_factory=ExtractedField)
    tags: list[str] = []
```

### Storage example

```json
{
  "company": {"value": "Google", "source": "parser"},
  "role": {"value": "SDE", "source": "parser"},
  "batch": {"value": "2024", "source": "parser"},
  "stipend": {"value": null, "source": null},
  "location": {"value": "Remote", "source": "llm"},
  "tags": ["ppo", "remote"]
}
```

## FTS

Deferred post-MVP. Inbox uses partial index; history search via LIKE until v1.1.

## Related

- [state-machines.md](./state-machines.md)
- [architecture-freeze-v3.1.md](./architecture-freeze-v3.1.md)
