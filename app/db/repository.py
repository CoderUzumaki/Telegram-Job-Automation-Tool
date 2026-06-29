import json
import sqlite3
from datetime import datetime, timezone
from typing import Any

from app.models.extraction import Extraction
from app.models.message import Link, Message
from app.models.setting import Setting

UTC = timezone.utc


def _utcnow() -> datetime:
    return datetime.now(UTC)


def _dt_to_str(dt: datetime) -> str:
    return dt.astimezone(UTC).isoformat()


def _str_to_dt(value: str | None) -> datetime | None:
    if value is None:
        return None
    return datetime.fromisoformat(value)


def _row_to_message(row: sqlite3.Row, links: list[Link] | None = None) -> Message:
    extraction = Extraction.model_validate(json.loads(row["extraction"] or "{}"))
    keys = row.keys()
    return Message(
        id=row["id"],
        channel_id=row["channel_id"],
        message_id=row["message_id"],
        job_index=row["job_index"] if "job_index" in keys else 0,
        posted_at=_str_to_dt(row["posted_at"]),
        ingested_at=_str_to_dt(row["ingested_at"]),
        raw_text=row["raw_text"],
        job_description=row["job_description"] if "job_description" in keys else None,
        extraction=extraction,
        parser_version=row["parser_version"],
        parser_matched=bool(row["parser_matched"]),
        filter_passed=bool(row["filter_passed"]),
        relevance_score=row["relevance_score"],
        relevance_reason=row["relevance_reason"],
        profile_version_scored=row["profile_version_scored"],
        filter_rules_version_scored=row["filter_rules_version_scored"],
        llm_schema_version=row["llm_schema_version"],
        processing_state=row["processing_state"],
        processing_error=row["processing_error"],
        last_error_stage=row["last_error_stage"],
        last_error_at=_str_to_dt(row["last_error_at"]),
        parser_attempts=row["parser_attempts"],
        llm_attempts=row["llm_attempts"],
        review_state=row["review_state"],
        reviewed_at=_str_to_dt(row["reviewed_at"]),
        export_state=row["export_state"],
        export_error=row["export_error"],
        export_attempts=row["export_attempts"],
        sheet_row_id=row["sheet_row_id"],
        exported_at=_str_to_dt(row["exported_at"]),
        links=links or [],
    )


