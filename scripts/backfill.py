import argparse
import asyncio
import logging

from app.config import settings
from app.db.connection import init_db
from app.db.repository import MessageRepository
from app.ingest.telethon_client import TelethonListener
from app.pipeline.queue import PipelineQueue
from app.pipeline.worker import PipelineWorker

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def main(limit: int) -> None:
    conn = init_db(settings.database_path)
    repo = MessageRepository(conn)
    queue = PipelineQueue(repo)
    worker = PipelineWorker(repo, queue)
    listener = TelethonListener(repo, queue)
    worker.start()
    count = await listener.backfill(limit=limit)
    logger.info("Backfilled %d messages", count)
    await worker.stop()
    conn.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=100)
    args = parser.parse_args()
    asyncio.run(main(args.limit))
