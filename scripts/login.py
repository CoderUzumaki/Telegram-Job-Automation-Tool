import asyncio
import json
import logging

from app.config import settings
from app.db.connection import init_db
from app.db.repository import MessageRepository
from app.ingest.telethon_client import TelethonListener
from app.pipeline.queue import PipelineQueue

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def main() -> None:
    from telethon import TelegramClient

    client = TelegramClient(
        str(settings.telegram_session_path),
        settings.telegram_api_id,
        settings.telegram_api_hash,
    )
    await client.start()
    logger.info("Telegram session saved to %s", settings.telegram_session_path)
    await client.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
