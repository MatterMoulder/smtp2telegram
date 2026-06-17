from __future__ import annotations

import html
import re
from dataclasses import dataclass
from urllib.parse import urlparse


@dataclass(frozen=True)
class ExtractedLink:
    url: str
    label: str


URL_RE = re.compile(
    r"https?://[^\s<>'\"]+",
    re.IGNORECASE,
)

HREF_RE = re.compile(
    r"""href=["'](https?://[^"']+)["']""",
    re.IGNORECASE,
)


def _clean_url(url: str) -> str:
    url = html.unescape(url.strip())
    return url.rstrip(".,);]}>")


def _make_label(url: str) -> str:
    parsed = urlparse(url)
    label = parsed.netloc or url

    path = parsed.path.strip("/")
    if path:
        short_path = path[:45] + "…" if len(path) > 45 else path
        label = f"{label}/{short_path}"

    return label


def extract_links(text: str, limit: int = 10) -> list[ExtractedLink]:
    candidates: list[str] = []

    for match in HREF_RE.finditer(text or ""):
        candidates.append(match.group(1))

    for match in URL_RE.finditer(text or ""):
        candidates.append(match.group(0))

    seen: set[str] = set()
    links: list[ExtractedLink] = []

    for raw_url in candidates:
        url = _clean_url(raw_url)

        if not url or url in seen:
            continue

        seen.add(url)
        links.append(ExtractedLink(url=url, label=_make_label(url)))

        if len(links) >= limit:
            break

    return links