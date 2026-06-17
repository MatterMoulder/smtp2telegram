from __future__ import annotations

import email
import html
import re
from bs4 import BeautifulSoup
from dataclasses import dataclass, field
from email.header import decode_header, make_header
from email.message import EmailMessage, Message
from email.policy import default
from email.utils import getaddresses, parsedate_to_datetime


@dataclass(frozen=True)
class MailAttachment:
    filename: str
    content_type: str
    size_bytes: int


@dataclass(frozen=True)
class ParsedMail:
    envelope_from: str
    envelope_to: list[str]
    peer: str

    header_from: str
    header_to: str
    cc: str
    subject: str
    date: str
    message_id: str

    body: str
    body_source: str

    attachments: list[MailAttachment] = field(default_factory=list)


def decode_header_value(value: str | None) -> str:
    if not value:
        return ""

    try:
        return str(make_header(decode_header(value)))
    except Exception:
        return value


def normalize_addresses(value: str | None) -> str:
    if not value:
        return ""

    decoded = decode_header_value(value)
    addresses = getaddresses([decoded])

    if not addresses:
        return decoded

    result = []

    for name, addr in addresses:
        if name and addr:
            result.append(f"{name} <{addr}>")
        elif addr:
            result.append(addr)
        elif name:
            result.append(name)

    return ", ".join(result)


def format_email_date(value: str | None) -> str:
    if not value:
        return ""

    try:
        return parsedate_to_datetime(value).strftime("%Y-%m-%d %H:%M:%S %z")
    except Exception:
        return value


def simple_html_to_text(value: str) -> str:
    """
    Safe-ish HTML-to-text fallback for emails.

    This intentionally does not preserve email HTML markup.
    Email HTML is usually not compatible with Telegram Rich HTML.
    """

    value = re.sub(r"(?is)<style.*?>.*?</style>", "", value)
    value = re.sub(r"(?is)<script.*?>.*?</script>", "", value)

    value = re.sub(r"(?i)<br\s*/?>", "\n", value)
    value = re.sub(r"(?i)</p\s*>", "\n\n", value)
    value = re.sub(r"(?i)</div\s*>", "\n", value)
    value = re.sub(r"(?i)</li\s*>", "\n", value)
    value = re.sub(r"(?i)<li[^>]*>", "- ", value)

    value = re.sub(r"(?is)<[^>]+>", "", value)
    value = html.unescape(value)

    value = re.sub(r"\n{4,}", "\n\n\n", value)
    return value.strip()


def _decode_payload(part: Message) -> str:
    payload = part.get_payload(decode=True)

    if payload is None:
        raw_payload = part.get_payload()
        return raw_payload if isinstance(raw_payload, str) else ""

    charset = part.get_content_charset() or "utf-8"
    return payload.decode(charset, errors="replace")


def extract_body(msg: Message) -> tuple[str, str]:
    """
    Prefer text/plain.
    If text/html exists, preserve links from HTML and append them to plain text.
    """

    if msg.is_multipart():
        text_body: str | None = None
        html_body: str | None = None

        for part in msg.walk():
            content_type = part.get_content_type()
            disposition = str(part.get("Content-Disposition", "")).lower()

            if "attachment" in disposition:
                continue

            if content_type == "text/plain":
                text = _decode_payload(part).strip()
                if text and text_body is None:
                    text_body = text

            elif content_type == "text/html":
                text = _decode_payload(part)
                if text and html_body is None:
                    html_body = text

        if text_body:
            if html_body:
                html_text = html_to_text_with_links(html_body)

                if "Links:" in html_text and "Links:" not in text_body:
                    links_part = html_text.split("Links:", 1)[1].strip()
                    if links_part:
                        text_body += "\n\nLinks:\n" + links_part

            return text_body, "text/plain"

        if html_body:
            return html_to_text_with_links(html_body), "text/html"

        return "", "empty"

    content_type = msg.get_content_type()

    if content_type == "text/html":
        return html_to_text_with_links(_decode_payload(msg)), "text/html"

    return _decode_payload(msg).strip(), content_type or "unknown"


def extract_attachments(msg: Message) -> list[MailAttachment]:
    if not msg.is_multipart():
        return []

    attachments: list[MailAttachment] = []

    for part in msg.walk():
        disposition = str(part.get("Content-Disposition", "")).lower()
        filename = part.get_filename()

        if "attachment" not in disposition and not filename:
            continue

        decoded_filename = decode_header_value(filename) or "(unnamed)"
        content_type = part.get_content_type()
        size_bytes = len(part.get_payload(decode=True) or b"")

        attachments.append(
            MailAttachment(
                filename=decoded_filename,
                content_type=content_type,
                size_bytes=size_bytes,
            )
        )

    return attachments


def parse_mail(
        raw: bytes,
        *,
        envelope_from: str = "",
        envelope_to: list[str] | None = None,
        peer: str = "",
) -> ParsedMail:
    msg: EmailMessage = email.message_from_bytes(raw, policy=default)

    body, body_source = extract_body(msg)

    return ParsedMail(
        envelope_from=envelope_from,
        envelope_to=envelope_to or [],
        peer=peer,
        header_from=normalize_addresses(msg.get("From")) or envelope_from or "unknown",
        header_to=normalize_addresses(msg.get("To")) or ", ".join(envelope_to or []),
        cc=normalize_addresses(msg.get("Cc")),
        subject=decode_header_value(msg.get("Subject")) or "(no subject)",
        date=format_email_date(msg.get("Date")),
        message_id=msg.get("Message-ID") or "",
        body=body,
        body_source=body_source,
        attachments=extract_attachments(msg),
    )

def html_to_text_with_links(html_body: str) -> str:
    soup = BeautifulSoup(html_body or "", "html.parser")

    links: list[str] = []
    seen: set[str] = set()

    for a in soup.find_all("a", href=True):
        href = str(a["href"]).strip()
        label = a.get_text(" ", strip=True)

        if not href.startswith(("http://", "https://")):
            continue

        if href in seen:
            continue

        seen.add(href)

        if label:
            links.append(f"{label}: {href}")
        else:
            links.append(href)

    text = soup.get_text("\n", strip=True)

    if links:
        text += "\n\nLinks:\n" + "\n".join(links)

    return text