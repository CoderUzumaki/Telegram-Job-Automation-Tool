import pytest

from app.pipeline.keyword_filter import passes_filter


def test_include_keyword_match():
    rules = {"include": ["intern", "sde"], "exclude": []}
    assert passes_filter("Software Engineer Intern at Google", rules) is True


def test_exclude_keyword_blocks():
    rules = {"include": ["intern"], "exclude": ["senior only"]}
    assert passes_filter("Senior only role for intern team", rules) is False


def test_no_include_means_pass():
    rules = {"include": [], "exclude": ["spam"]}
    assert passes_filter("Any job post", rules) is True


def test_case_insensitive():
    rules = {"include": ["FASTAPI"], "exclude": []}
    assert passes_filter("Backend fastapi intern", rules) is True
