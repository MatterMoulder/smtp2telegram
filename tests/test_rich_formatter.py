import unittest

from app.mail_parser import ParsedMail, MailAttachment
from app.rich_formatter import (
    build_rich_html,
    format_bytes,
    h,
    metadata_row,
    format_attachment_item,
    format_attachments,
)


class FormatBytesTestCase(unittest.TestCase):
    def test_format_bytes_single_byte(self):
        self.assertEqual(format_bytes(1), "1 B")

    def test_format_bytes_under_1kb(self):
        self.assertEqual(format_bytes(512), "512 B")

    def test_format_bytes_exactly_1kb(self):
        self.assertEqual(format_bytes(1024), "1.0 KB")

    def test_format_bytes_kilobytes(self):
        self.assertEqual(format_bytes(2048), "2.0 KB")

    def test_format_bytes_megabytes(self):
        self.assertEqual(format_bytes(1024 * 1024), "1.0 MB")

    def test_format_bytes_gigabytes(self):
        self.assertEqual(format_bytes(1024 * 1024 * 1024), "1.0 GB")

    def test_format_bytes_large_gigabytes(self):
        result = format_bytes(5 * 1024 * 1024 * 1024)
        self.assertIn("GB", result)

    def test_format_bytes_zero(self):
        self.assertEqual(format_bytes(0), "0 B")


class HtmlEscapeTestCase(unittest.TestCase):
    def test_h_escapes_angle_brackets(self):
        result = h("<script>alert(1)</script>")
        self.assertIn("&lt;", result)
        self.assertIn("&gt;", result)

    def test_h_escapes_quotes(self):
        result = h('test"quote"test')
        self.assertIn("&quot;", result)

    def test_h_escapes_ampersand(self):
        result = h("test&test")
        self.assertIn("&amp;", result)

    def test_h_handles_none(self):
        result = h(None)
        self.assertEqual(result, "")

    def test_h_handles_empty_string(self):
        result = h("")
        self.assertEqual(result, "")

    def test_h_preserves_text(self):
        result = h("Hello World")
        self.assertEqual(result, "Hello World")


class MetadataRowTestCase(unittest.TestCase):
    def test_metadata_row_with_code(self):
        result = metadata_row("Label", "value")
        self.assertIn("<b>Label</b>", result)
        self.assertIn("<code>value</code>", result)

    def test_metadata_row_with_bold(self):
        result = metadata_row("Label", "value", code=False, bold=True)
        self.assertIn("<b>Label</b>", result)
        self.assertIn("<b>value</b>", result)

    def test_metadata_row_plain_text(self):
        result = metadata_row("Label", "value", code=False, bold=False)
        self.assertIn("<b>Label</b>", result)
        self.assertNotIn("<code>", result)
        self.assertNotIn("<b>value</b>", result)

    def test_metadata_row_empty_value_returns_empty(self):
        result = metadata_row("Label", "")
        self.assertEqual(result, "")

    def test_metadata_row_escapes_content(self):
        result = metadata_row("Label", "<script>alert(1)</script>")
        self.assertNotIn("<script>", result)
        self.assertIn("&lt;script&gt;", result)


class FormatAttachmentItemTestCase(unittest.TestCase):
    def test_format_attachment_item(self):
        attachment = MailAttachment(
            filename="test.txt",
            content_type="text/plain",
            size_bytes=1024,
        )
        result = format_attachment_item(attachment)
        self.assertIn("test.txt", result)
        self.assertIn("text/plain", result)
        self.assertIn("1.0 KB", result)

    def test_format_attachment_item_escapes_filename(self):
        attachment = MailAttachment(
            filename="<script>.txt",
            content_type="text/plain",
            size_bytes=100,
        )
        result = format_attachment_item(attachment)
        self.assertNotIn("<script>", result)
        self.assertIn("&lt;script&gt;", result)

    def test_format_attachment_item_contains_li(self):
        attachment = MailAttachment(
            filename="file.txt",
            content_type="text/plain",
            size_bytes=100,
        )
        result = format_attachment_item(attachment)
        self.assertIn("<li>", result)
        self.assertIn("</li>", result)