class MessageRepository:
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    def _fetch_links(self, message_id: int) -> list[Link]:
        rows = self.conn.execute(
            "SELECT id, message_id, url, domain, position FROM links WHERE message_id = ? ORDER BY position",
            (message_id,),
        ).fetchall()
        return [Link(id=r["id"], message_id=r["message_id"], url=r["url"], domain=r["domain"], position=r["position"]) for r in rows]

    def _get_row(self, message_id: int) -> sqlite3.Row | None:
        return self.conn.execute("SELECT * FROM messages WHERE id = ?", (message_id,)).fetchone()

    def get_by_id(self, message_id: int) -> Message | None:
        row = self._get_row(message_id)
        if not row:
            return None
        return _row_to_message(row, self._fetch_links(message_id))

    # --- Ingest ---

    def insert_message(
        self,
        channel_id: str,
        message_id: int,
        posted_at: datetime,
        raw_text: str,
    ) -> int | None:
        now = _utcnow()
        cursor = self.conn.execute(
            """
            INSERT OR IGNORE INTO messages (
                channel_id, message_id, posted_at, ingested_at, raw_text,
                extraction, processing_state, review_state, export_state
            ) VALUES (?, ?, ?, ?, ?, '{}', 'pending', 'none', 'none')
            """,
            (channel_id, message_id, _dt_to_str(posted_at), _dt_to_str(now), raw_text),
        )
        self.conn.commit()
        if cursor.rowcount == 0:
            existing = self.conn.execute(
                "SELECT id FROM messages WHERE channel_id = ? AND message_id = ? AND job_index = 0",
                (channel_id, message_id),
            ).fetchone()
            return existing["id"] if existing else None
        return cursor.lastrowid

    def insert_links(self, message_id: int, links: list[tuple[str, str, int]]) -> None:
        self.conn.execute("DELETE FROM links WHERE message_id = ?", (message_id,))
        for url, domain, position in links:
            self.conn.execute(
                "INSERT INTO links (message_id, url, domain, position) VALUES (?, ?, ?, ?)",
                (message_id, url, domain, position),
            )
        self.conn.commit()

    # --- Pipeline ---

    def claim_for_processing(self, message_id: int) -> Message | None:
        cursor = self.conn.execute(
            """
            UPDATE messages SET processing_state = 'processing'
            WHERE id = ? AND processing_state IN ('pending', 'error')
            """,
            (message_id,),
        )
        self.conn.commit()
        if cursor.rowcount == 0:
            return None
        row = self._get_row(message_id)
        if not row:
            return None
        return _row_to_message(row, self._fetch_links(message_id))

    def save_parse_result(
        self,
        message_id: int,
        extraction: Extraction,
        parser_matched: bool,
        parser_version: int,
        job_description: str | None = None,
    ) -> None:
        self.conn.execute(
            """
            UPDATE messages SET
                extraction = ?, parser_matched = ?, parser_version = ?, job_description = ?
            WHERE id = ?
            """,
            (
                json.dumps(extraction.model_dump()),
                int(parser_matched),
                parser_version,
                job_description,
                message_id,
            ),
        )
        self.conn.commit()

    def fan_out_jobs(self, parent_id: int, jobs: list, parser_version: int) -> list[int]:
        """Split one telegram row into multiple job rows. Returns list of message ids to process."""
        parent = self._get_row(parent_id)
        if not parent:
            return []
        if len(jobs) <= 1:
            job = jobs[0]
            self.save_parse_result(
                parent_id, job.extraction, job.parser_matched, parser_version, job.job_description
            )
            return [parent_id]

        ids: list[int] = []
        for i, job in enumerate(jobs):
            if i == 0:
                self.conn.execute(
                    """
                    UPDATE messages SET
                        extraction = ?, job_description = ?, parser_matched = ?, parser_version = ?,
                        job_index = 0
                    WHERE id = ?
                    """,
                    (
                        json.dumps(job.extraction.model_dump()),
                        job.job_description,
                        int(job.parser_matched),
                        parser_version,
                        parent_id,
                    ),
                )
                ids.append(parent_id)
            else:
                cursor = self.conn.execute(
                    """
                    INSERT INTO messages (
                        channel_id, message_id, job_index, posted_at, ingested_at, raw_text,
                        extraction, job_description, parser_matched, parser_version,
                        processing_state, review_state, export_state
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'processing', 'none', 'none')
                    """,
                    (
                        parent["channel_id"],
                        parent["message_id"],
                        i,
                        parent["posted_at"],
                        parent["ingested_at"],
                        parent["raw_text"],
                        json.dumps(job.extraction.model_dump()),
                        job.job_description,
                        int(job.parser_matched),
                        parser_version,
                    ),
                )
                ids.append(cursor.lastrowid)
        parent_links = self._fetch_links(parent_id)
        if parent_links:
            link_tuples = [(l.url, l.domain, l.position) for l in parent_links]
            for sid in ids[1:]:
                self.insert_links(sid, link_tuples)
        self.conn.commit()
        return ids

    def save_filter_result(self, message_id: int, filter_passed: bool) -> None:
        self.conn.execute(
            "UPDATE messages SET filter_passed = ? WHERE id = ?",
            (int(filter_passed), message_id),
        )
        self.conn.commit()

    def save_score_result(
        self,
        message_id: int,
        extraction: Extraction,
        score: int,
        reason: str,
        profile_ver: int,
        rules_ver: int,
        llm_schema_ver: int,
    ) -> None:
        self.conn.execute(
            """
            UPDATE messages SET
                extraction = ?, relevance_score = ?, relevance_reason = ?,
                profile_version_scored = ?, filter_rules_version_scored = ?,
                llm_schema_version = ?
            WHERE id = ?
            """,
            (
                json.dumps(extraction.model_dump()),
                score,
                reason,
                profile_ver,
                rules_ver,
                llm_schema_ver,
                message_id,
            ),
        )
        self.conn.commit()

    def mark_processing_error(self, message_id: int, stage: str, error: str) -> None:
        now = _dt_to_str(_utcnow())
        if stage == "parser":
            self.conn.execute(
                """
                UPDATE messages SET
                    processing_state = 'error', processing_error = ?,
                    last_error_stage = ?, last_error_at = ?, parser_attempts = parser_attempts + 1
                WHERE id = ?
                """,
                (error, stage, now, message_id),
            )
        elif stage == "llm":
            self.conn.execute(
                """
                UPDATE messages SET
                    processing_state = 'error', processing_error = ?,
                    last_error_stage = ?, last_error_at = ?, llm_attempts = llm_attempts + 1
                WHERE id = ?
                """,
                (error, stage, now, message_id),
            )
        else:
            self.conn.execute(
                """
                UPDATE messages SET
                    processing_state = 'error', processing_error = ?,
                    last_error_stage = ?, last_error_at = ?
                WHERE id = ?
                """,
                (error, stage, now, message_id),
            )
        self.conn.commit()

    def mark_processing_ready(self, message_id: int, review_state: str) -> None:
        self.conn.execute(
            """
            UPDATE messages SET processing_state = 'ready', review_state = ?
            WHERE id = ?
            """,
            (review_state, message_id),
        )
        self.conn.commit()

    def reset_processing_for_retry(self, message_id: int, stage: str | None = None) -> None:
        if stage == "parser":
            self.conn.execute(
                "UPDATE messages SET processing_state = 'pending', parser_attempts = 0, processing_error = NULL WHERE id = ?",
                (message_id,),
            )
        elif stage == "llm":
            self.conn.execute(
                "UPDATE messages SET processing_state = 'pending', llm_attempts = 0, processing_error = NULL WHERE id = ?",
                (message_id,),
            )
        else:
            self.conn.execute(
                """
                UPDATE messages SET
                    processing_state = 'pending', processing_error = NULL,
                    parser_attempts = 0, llm_attempts = 0
                WHERE id = ?
                """,
                (message_id,),
            )
        self.conn.commit()

    # --- Review ---

    def approve(self, message_id: int) -> Message | None:
        now = _dt_to_str(_utcnow())
        self.conn.execute(
            """
            UPDATE messages SET review_state = 'approved', reviewed_at = ?, export_state = 'pending'
            WHERE id = ? AND review_state IN ('inbox', 'auto_skipped')
            """,
            (now, message_id),
        )
        self.conn.commit()
        return self.get_by_id(message_id)

    def reject(self, message_id: int) -> Message | None:
        now = _dt_to_str(_utcnow())
        self.conn.execute(
            "UPDATE messages SET review_state = 'rejected', reviewed_at = ? WHERE id = ?",
            (now, message_id),
        )
        self.conn.commit()
        return self.get_by_id(message_id)

    # --- Export ---

    def mark_export_pending(self, message_id: int) -> None:
        self.conn.execute(
            "UPDATE messages SET export_state = 'pending' WHERE id = ?",
            (message_id,),
        )
        self.conn.commit()

    def mark_exported(self, message_id: int, sheet_row_id: str) -> None:
        now = _dt_to_str(_utcnow())
        self.conn.execute(
            """
            UPDATE messages SET export_state = 'exported', sheet_row_id = ?, exported_at = ?, export_error = NULL
            WHERE id = ?
            """,
            (sheet_row_id, now, message_id),
        )
        self.conn.commit()

    def mark_export_failed(self, message_id: int, error: str) -> None:
        self.conn.execute(
            """
            UPDATE messages SET export_state = 'failed', export_error = ?, export_attempts = export_attempts + 1
            WHERE id = ?
            """,
            (error, message_id),
        )
        self.conn.commit()

    # --- Read ---

    def get_inbox(
        self,
        limit: int = 100,
        offset: int = 0,
        posted_date: str | None = None,
        last_n: int | None = None,
    ) -> list[Message]:
        sql = "SELECT * FROM messages WHERE review_state = 'inbox'"
        params: list = []
        if posted_date:
            sql += " AND date(posted_at) = date(?)"
            params.append(posted_date)
        sql += " ORDER BY relevance_score DESC, posted_at DESC"
        if last_n is not None:
            sql += " LIMIT ?"
            params.append(last_n)
        else:
            sql += " LIMIT ? OFFSET ?"
            params.extend([limit, offset])
        rows = self.conn.execute(sql, params).fetchall()
        return [_row_to_message(r, self._fetch_links(r["id"])) for r in rows]

    def get_approved(self, limit: int = 100, offset: int = 0) -> list[Message]:
        rows = self.conn.execute(
            """
            SELECT * FROM messages WHERE review_state = 'approved'
            ORDER BY reviewed_at DESC LIMIT ? OFFSET ?
            """,
            (limit, offset),
        ).fetchall()
        return [_row_to_message(r, self._fetch_links(r["id"])) for r in rows]

    def resolve_post_action_selection(self, acted_id: int, prior_ids: list[int]) -> Message | None:
        """After approve/reject, pick next item at same list index or last available."""
        if acted_id in prior_ids:
            idx = prior_ids.index(acted_id)
        else:
            idx = 0
        new_inbox = self.get_inbox(limit=500)
        if not new_inbox:
            return None
        if idx < len(new_inbox):
            return new_inbox[idx]
        return new_inbox[-1]

    def get_skipped(self, limit: int = 50, offset: int = 0) -> list[Message]:
        rows = self.conn.execute(
            """
            SELECT * FROM messages WHERE review_state = 'auto_skipped'
            ORDER BY posted_at DESC LIMIT ? OFFSET ?
            """,
            (limit, offset),
        ).fetchall()
        return [_row_to_message(r, self._fetch_links(r["id"])) for r in rows]

    def get_history(self, limit: int = 50, offset: int = 0) -> list[Message]:
        rows = self.conn.execute(
            """
            SELECT * FROM messages WHERE review_state IN ('approved', 'rejected')
            ORDER BY reviewed_at DESC LIMIT ? OFFSET ?
            """,
            (limit, offset),
        ).fetchall()
        return [_row_to_message(r, self._fetch_links(r["id"])) for r in rows]

    def list_pending_for_recovery(self) -> list[int]:
        rows = self.conn.execute(
            "SELECT id FROM messages WHERE processing_state IN ('pending', 'error') ORDER BY posted_at ASC"
        ).fetchall()
        return [r["id"] for r in rows]

    def count_by_review_state(self, review_state: str) -> int:
        row = self.conn.execute(
            "SELECT COUNT(*) AS c FROM messages WHERE review_state = ?",
            (review_state,),
        ).fetchone()
        return row["c"]

    def count_by_processing_state(self, state: str) -> int:
        row = self.conn.execute(
            "SELECT COUNT(*) AS c FROM messages WHERE processing_state = ?",
            (state,),
        ).fetchone()
        return row["c"]

    def count_ingested_since(self, since: datetime) -> int:
        row = self.conn.execute(
            "SELECT COUNT(*) AS c FROM messages WHERE ingested_at >= ?",
            (_dt_to_str(since),),
        ).fetchone()
        return row["c"]

    def parser_match_rate_7d(self) -> float:
        row = self.conn.execute(
            """
            SELECT
                SUM(CASE WHEN parser_matched = 1 THEN 1 ELSE 0 END) AS matched,
                COUNT(*) AS total
            FROM messages
            WHERE ingested_at >= datetime('now', '-7 days')
            """
        ).fetchone()
        if not row or row["total"] == 0:
            return 0.0
        return row["matched"] / row["total"]

    def count_export_failed(self) -> int:
        row = self.conn.execute(
            "SELECT COUNT(*) AS c FROM messages WHERE export_state = 'failed'"
        ).fetchone()
        return row["c"]

    # --- Settings ---

    def get_setting(self, key: str) -> Setting | None:
        row = self.conn.execute("SELECT * FROM settings WHERE key = ?", (key,)).fetchone()
        if not row:
            return None
        return Setting(
            key=row["key"],
            value_json=json.loads(row["value_json"]),
            version=row["version"],
            updated_at=_str_to_dt(row["updated_at"]),
        )

    def put_setting(self, key: str, value_json: dict[str, Any]) -> Setting:
        now = _dt_to_str(_utcnow())
        existing = self.get_setting(key)
        version = (existing.version + 1) if existing else 1
        self.conn.execute(
            """
            INSERT INTO settings (key, value_json, version, updated_at)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(key) DO UPDATE SET
                value_json = excluded.value_json,
                version = excluded.version,
                updated_at = excluded.updated_at
            """,
            (key, json.dumps(value_json), version, now),
        )
        self.conn.commit()
        return Setting(key=key, value_json=value_json, version=version, updated_at=_str_to_dt(now))

    def bootstrap_settings(self, seeds: dict[str, dict[str, Any]]) -> None:
        for key, value in seeds.items():
            if self.get_setting(key) is None:
                self.put_setting(key, value)
