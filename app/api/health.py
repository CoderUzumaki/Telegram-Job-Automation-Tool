from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Request

router = APIRouter(prefix="/api/health", tags=["health"])


@router.get("")
async def health(request: Request):
    repo = request.app.state.repo
    listener = getattr(request.app.state, "listener", None)
    since = datetime.now(timezone.utc) - timedelta(hours=24)
    return {
        "last_telegram_sync_at": (
            listener.last_sync_at.isoformat() if listener and listener.last_sync_at else None
        ),
        "telegram_connected": listener.connected if listener else False,
        "messages_ingested_24h": repo.count_ingested_since(since),
        "inbox_count": repo.count_by_review_state("inbox"),
        "processing_pending_count": repo.count_by_processing_state("pending"),
        "processing_error_count": repo.count_by_processing_state("error"),
        "parser_match_rate_7d": round(repo.parser_match_rate_7d(), 3),
        "export_failed_count": repo.count_export_failed(),
    }
