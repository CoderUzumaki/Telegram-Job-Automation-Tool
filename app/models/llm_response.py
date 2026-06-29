from pydantic import BaseModel, Field

LLM_SCHEMA_VERSION = 1


class LLMScoreResponse(BaseModel):
    schema_version: int = Field(default=LLM_SCHEMA_VERSION)
    relevance_score: int = Field(ge=0, le=100)
    relevance_reason: str
    enrichments: dict = Field(default_factory=dict)
