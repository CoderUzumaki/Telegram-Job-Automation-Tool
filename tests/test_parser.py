import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from app.db.connection import init_db
from app.db.repository import MessageRepository
from app.models.extraction import Extraction
from app.parsing.channel_parser import parse_message, PARSER_VERSION

FIXTURES_DIR = Path(__file__).parent / "fixtures" / "posts"


@pytest.fixture
def repo(tmp_path):
    conn = init_db(tmp_path / "test.db")
    return MessageRepository(conn)


def test_golden_parser_fixtures():
    txt_files = sorted(
        p for p in FIXTURES_DIR.glob("*.txt") if p.with_suffix(".expected.json").exists()
    )
    assert len(txt_files) >= 9, "Expected at least 9 golden parser fixtures"
    for txt_path in txt_files:
        expected_path = txt_path.with_suffix(".expected.json")
        assert expected_path.exists(), f"Missing expected file for {txt_path.name}"
        raw = txt_path.read_text(encoding="utf-8")
        expected = json.loads(expected_path.read_text(encoding="utf-8"))
        extraction, matched = parse_message(raw)
        assert matched, f"Parser should match {txt_path.stem}"
        assert extraction.model_dump() == expected, txt_path.stem


def test_parser_version_constant():
    assert PARSER_VERSION == 2


def test_insert_message_dedup(repo: MessageRepository):
    posted = datetime(2026, 1, 1, tzinfo=timezone.utc)
    id1 = repo.insert_message("ch1", 100, posted, "hello")
    id2 = repo.insert_message("ch1", 100, posted, "hello again")
    assert id1 is not None
    assert id2 == id1


def test_claim_for_processing(repo: MessageRepository):
    posted = datetime(2026, 1, 1, tzinfo=timezone.utc)
    mid = repo.insert_message("ch1", 101, posted, "job post")
    claimed = repo.claim_for_processing(mid)
    assert claimed is not None
    assert claimed.processing_state == "processing"
    assert repo.claim_for_processing(mid) is None


def test_pipeline_to_inbox(repo: MessageRepository):
    posted = datetime(2026, 1, 1, tzinfo=timezone.utc)
    mid = repo.insert_message("ch1", 102, posted, "Company - Acme\nRole - SDE")
    repo.claim_for_processing(mid)
    extraction = Extraction()
    extraction.company.value = "Acme"
    extraction.company.source = "parser"
    extraction.role.value = "SDE"
    extraction.role.source = "parser"
    repo.save_parse_result(mid, extraction, True, PARSER_VERSION)
    repo.save_filter_result(mid, True)
    repo.save_score_result(mid, extraction, 85, "Good fit", 1, 1, 1)
    repo.mark_processing_ready(mid, "inbox")
    inbox = repo.get_inbox()
    assert len(inbox) == 1
    assert inbox[0].relevance_score == 85


def test_approve_triggers_export_pending(repo: MessageRepository):
    posted = datetime(2026, 1, 1, tzinfo=timezone.utc)
    mid = repo.insert_message("ch1", 103, posted, "text")
    repo.conn.execute("UPDATE messages SET review_state = 'inbox' WHERE id = ?", (mid,))
    repo.conn.commit()
    msg = repo.approve(mid)
    assert msg.review_state == "approved"
    assert msg.export_state == "pending"


def test_list_pending_for_recovery(repo: MessageRepository):
    posted = datetime(2026, 1, 1, tzinfo=timezone.utc)
    mid = repo.insert_message("ch1", 104, posted, "text")
    pending = repo.list_pending_for_recovery()
    assert mid in pending


def test_settings_version_increment(repo: MessageRepository):
    s1 = repo.put_setting("profile", {"roles": ["SDE"]})
    s2 = repo.put_setting("profile", {"roles": ["SDE", "Backend"]})
    assert s2.version == s1.version + 1


def test_insert_links(repo: MessageRepository):
    posted = datetime(2026, 1, 1, tzinfo=timezone.utc)
    mid = repo.insert_message("ch1", 105, posted, "apply https://example.com/jobs")
    repo.insert_links(mid, [("https://example.com/jobs", "example.com", 0)])
    msg = repo.get_by_id(mid)
    assert len(msg.links) == 1
    assert msg.links[0].domain == "example.com"
