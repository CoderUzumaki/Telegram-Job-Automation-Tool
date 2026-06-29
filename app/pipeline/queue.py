import asyncio
import logging

from app.db.repository import MessageRepository

logger = logging.getLogger(__name__)


class PipelineQueue:
    def __init__(self, repo: MessageRepository):
        self.repo = repo
        self.queue: asyncio.Queue[int | None] = asyncio.Queue()
        self._shutdown = False

    async def enqueue(self, message_id: int) -> None:
        if not self._shutdown:
            await self.queue.put(message_id)

    async def enqueue_many(self, ids: list[int]) -> None:
        for mid in ids:
            await self.enqueue(mid)

    async def recover_pending(self) -> int:
        ids = self.repo.list_pending_for_recovery()
        await self.enqueue_many(ids)
        logger.info("Recovered %d pending messages", len(ids))
        return len(ids)

    def request_shutdown(self) -> None:
        self._shutdown = True

    async def get(self) -> int | None:
        if self._shutdown and self.queue.empty():
            return None
        try:
            return await asyncio.wait_for(self.queue.get(), timeout=2.0)
        except asyncio.TimeoutError:
            if self.queue.empty():
                await self.recover_pending()
            return None

    def task_done(self) -> None:
        self.queue.task_done()
