import re
from dataclasses import dataclass

from app.models.extraction import Extraction, ExtractedField

PARSER_VERSION = 2

WATERMARK_PATTERNS = [
    re.compile(r"Original source:\s*SDE Jobs\s*&\s*Internships\s*\(Premium\)\s*", re.IGNORECASE),
    re.compile(r"Original source:\s*SDE Jobs\s+and\s+Internships\s*", re.IGNORECASE),
]

LABEL_ALIASES: dict[str, list[str]] = {
    "company": ["Company", "Organization", "Employer"],
    "role": ["Role", "Position", "Title"],
    "batch": ["Batch", "Eligibility", "Graduation"],
    "stipend": ["Stipend", "Salary", "CTC", "Package"],
    "location": ["Location", "Work Location", "Place"],
}

FIELD_LINE = re.compile(
    r"^(?:\d+\)\s*)?(?P<label>[A-Za-z][A-Za-z /]+?)\s*[-:]\s*(?P<value>.+?)\s*$"
)

JOB_SPLIT = re.compile(r"(?=^\d+\)\s*Company\s*[-:])", re.MULTILINE | re.IGNORECASE)


@dataclass
class ParsedJob:
    extraction: Extraction
    parser_matched: bool
    job_description: str = ""


def _strip_watermarks(text: str) -> str:
    for pattern in WATERMARK_PATTERNS:
        text = pattern.sub("", text)
    return text


def _normalize_label(label: str) -> str | None:
    cleaned = label.strip()
    for field, aliases in LABEL_ALIASES.items():
        for alias in aliases:
            if cleaned.lower() == alias.lower():
                return field
    return None


def _field(value: str) -> ExtractedField:
    return ExtractedField(value=value.strip(), source="parser")


def _extract_tags(extraction: Extraction, text: str) -> list[str]:
    role_val = extraction.role.value or ""
    tags: list[str] = []
    lower = text.lower()
    if "(+ppo)" in role_val.lower() or re.search(r"\bppo\b", lower):
        tags.append("ppo")
    if extraction.location.value and "remote" in extraction.location.value.lower():
        tags.append("remote")
    return tags


def _extract_job_description(chunk: str, header_end_idx: int) -> str:
    """Text between header fields and How to Apply."""
    body = chunk[header_end_idx:].strip()
    m = re.search(r"^How to Apply\s*:", body, re.IGNORECASE | re.MULTILINE)
    if m:
        body = body[: m.start()].strip()
    lines = []
    for line in body.splitlines():
        line = line.strip()
        if not line or re.match(r"^Original source:", line, re.I):
            continue
        lines.append(line)
    return "\n".join(lines).strip()


def _parse_chunk(chunk: str) -> ParsedJob:
    chunk = chunk.strip()
    extraction = Extraction()
    matched_fields = 0
    last_header_line = 0

    for i, line in enumerate(chunk.splitlines()):
        line = line.strip()
        if not line or line.startswith("•") or line.startswith("●"):
            continue
        m = FIELD_LINE.match(line)
        if not m:
            continue
        field_name = _normalize_label(m.group("label"))
        if not field_name:
            continue
        value = m.group("value").strip()
        if not value:
            continue
        setattr(extraction, field_name, _field(value))
        matched_fields += 1
        last_header_line = i

    extraction.tags = _extract_tags(extraction, chunk)
    parser_matched = matched_fields >= 2 and bool(extraction.company.value or extraction.role.value)

    header_lines = chunk.splitlines()
    header_end = sum(len(l) + 1 for l in header_lines[: last_header_line + 1]) if last_header_line else 0
    job_description = _extract_job_description(chunk, header_end)

    return ParsedJob(extraction=extraction, parser_matched=parser_matched, job_description=job_description)


def _split_chunks(raw_text: str) -> list[str]:
    cleaned = _strip_watermarks(raw_text)
    matches = list(JOB_SPLIT.finditer(cleaned))
    if matches:
        chunks: list[str] = []
        for i, m in enumerate(matches):
            start = m.start()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(cleaned)
            chunks.append(cleaned[start:end].strip())
        return [c for c in chunks if c]
    return [cleaned.strip()] if cleaned.strip() else [raw_text]


def parse_message_multi(raw_text: str) -> list[ParsedJob]:
    chunks = _split_chunks(raw_text)
    jobs = [_parse_chunk(c) for c in chunks]
    return jobs if jobs else [ParsedJob(extraction=Extraction(), parser_matched=False)]


def parse_message(raw_text: str) -> tuple[Extraction, bool]:
    job = parse_message_multi(raw_text)[0]
    return job.extraction, job.parser_matched


def parse_message_with_description(raw_text: str) -> ParsedJob:
    return parse_message_multi(raw_text)[0]
