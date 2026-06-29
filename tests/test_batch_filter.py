import pytest

from app.pipeline.batch_filter import batch_matches, parse_batch_years


def test_parse_batch_years():
    assert parse_batch_years("2025/2026/2027") == {2025, 2026, 2027}


def test_batch_match_ok():
    ok, reason = batch_matches("2025", "2025/2026/2027")
    assert ok is True
    assert reason == ""


def test_batch_mismatch():
    ok, reason = batch_matches("2025", "2023/2024")
    assert ok is False
    assert "mismatch" in reason.lower()


def test_no_user_batch_passes():
    ok, _ = batch_matches(None, "2025")
    assert ok is True


def test_strict_empty_job_batch_fails():
    ok, reason = batch_matches("2025", None, strict=True)
    assert ok is False
