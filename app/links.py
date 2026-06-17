import re
from dataclasses import dataclass
from urllib.parse import urlparse


@dataclass(frozen=True)
class ExtractedLink:
    url: str
    label: str


URL_RE = re.compile(
    r"https?://[^\s<>\"]+",
    re.IGNORECASE,
)


def extract_links(text: str, limit: int = 10) -> list[ExtractedLink]:
    seen: set[str] = set()
    links: list[ExtractedLink] = []

    for match in URL_RE.finditer(text or ""):
        url = match.group(0).rstrip(".,);]}>")

        if url in seen:
            continue

        seen.add(url)

        parsed = urlparse(url)
        label = parsed.netloc or url

        path = parsed.path.strip("/")
        if path:
            short_path = path[:40] + "…" if len(path) > 40 else path
            label = f"{label}/{short_path}"

        links.append(ExtractedLink(url=url, label=label))

        if len(links) >= limit:
            break

    return links