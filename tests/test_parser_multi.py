from pathlib import Path

import pytest

from app.parsing.channel_parser import PARSER_VERSION, parse_message_multi

FIXTURES_DIR = Path(__file__).parent / "fixtures" / "posts"


def test_parser_version_is_2():
    assert PARSER_VERSION == 2


def test_referral_alert_splits_three_jobs():
    raw = (FIXTURES_DIR / "referral_alert_three_jobs.txt").read_text(encoding="utf-8")
    jobs = parse_message_multi(raw)
    assert len(jobs) == 3
    companies = [j.extraction.company.value for j in jobs]
    assert companies == ["Wipro", "Prototyping.io", "Zentrobyte Tech Pvt Ltd"]
    assert jobs[0].extraction.batch.value == "2025"
    assert jobs[2].extraction.role.value == "Software Development Intern (+PPO)"
    assert "Technical Skills" in jobs[0].job_description
    assert jobs[0].parser_matched is True
