import re
from urllib.parse import urlparse

URL_PATTERN = re.compile(
    r"https?://[^\s<>\"']+|"
    r"mailto:[^\s<>\"']+",
    re.IGNORECASE,
)


def normalize_url(url: str) -> str:
    return url.rstrip(".,);]")


def extract_domain(url: str) -> str:
    if url.lower().startswith("mailto:"):
        return url.split(":", 1)[1].split("@")[-1]
    parsed = urlparse(url)
    host = parsed.netloc or parsed.path.split("/")[0]
    return host.removeprefix("www.")


def extract_links_from_text(text: str) -> list[tuple[str, str, int]]:
    seen: set[str] = set()
    links: list[tuple[str, str, int]] = []
    for match in URL_PATTERN.finditer(text):
        url = normalize_url(match.group(0))
        if url in seen:
            continue
        seen.add(url)
        links.append((url, extract_domain(url), len(links)))
    return links
