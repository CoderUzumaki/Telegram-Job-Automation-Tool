import json
import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.api import health, inbox, messages, settings as settings_api
from app.config import settings
from app.db.connection import init_db
from app.db.repository import MessageRepository
from app.ingest.telethon_client import TelethonListener
from app.pipeline.queue import PipelineQueue
from app.pipeline.worker import PipelineWorker

logger = logging.getLogger(__name__)

SEED_DIR = Path(__file__).resolve().parent.parent / "config" / "seed"


@asynccontextmanager
async def lifespan(app: FastAPI):
    logging.basicConfig(level=logging.INFO)
    conn = init_db(settings.database_path)
    repo = MessageRepository(conn)
    seeds = {
        "profile": json.loads((SEED_DIR / "profile.json").read_text(encoding="utf-8")),
        "filter_rules": json.loads((SEED_DIR / "filter_rules.json").read_text(encoding="utf-8")),
        "score_threshold": {"value": 65},
    }
    repo.bootstrap_settings(seeds)

    queue = PipelineQueue(repo)
    worker = PipelineWorker(repo, queue)
    listener = TelethonListener(repo, queue)

    app.state.conn = conn
    app.state.repo = repo
    app.state.queue = queue
    app.state.worker = worker
    app.state.listener = listener

    await queue.recover_pending()
    worker.start()
    try:
        await listener.start()
    except Exception:
        logger.exception("Telegram listener failed to start")

    yield

    await listener.stop()
    await worker.stop()
    conn.close()


def create_app() -> FastAPI:
    app = FastAPI(title="Telegram Job Radar", lifespan=lifespan)
    templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))
    app.state.templates = templates

    static_dir = Path(__file__).parent / "static"
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

    app.include_router(health.router)
    app.include_router(inbox.router)
    app.include_router(messages.router)
    app.include_router(settings_api.router)
    app.add_api_route("/settings", settings_api.settings_page, methods=["GET"], response_class=HTMLResponse)
    return app


app = create_app()
