# Telegram Job Radar

Personal local-first tool: ingest job posts from a private Telegram group, parse and score them, triage in a web inbox, export approved jobs to Google Sheets or CSV.

## Quick start

```bash
python -m venv .venv
.venv\Scripts\activate        # Windows
pip install -e ".[dev]"

copy .env.example .env
# See docs/env-setup.md for how to get each variable

mkdir data
python scripts/login.py       # One-time Telegram OTP login
python scripts/list_dialogs.py  # Find your group id
python scripts/backfill.py --limit 50

uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Open http://127.0.0.1:8000 (HTTP Basic Auth from `.env`).

## Configuration

See **[docs/env-setup.md](docs/env-setup.md)** for how to obtain every `.env` variable.

## Architecture

Single Python process: Telethon listener → in-process queue → pipeline worker → SQLite → FastAPI+HTMX inbox.

See [docs/](docs/) for full architecture freeze v3.1.

## Features

- Master-detail inbox with approve/reject
- Approved jobs page
- Batch enforcement (set your batch in Settings)
- Multi-job split (one Telegram message → multiple inbox items)
- Browse inbox by date or last N posts
- CSV export fallback; Google Sheets optional

## Tests

```bash
pytest
```

Golden parser fixtures: `tests/fixtures/posts/`.

## Scripts

| Script | Purpose |
|--------|---------|
| `scripts/login.py` | Telegram OTP authentication |
| `scripts/list_dialogs.py` | List chats and ids |
| `scripts/backfill.py` | Fetch historical messages (`--limit N`) |
| `scripts/reprocess.py` | Re-queue messages for pipeline |

## Backup

Copy `data/job_radar.db` weekly. Session file: `data/telegram.session`.

## License

MIT — see [LICENSE](LICENSE).
