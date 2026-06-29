# Environment Variables Setup

Copy `.env.example` to `.env` and fill in each variable.

## Telegram (required)

| Variable | How to get it |
|----------|----------------|
| `TELEGRAM_API_ID` | [my.telegram.org](https://my.telegram.org) → API development tools → App api_id |
| `TELEGRAM_API_HASH` | Same page → App api_hash |
| `TELEGRAM_SESSION_PATH` | Default `./data/telegram.session` — created by `python scripts/login.py` |
| `TELEGRAM_CHANNEL` | Group/channel id (e.g. `-1003808633277`), `@username`, or display name. Run `python scripts/list_dialogs.py` to list your chats. |

## Database

| Variable | Default |
|----------|---------|
| `DATABASE_PATH` | `./data/job_radar.db` (auto-created) |

## LLM (recommended)

| Variable | How to get it |
|----------|----------------|
| `LLM_API_KEY` | [OpenAI](https://platform.openai.com/api-keys), [OpenRouter](https://openrouter.ai/keys), or Groq |
| `LLM_BASE_URL` | `https://api.openai.com/v1` (or provider URL) |
| `LLM_MODEL` | e.g. `gpt-4o-mini` |

Without `LLM_API_KEY`, scoring defaults to 50.

## Dashboard

| Variable | Notes |
|----------|-------|
| `DASHBOARD_USER` | Choose any username for HTTP Basic Auth |
| `DASHBOARD_PASS` | Choose a strong password |
| `HOST` | Default `127.0.0.1` |
| `PORT` | Default `8000` |

## Google Sheets (optional)

| Variable | How to get it |
|----------|----------------|
| `GOOGLE_SHEETS_CREDENTIALS_PATH` | Google Cloud Console → OAuth Desktop client JSON |
| `GOOGLE_SHEETS_TOKEN_PATH` | Created after OAuth flow |
| `GOOGLE_SHEET_ID` | From spreadsheet URL: `/d/SHEET_ID/edit` |
| `CSV_EXPORT_PATH` | Default `./data/exports` (fallback when Sheets not configured) |

## Profile batch (settings UI)

Set your graduation batch year in **Settings → Your batch** (e.g. `2025`). Used for batch enforcement in the pipeline.
