import pytest

from app.ingest.link_extractor import extract_domain, extract_links_from_text, normalize_url


def test_extract_https_links():
    text = "Apply here: https://example.com/jobs/123 and https://forms.gle/abc"
    links = extract_links_from_text(text)
    assert len(links) == 2
    assert links[0][1] == "example.com"
    assert links[1][1] == "forms.gle"


def test_extract_mailto():
    text = "Email: mailto:contact@retracelabs.io"
    links = extract_links_from_text(text)
    assert len(links) == 1
    assert links[0][1] == "retracelabs.io"


def test_normalize_url_strips_trailing_punctuation():
    assert normalize_url("https://example.com/path.") == "https://example.com/path"


def test_extract_domain():
    assert extract_domain("https://www.google.com/forms") == "google.com"
