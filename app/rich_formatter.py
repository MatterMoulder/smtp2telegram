from __future__ import annotations

import html

from app.mail_parser import MailAttachment, ParsedMail
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


def format_attachments(attachments: list[MailAttachment]) -> str:
    if not attachments:
        return "<p><i>No attachments</i></p>"

    items = "\n".join(format_attachment_item(item) for item in attachments)
    return f"<ul>\n{items}\n</ul>"


def build_rich_html(mail: ParsedMail) -> str:
    body = mail.body[:MAX_BODY_CHARS]
    preview = body[:PREVIEW_CHARS] if body else "(empty body)"

    otp = extract_otp(f"{mail.subject}\n{body}")

    rows = "\n".join(
        row
        for row in [
            metadata_row("Subject", mail.subject, code=False, bold=True),
            metadata_row("From", mail.header_from),
            metadata_row("To", mail.header_to),
            metadata_row("Date", mail.date)
        ]
        if row
    )

    otp_block = ""
    title = "📩 Mail from service"

    if otp:
        title = "🔐 Verification code"
        otp_block = f"""
<blockquote>
  <h1>{h(otp)}</h1>
</blockquote>

<hr/>
""".strip()

    attachments_html = format_attachments(mail.attachments)

    return f"""
<h2>{h(title)}</h2>

{otp_block}

<table bordered striped>
{rows}
</table>

<hr/>

<h3>Preview</h3>
<blockquote>
  <p>{h(preview)}</p>
</blockquote>

<details>
  <summary>Full body</summary>
  <pre>{h(body)}</pre>
</details>

<details>
  <summary>Attachments</summary>
  {attachments_html}
</details>
""".strip()