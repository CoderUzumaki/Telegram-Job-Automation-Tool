import argparse
import asyncio
import logging

from app.config import settings
from app.db.connection import init_db
from app.db.repository import MessageRepository
from app.pipeline.queue import PipelineQueue
from app.pipeline.worker import PipelineWorker

logging.basicConfig(level=logging.INFO)


async def main(since_days: int) -> None:
    conn = init_db(settings.database_path)
    repo = MessageRepository(conn)
    queue = PipelineQueue(repo)
    worker = PipelineWorker(repo, queue)
    worker.start()

    if since_days:
        rows = conn.execute(
            "SELECT id FROM messages WHERE ingested_at >= datetime('now', ?)",
            (f"-{since_days} days",),
        ).fetchall()
        ids = [r["id"] for r in rows]
        for mid in ids:
            repo.reset_processing_for_retry(mid)
            await queue.enqueue(mid)
    else:
        await queue.recover_pending()

    await worker.stop()
    conn.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--since", type=int, default=7, help="Reprocess messages from last N days")
    args = parser.parse_args()
    asyncio.run(main(args.since))
