import logging
from datetime import timezone

from telethon import TelegramClient, events
from telethon.tl.types import Message as TgMessage

from app.config import settings
from app.db.repository import MessageRepository
from app.ingest.entity_resolver import peer_storage_id, resolve_chat_entity
from app.ingest.link_extractor import extract_links_from_text
from app.pipeline.queue import PipelineQueue

logger = logging.getLogger(__name__)


class TelethonListener:
    def __init__(self, repo: MessageRepository, queue: PipelineQueue):
        self.repo = repo
        self.queue = queue
        self.client: TelegramClient | None = None
        self._chat_entity = None
        self._chat_storage_id: str | None = None
        self.last_sync_at = None
        self.connected = False

    def _build_client(self) -> TelegramClient:
        return TelegramClient(
            str(settings.telegram_session_path),
            settings.telegram_api_id,
            settings.telegram_api_hash,
        )

    async def _ensure_chat(self) -> object:
        if not self.client:
            raise RuntimeError("Telegram client not started")
        if self._chat_entity is None:
            self._chat_entity = await resolve_chat_entity(self.client, settings.telegram_channel)
            self._chat_storage_id = str(self._chat_entity.id)
            logger.info("Using chat %s (storage id %s)", settings.telegram_channel, self._chat_storage_id)
        return self._chat_entity

    async def start(self) -> None:
        if not settings.telegram_api_id or not settings.telegram_channel:
            logger.warning("Telegram not configured; listener disabled")
            return
        self.client = self._build_client()
        await self.client.start()
        self.connected = True
        chat = await self._ensure_chat()

        @self.client.on(events.NewMessage(chats=chat))
        async def handler(event: events.NewMessage.Event) -> None:
            await self._handle_message(event.message)

        logger.info("Telethon listener started for %s", settings.telegram_channel)

    async def stop(self) -> None:
        if self.client:
            await self.client.disconnect()
            self.connected = False

    async def _handle_message(self, message: TgMessage) -> None:
        if not message.text:
            return
        posted = message.date
        if posted.tzinfo is None:
            posted = posted.replace(tzinfo=timezone.utc)
        channel_id = peer_storage_id(message.peer_id, self._chat_storage_id or settings.telegram_channel)
        mid = self.repo.insert_message(channel_id, message.id, posted, message.text)
        if mid is None:
            return
        links = extract_links_from_text(message.text)
        if links:
            self.repo.insert_links(mid, links)
        await self.queue.enqueue(mid)
        self.last_sync_at = posted
        logger.info("Ingested message %s", mid)

    async def backfill(self, limit: int = 100) -> int:
        if not self.client:
            self.client = self._build_client()
            await self.client.start()
            self.connected = True
        chat = await self._ensure_chat()
        count = 0
        batch_ids: list[int] = []
        async for message in self.client.iter_messages(chat, limit=limit):
            if not message.text:
                continue
            posted = message.date
            if posted.tzinfo is None:
                posted = posted.replace(tzinfo=timezone.utc)
            channel_id = peer_storage_id(message.peer_id, self._chat_storage_id or settings.telegram_channel)
            mid = self.repo.insert_message(channel_id, message.id, posted, message.text)
            if mid is None:
                continue
            links = extract_links_from_text(message.text)
            if links:
                self.repo.insert_links(mid, links)
            batch_ids.append(mid)
            count += 1
            if len(batch_ids) >= 100:
                await self.queue.enqueue_many(batch_ids)
                batch_ids = []
        if batch_ids:
            await self.queue.enqueue_many(batch_ids)
        self.last_sync_at = None
        logger.info("Backfill complete: %d messages", count)
        return count
