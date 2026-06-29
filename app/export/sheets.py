import logging

from app.config import settings
from app.models.message import Message

logger = logging.getLogger(__name__)


def export_to_sheets(msg: Message, sheet_id: str) -> str:
    """Export a message row to Google Sheets. Requires OAuth token file."""
    creds_path = settings.google_sheets_credentials_path
    token_path = settings.google_sheets_token_path
    if not creds_path.exists() or not token_path.exists():
        raise RuntimeError("Google Sheets credentials or token not configured")

    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build

    creds = Credentials.from_authorized_user_file(str(token_path))
    service = build("sheets", "v4", credentials=creds)
    e = msg.extraction
    values = [[
        msg.id,
        e.company.value or "",
        e.role.value or "",
        e.batch.value or "",
        e.stipend.value or "",
        e.location.value or "",
        ", ".join(e.tags),
        msg.relevance_score or "",
        msg.relevance_reason or "",
        " | ".join(l.url for l in msg.links),
    ]]
    result = (
        service.spreadsheets()
        .values()
        .append(
            spreadsheetId=sheet_id or settings.google_sheet_id,
            range="A1",
            valueInputOption="RAW",
            insertDataOption="INSERT_ROWS",
            body={"values": values},
        )
        .execute()
    )
    updates = result.get("updates", {})
    row = updates.get("updatedRange", "unknown")
    logger.info("Exported message %s to Sheets %s", msg.id, row)
    return row
