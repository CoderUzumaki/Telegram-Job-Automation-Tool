import asyncio
import logging

from app.db.repository import MessageRepository
from app.models.llm_response import LLM_SCHEMA_VERSION
from app.parsing.channel_parser import PARSER_VERSION, parse_message_multi
from app.pipeline.batch_filter import batch_matches
from app.pipeline.keyword_filter import passes_filter
from app.pipeline.llm_scorer import score_message
from app.pipeline.queue import PipelineQueue

logger = logging.getLogger(__name__)

MAX_PARSER_ATTEMPTS = 3
MAX_LLM_ATTEMPTS = 3
BACKOFF_SECONDS = [30, 120, 600]


class PipelineWorker:
    def __init__(self, repo: MessageRepository, queue: PipelineQueue):
        self.repo = repo
        self.queue = queue
        self._task: asyncio.Task | None = None

    def start(self) -> None:
        self._task = asyncio.create_task(self._run())

    async def stop(self) -> None:
        self.queue.request_shutdown()
        if self._task:
            await self._task

    async def _run(self) -> None:
        while True:
            message_id = await self.queue.get()
            if message_id is None:
                break
            try:
                await self._process(message_id)
            except Exception:
                logger.exception("Unexpected pipeline error for message %s", message_id)
            finally:
                self.queue.task_done()

    async def _process(self, message_id: int) -> None:
        msg = self.repo.claim_for_processing(message_id)
        if not msg:
            return

        try:
            jobs = parse_message_multi(msg.raw_text)
            job_ids = self.repo.fan_out_jobs(message_id, jobs, PARSER_VERSION)
        except Exception as exc:
            self._handle_stage_error(message_id, "parser", str(exc), msg.parser_attempts)
            return

        for jid in job_ids:
            await self._process_stages(jid)

    async def _process_stages(self, message_id: int) -> None:
        msg = self.repo.get_by_id(message_id)
        if not msg:
            return

        filter_rules = self.repo.get_setting("filter_rules")
        rules = filter_rules.value_json if filter_rules else {"include": [], "exclude": []}
        try:
            passed = passes_filter(msg.raw_text, rules)
            self.repo.save_filter_result(message_id, passed)
        except Exception as exc:
            self._handle_stage_error(message_id, "filter", str(exc), 0)
            return

        if not passed:
            self.repo.mark_processing_ready(message_id, "auto_skipped")
            return

        profile_setting = self.repo.get_setting("profile")
        profile = profile_setting.value_json if profile_setting else {}
        user_batch = profile.get("batch")
        strict_batch = profile.get("strict_batch", True)
        job_batch = msg.extraction.batch.value
        batch_ok, batch_reason = batch_matches(user_batch, job_batch, strict=strict_batch)
        if not batch_ok:
            self.repo.save_score_result(
                message_id,
                msg.extraction,
                0,
                batch_reason,
                profile_setting.version if profile_setting else 0,
                filter_rules.version if filter_rules else 0,
                LLM_SCHEMA_VERSION,
            )
            self.repo.mark_processing_ready(message_id, "auto_skipped")
            return

        threshold_setting = self.repo.get_setting("score_threshold")
        threshold = threshold_setting.value_json.get("value", 65) if threshold_setting else 65

        try:
            result = await score_message(msg.raw_text, msg.extraction, profile)
            merged = msg.extraction.merge_llm(result.enrichments)
            profile_ver = profile_setting.version if profile_setting else 0
            rules_ver = filter_rules.version if filter_rules else 0
            self.repo.save_score_result(
                message_id,
                merged,
                result.relevance_score,
                result.relevance_reason,
                profile_ver,
                rules_ver,
                LLM_SCHEMA_VERSION,
            )
            review = "inbox" if result.relevance_score >= threshold else "auto_skipped"
            self.repo.mark_processing_ready(message_id, review)
        except Exception as exc:
            self._handle_stage_error(message_id, "llm", str(exc), msg.llm_attempts)

    def _handle_stage_error(self, message_id: int, stage: str, error: str, attempts: int) -> None:
        self.repo.mark_processing_error(message_id, stage, error)
        msg = self.repo.get_by_id(message_id)
        if not msg:
            return
        cap = MAX_PARSER_ATTEMPTS if stage == "parser" else MAX_LLM_ATTEMPTS
        current = msg.parser_attempts if stage == "parser" else msg.llm_attempts
        if current < cap:
            delay = BACKOFF_SECONDS[min(current - 1, len(BACKOFF_SECONDS) - 1)]
            asyncio.create_task(self._retry_later(message_id, delay))

    async def _retry_later(self, message_id: int, delay: int) -> None:
        await asyncio.sleep(delay)
        self.repo.conn.execute(
            "UPDATE messages SET processing_state = 'pending' WHERE id = ? AND processing_state = 'error'",
            (message_id,),
        )
        self.repo.conn.commit()
        await self.queue.enqueue(message_id)
