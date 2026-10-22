"""Offline checks for the version-controlled architecture documentation."""

import re
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[2]
DOCS = ROOT / "docs"


def test_documentation_local_links_resolve():
    documents = [ROOT / "README.md", *DOCS.rglob("*.md")]
    for document in documents:
        text = document.read_text(encoding="utf-8")
        assert text.startswith("# "), f"Missing title: {document}"
        assert not re.search(r"[ \t]+$", text, re.MULTILINE), document
        for target in re.findall(r"\[[^\]]+\]\(([^)]+)\)", text):
            url = urlsplit(target)
            if url.scheme or not url.path:
                continue
            destination = (document.parent / unquote(url.path)).resolve()
            assert destination.is_relative_to(ROOT), target
            assert destination.exists(), f"Broken link in {document}: {target}"


def test_decisions_have_reviewable_structure():
    decisions = sorted((DOCS / "decisions").glob("ADR-*.md"))
    assert len(decisions) >= 7
    for decision in decisions:
        text = decision.read_text(encoding="utf-8")
        for required in (
            "Status:", "Owner:", "Date:", "Reference:",
            "## Context", "## Decision", "## Consequences and alternatives",
            "## Verification", "## Supersession",
        ):
            assert required in text, f"{decision}: missing {required}"
