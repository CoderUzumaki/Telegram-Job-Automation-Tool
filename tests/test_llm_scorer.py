import pytest

from app.models.extraction import Extraction
from app.models.llm_response import LLMScoreResponse


def test_merge_llm_does_not_overwrite_parser():
    extraction = Extraction()
    extraction.company.value = "Google"
    extraction.company.source = "parser"
    extraction.location.value = None

    result = LLMScoreResponse(
        relevance_score=82,
        relevance_reason="Good fit",
        enrichments={"location": "Remote", "tags": ["ppo"]},
    )
    merged = extraction.merge_llm(result.enrichments)
    assert merged.company.value == "Google"
    assert merged.company.source == "parser"
    assert merged.location.value == "Remote"
    assert merged.location.source == "llm"
    assert "ppo" in merged.tags


def test_llm_schema_version():
    r = LLMScoreResponse(relevance_score=50, relevance_reason="ok")
    assert r.schema_version == 1
