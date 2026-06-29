from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from app.models.extraction import Extraction

ProcessingState = Literal["pending", "processing", "ready", "error"]
ReviewState = Literal["none", "inbox", "auto_skipped", "approved", "rejected"]
ExportState = Literal["none", "pending", "exported", "failed"]
ErrorStage = Literal["parser", "filter", "llm"]


class Link(BaseModel):
    id: int | None = None
    message_id: int
    url: str
    domain: str
    position: int


class Message(BaseModel):
    id: int
    channel_id: str
    message_id: int
    job_index: int = 0
    posted_at: datetime
    ingested_at: datetime
    raw_text: str
    job_description: str | None = None
    extraction: Extraction = Field(default_factory=Extraction)
    parser_version: int = 0
    parser_matched: bool = False
    filter_passed: bool = False
    relevance_score: int | None = None
    relevance_reason: str | None = None
    profile_version_scored: int | None = None
    filter_rules_version_scored: int | None = None
    llm_schema_version: int | None = None
    processing_state: ProcessingState = "pending"
    processing_error: str | None = None
    last_error_stage: ErrorStage | None = None
    last_error_at: datetime | None = None
    parser_attempts: int = 0
    llm_attempts: int = 0
    review_state: ReviewState = "none"
    reviewed_at: datetime | None = None
    export_state: ExportState = "none"
    export_error: str | None = None
    export_attempts: int = 0
    sheet_row_id: str | None = None
    exported_at: datetime | None = None
    links: list[Link] = Field(default_factory=list)
