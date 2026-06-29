import json
import logging

import httpx

from app.config import settings
from app.models.extraction import Extraction
from app.models.llm_response import LLM_SCHEMA_VERSION, LLMScoreResponse

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You score job posts for relevance to a candidate profile.
Return JSON only with schema_version, relevance_score (0-100), relevance_reason, and enrichments.
enrichments may include location and tags only for fields not already filled by the parser.
Never overwrite parser-provided field values."""


async def score_message(
    raw_text: str,
    extraction: Extraction,
    profile: dict,
) -> LLMScoreResponse:
    if not settings.llm_configured:
        return LLMScoreResponse(
            relevance_score=50,
            relevance_reason="LLM not configured; default score applied.",
            enrichments={},
        )

    payload = {
        "model": settings.llm_model,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": json.dumps(
                    {
                        "raw_text": raw_text,
                        "extraction": extraction.model_dump(),
                        "profile": profile,
                        "schema_version": LLM_SCHEMA_VERSION,
                    }
                ),
            },
        ],
        "temperature": 0.2,
        "response_format": {"type": "json_object"},
    }
    headers = {"Authorization": f"Bearer {settings.llm_api_key}"}
    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.post(f"{settings.llm_base_url.rstrip('/')}/chat/completions", json=payload, headers=headers)
        resp.raise_for_status()
        content = resp.json()["choices"][0]["message"]["content"]
    data = json.loads(content)
    result = LLMScoreResponse.model_validate(data)
    if result.schema_version != LLM_SCHEMA_VERSION:
        raise ValueError(f"Unsupported LLM schema version: {result.schema_version}")
    return result
