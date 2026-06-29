import csv
import logging
from datetime import datetime, timezone
from pathlib import Path

from app.db.repository import MessageRepository
from app.models.message import Message

logger = logging.getLogger(__name__)

CSV_COLUMNS = [
    "id",
    "company",
    "role",
    "batch",
    "stipend",
    "location",
    "tags",
    "relevance_score",
    "relevance_reason",
    "links",
    "exported_at",
]


def _row_from_message(msg: Message) -> dict:
    e = msg.extraction
    return {
        "id": msg.id,
        "company": e.company.value or "",
        "role": e.role.value or "",
        "batch": e.batch.value or "",
        "stipend": e.stipend.value or "",
        "location": e.location.value or "",
        "tags": ", ".join(e.tags),
        "relevance_score": msg.relevance_score or "",
        "relevance_reason": msg.relevance_reason or "",
        "links": " | ".join(l.url for l in msg.links),
        "exported_at": datetime.now(timezone.utc).isoformat(),
    }


def export_message_to_csv(msg: Message, export_dir: Path) -> str:
    export_dir.mkdir(parents=True, exist_ok=True)
    path = export_dir / "approved_jobs.csv"
    write_header = not path.exists()
    with path.open("a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
        if write_header:
            writer.writeheader()
        writer.writerow(_row_from_message(msg))
    return str(path)


async def export_message(msg: Message, repo: MessageRepository, export_dir: Path, sheet_id: str) -> str:
    from app.export.sheets import export_to_sheets

    if sheet_id:
        try:
            row_id = export_to_sheets(msg, sheet_id)
            repo.mark_exported(msg.id, row_id)
            return row_id
        except Exception as exc:
            logger.warning("Sheets export failed, falling back to CSV: %s", exc)
    path = export_message_to_csv(msg, export_dir)
    repo.mark_exported(msg.id, f"csv:{path}")
    return f"csv:{path}"