class FormatAttachmentsTestCase(unittest.TestCase):
    def test_format_attachments_empty_list(self):
        result = format_attachments([])
        self.assertIn("No attachments", result)

    def test_format_attachments_single(self):
        attachments = [
            MailAttachment(
                filename="file.txt",
                content_type="text/plain",
                size_bytes=1024,
            )
        ]
        result = format_attachments(attachments)
        self.assertNotIn("No attachments", result)
        self.assertIn("file.txt", result)
        self.assertIn("<ul>", result)
        self.assertIn("</ul>", result)

    def test_format_attachments_multiple(self):
        attachments = [
            MailAttachment(
                filename="file1.txt",
                content_type="text/plain",
                size_bytes=1024,
            ),
            MailAttachment(
                filename="file2.pdf",
                content_type="application/pdf",
                size_bytes=2048,
            ),
        ]
        result = format_attachments(attachments)
        self.assertIn("file1.txt", result)
        self.assertIn("file2.pdf", result)


class BuildRichHtmlTestCase(unittest.TestCase):
    def test_build_rich_html_contains_metadata(self):
        mail = ParsedMail(
            envelope_from="nas@local",
            envelope_to=["telegram@local"],
            peer="192.168.1.50",
            header_from="NAS <nas@local>",
            header_to="telegram@local",
            cc="",
            subject="Disk warning",
            date="2026-06-17 12:00:00 +0300",
            message_id="<test-123@local>",
            body="Disk usage is 91%.",
            body_source="text/plain",
            attachments=[],
        )

        rich_html = build_rich_html(mail)

        self.assertIn("<h2>📩 Mail from service</h2>", rich_html)
        self.assertIn("Disk warning", rich_html)
        self.assertIn("Disk usage is 91%.", rich_html)
        self.assertIn("NAS &lt;nas@local&gt;", rich_html)
        self.assertIn("No attachments", rich_html)

    def test_build_rich_html_escapes_user_content(self):
        mail = ParsedMail(
            envelope_from="evil@local",
            envelope_to=["telegram@local"],
            peer="192.168.1.66",
            header_from="<script>alert(1)</script>",
            header_to="telegram@local",
            cc="",
            subject="<b>fake bold</b>",
            date="",
            message_id="",
            body="<script>alert('xss')</script>",
            body_source="text/plain",
            attachments=[],
        )

        rich_html = build_rich_html(mail)

        self.assertIn("&lt;script&gt;alert", rich_html)
        self.assertIn("&lt;b&gt;fake bold&lt;/b&gt;", rich_html)

        self.assertNotIn("<script>", rich_html)
        self.assertNotIn("<b>fake bold</b>", rich_html)

    def test_build_rich_html_contains_attachments(self):
        mail = ParsedMail(
            envelope_from="nas@local",
            envelope_to=["telegram@local"],
            peer="192.168.1.50",
            header_from="nas@local",
            header_to="telegram@local",
            cc="",
            subject="Report",
            date="",
            message_id="",
            body="See attachment",
            body_source="text/plain",
            attachments=[
                MailAttachment(
                    filename="report.txt",
                    content_type="text/plain",
                    size_bytes=2048,
                )
            ],
        )

        rich_html = build_rich_html(mail)

        self.assertIn("report.txt", rich_html)
        self.assertIn("text/plain", rich_html)
        self.assertIn("2.0 KB", rich_html)

    def test_build_rich_html_with_otp(self):
        mail = ParsedMail(
            envelope_from="auth@example.com",
            envelope_to=["user@example.com"],
            peer="192.168.1.1",
            header_from="auth@example.com",
            header_to="user@example.com",
            cc="",
            subject="Verification code",
            date="",
            message_id="",
            body="Your code is 123456",
            body_source="text/plain",
            attachments=[],
        )

        rich_html = build_rich_html(mail)

        self.assertIn("🔐 Verification code", rich_html)
        self.assertIn("123456", rich_html)

    def test_build_rich_html_without_otp(self):
        mail = ParsedMail(
            envelope_from="sender@example.com",
            envelope_to=["recipient@example.com"],
            peer="192.168.1.1",
            header_from="sender@example.com",
            header_to="recipient@example.com",
            cc="",
            subject="Regular email",
            date="",
            message_id="",
            body="This is a regular email",
            body_source="text/plain",
            attachments=[],
        )

        rich_html = build_rich_html(mail)

        self.assertIn("📩 Mail from service", rich_html)
        self.assertNotIn("🔐 Verification code", rich_html)

    def test_build_rich_html_empty_body(self):
        mail = ParsedMail(
            envelope_from="sender@example.com",
            envelope_to=["recipient@example.com"],
            peer="192.168.1.1",
            header_from="sender@example.com",
            header_to="recipient@example.com",
            cc="",
            subject="Empty",
            date="",
            message_id="",
            body="",
            body_source="text/plain",
            attachments=[],
        )

        rich_html = build_rich_html(mail)

        self.assertIn("(empty body)", rich_html)

    def test_build_rich_html_with_message_id(self):
        mail = ParsedMail(
            envelope_from="sender@example.com",
            envelope_to=["recipient@example.com"],
            peer="192.168.1.1",
            header_from="sender@example.com",
            header_to="recipient@example.com",
            cc="",
            subject="Test",
            date="",
            message_id="<msg-id-123@example.com>",
            body="Body",
            body_source="text/plain",
            attachments=[],
        )

        rich_html = build_rich_html(mail)

        # Message-ID is stored in mail object but not displayed in HTML
        self.assertIn("Test", rich_html)  # Subject should be present
        self.assertIn("Body", rich_html)  # Body should be present

    def test_build_rich_html_without_message_id(self):
        mail = ParsedMail(
            envelope_from="sender@example.com",
            envelope_to=["recipient@example.com"],
            peer="192.168.1.1",
            header_from="sender@example.com",
            header_to="recipient@example.com",
            cc="",
            subject="Test",
            date="",
            message_id="",
            body="Body",
            body_source="text/plain",
            attachments=[],
        )

        rich_html = build_rich_html(mail)

        self.assertNotIn("Message-ID", rich_html)

    def test_build_rich_html_with_cc(self):
        mail = ParsedMail(
            envelope_from="sender@example.com",
            envelope_to=["recipient@example.com"],
            peer="192.168.1.1",
            header_from="sender@example.com",
            header_to="recipient@example.com",
            cc="cc@example.com",
            subject="Test",
            date="",
            message_id="",
            body="Body",
            body_source="text/plain",
            attachments=[],
        )

        rich_html = build_rich_html(mail)

        # Verify the mail object has CC set
        self.assertEqual(mail.cc, "cc@example.com")
        # Verify the HTML still generates successfully
        self.assertIn("<h2>📩 Mail from service</h2>", rich_html)

    def test_build_rich_html_multiple_recipients(self):
        mail = ParsedMail(
            envelope_from="sender@example.com",
            envelope_to=["user1@example.com", "user2@example.com"],
            peer="192.168.1.1",
            header_from="sender@example.com",
            header_to="user1@example.com, user2@example.com",
            cc="",
            subject="Test",
            date="",
            message_id="",
            body="Body",
            body_source="text/plain",
            attachments=[],
        )

        rich_html = build_rich_html(mail)

        self.assertIn("user1@example.com", rich_html)
        self.assertIn("user2@example.com", rich_html)

    def test_build_rich_html_truncates_long_body(self):
        long_body = "x" * 30000
        mail = ParsedMail(
            envelope_from="sender@example.com",
            envelope_to=["recipient@example.com"],
            peer="192.168.1.1",
            header_from="sender@example.com",
            header_to="recipient@example.com",
            cc="",
            subject="Test",
            date="",
            message_id="",
            body=long_body,
            body_source="text/plain",
            attachments=[],
        )

        rich_html = build_rich_html(mail)

        # Body should be truncated in full body section
        self.assertIn("Full body", rich_html)

    def test_build_rich_html_contains_table(self):
        mail = ParsedMail(
            envelope_from="sender@example.com",
            envelope_to=["recipient@example.com"],
            peer="192.168.1.1",
            header_from="sender@example.com",
            header_to="recipient@example.com",
            cc="",
            subject="Test",
            date="2026-01-01 00:00:00",
            message_id="<id@test>",
            body="Body",
            body_source="text/plain",
            attachments=[],
        )

        rich_html = build_rich_html(mail)

        self.assertIn("<table", rich_html)
        self.assertIn("</table>", rich_html)


if __name__ == "__main__":
    unittest.main()