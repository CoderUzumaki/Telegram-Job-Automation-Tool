# Implementation Status

> **Last reviewed:** 2026-06-29  
**Architecture version:** v3.1 (frozen)  
**App version:** v2.1.0

## Overall progress

| Phase | Status |
|-------|--------|
| v1.0.0 GitHub release prep | Done (local git + tags; push requires `gh auth login`) |
| v1.1.0 UX: next-job nav, approved page, job description | Done |
| v1.2.0 Batch enforcement | Done |
| v2.0.0 Multi-job parser split | Done |
| v2.1.0 Browse modes (date / last N) | Done |

## Test status

```bash
pytest  # 26 passed
```

## Post-release actions for you

1. **Push to GitHub:**
   ```bash
   gh auth login
   gh repo create CoderUzumaki/Telegram-Job-Automation-Tool --public --source=. --remote=origin --push
   git push origin v1.0.0 v2.1.0
   ```
2. **Reprocess existing messages** (for multi-job split on old rows):
   ```bash
   python scripts/reprocess.py --since 30
   ```
3. **Set your batch** in Settings → Your batch (e.g. `2025`)

## Key changes in v2.1.0

- Multi-job referral alerts → separate inbox rows (`PARSER_VERSION=2`)
- Batch enforcement in pipeline
- Approve/reject advances to next job (HTMX OOB, no full reload)
- `/approved` page for accepted jobs
- Job description panel per parsed job
- Inbox filters: by date and last N posts
- `docs/env-setup.md` for all `.env` variables
