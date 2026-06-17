from __future__ import annotations

import html

from app.mail_parser import MailAttachment, ParsedMail
from app.links import extract_links
from app.otp import extract_otp


MAX_BODY_CHARS = 24_000
PREVIEW_CHARS = 900


def h(value: str | None) -> str:
    return html.escape(value or "", quote=True)


def format_bytes(size: int) -> str:
    units = ["B", "KB", "MB", "GB"]
    value = float(size)

    for unit in units:
        if value < 1024 or unit == units[-1]:
            if unit == "B":
                return f"{int(value)} {unit}"
            return f"{value:.1f} {unit}"
        value /= 1024

    return f"{size} B"


def metadata_row(label: str, value: str, *, code: bool = True, bold: bool = False) -> str:
    if not value:
        return ""

    if code:
        rendered = f"<code>{h(value)}</code>"
    elif bold:
        rendered = f"<b>{h(value)}</b>"
    else:
        rendered = h(value)

    return f"<tr><td><b>{h(label)}</b></td><td>{rendered}</td></tr>"


def format_attachment_item(attachment: MailAttachment) -> str:
    return (
        "<li>"
        f"<code>{h(attachment.filename)}</code>"
        " — "
        f"<code>{h(attachment.content_type)}</code>"
        ", "
        f"<code>{h(format_bytes(attachment.size_bytes))}</code>"
        "</li>"
    )

def format_links_block(text: str) -> str:
    links = extract_links(text)

    if not links:
        return ""

    lines = [
        "",
        "🔗 <b>Links</b>",
    ]

    for index, link in enumerate(links, start=1):
        url = html.escape(link.url, quote=True)
        label = html.escape(link.label)

        lines.append(f'{index}. <a href="{url}">{label}</a>')

    return "\n".join(lines)

def detect_mail_kind(subject: str | None, body: str | None) -> tuple[str, str]:
    text = f"{subject or ''}\n{body or ''}".lower()

    if any(
            marker in text
            for marker in [
                "verify your email",
                "verify email",
                "email verification",
                "confirm your email",
                "confirm email",
                "подтвердите email",
                "подтвердите почту",
                "подтверждение почты",
            ]
    ):
        return "✅ Verify email", "verify"

    if any(
            marker in text
            for marker in [
                "verification code",
                "security code",
                "one-time code",
                "one time code",
                "one-time password",
                "otp",
                "2fa",
                "two-factor",
                "two factor",
                "код подтверждения",
                "одноразовый код",
            ]
    ):
        return "🔐 Verification code", "otp"

    if any(
            marker in text
            for marker in [
                "reset your password",
                "password reset",
                "change your password",
                "recover your password",
                "сброс пароля",
                "восстановление пароля",
                "изменение пароля",
            ]
    ):
        return "🔑 Password reset", "password_reset"

    if any(
            marker in text
            for marker in [
                "alert",
                "critical",
                "down",
                "firing",
                "recovered",
                "тревога",
                "недоступен",
                "восстановлен",
            ]
    ):
        return "🚨 Alert", "alert"

    return "📩 Mail from service", "generic"

def find_primary_link(text: str, kind: str) -> tuple[str, str] | None:
    links = extract_links(text)

    if not links:
        return None

    keywords_by_kind = {
        "verify": ["verify", "verification", "confirm", "activate"],
        "password_reset": ["reset", "password", "recover"],
        "otp": ["verify", "verification", "login", "signin", "sign-in"],
        "alert": ["alert", "incident", "monitor"],
    }

    keywords = keywords_by_kind.get(kind, [])

    def score(link) -> int:
        url = link.url.lower()
        label = link.label.lower()
        haystack = f"{url} {label}"

        return sum(1 for keyword in keywords if keyword in haystack)

    best = max(links, key=score)

    if score(best) == 0 and kind in {"verify", "password_reset"}:
        return links[0].url, links[0].label

    return best.url, best.label


def format_attachments(attachments: list[MailAttachment]) -> str:
    if not attachments:
        return "<p><i>No attachments</i></p>"

    items = "\n".join(format_attachment_item(item) for item in attachments)
    return f"<ul>\n{items}\n</ul>"

def format_action_block(title: str, kind: str, otp: str | None, body: str) -> str:
    primary_link = find_primary_link(body, kind)

    lines = [
        f"<h2>{h(title)}</h2>",
    ]

    if otp:
        lines.extend(
            [
                "<blockquote>",
                f"  <h1>{h(otp)}</h1>",
                "</blockquote>",
            ]
        )

    if primary_link and kind in {"verify", "password_reset", "otp"}:
        url, label = primary_link
        lines.append(f'👉 <a href="{h(url)}">{h(label)}</a>')

    return "\n".join(lines)

def format_links_details(text: str) -> str:
    links = extract_links(text)

    if not links:
        return ""

    items = []

    for index, link in enumerate(links, start=1):
        url = html.escape(link.url, quote=True)
        label = html.escape(link.label)
        items.append(f'<li>{index}. <a href="{url}">{label}</a></li>')

    return f"""
<details>
  <summary>Links ({len(links)})</summary>
  <ul>
    {''.join(items)}
  </ul>
</details>
""".strip()

def build_rich_html(mail: ParsedMail) -> str:
    body = mail.body[:MAX_BODY_CHARS]
    preview = body[:PREVIEW_CHARS] if body else "(empty body)"

    otp = extract_otp(f"{mail.subject}\n{body}")
    title, kind = detect_mail_kind(mail.subject, body)

    if otp and kind == "generic":
        title = "🔐 Verification code"
        kind = "otp"

    rows = "\n".join(
        row
        for row in [
            metadata_row("Subject", mail.subject, code=False, bold=True),
            metadata_row("From", mail.header_from),
            metadata_row("To", mail.header_to),
            metadata_row("Date", mail.date),
        ]
        if row
    )

    links_html = format_links_details(body)
    action_block = format_action_block(title, kind, otp, body)
    attachments_html = format_attachments(mail.attachments)

    return f"""
{action_block}

<hr/>

<table bordered striped>
{rows}
</table>

<hr/>

<h3>Preview</h3>
<blockquote>
  <p>{h(preview)}</p>
</blockquote>

{links_html}

<details>
  <summary>Full body</summary>
  <pre>{h(body)}</pre>
</details>

<details>
  <summary>Attachments</summary>
  {attachments_html}
</details>
""".strip()