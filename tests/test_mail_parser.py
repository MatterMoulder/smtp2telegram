import unittest

from textwrap import dedent
from app.mail_parser import (
    parse_mail,
    decode_header_value,
    normalize_addresses,
    format_email_date,
    simple_html_to_text,
)


class DecodeHeaderValueTestCase(unittest.TestCase):
    def test_decode_plain_string(self):
        result = decode_header_value("Hello World")
        self.assertEqual(result, "Hello World")

    def test_decode_utf8_encoded_header(self):
        result = decode_header_value("=?utf-8?b?0J/RgNC40LLQtdGC?=")
        self.assertEqual(result, "Привет")

    def test_decode_none(self):
        result = decode_header_value(None)
        self.assertEqual(result, "")

    def test_decode_empty_string(self):
        result = decode_header_value("")
        self.assertEqual(result, "")


class NormalizeAddressesTestCase(unittest.TestCase):
    def test_normalize_single_address(self):
        result = normalize_addresses("user@example.com")
        self.assertEqual(result, "user@example.com")

    def test_normalize_address_with_name(self):
        result = normalize_addresses("John Doe <john@example.com>")
        self.assertEqual(result, "John Doe <john@example.com>")

    def test_normalize_multiple_addresses(self):
        result = normalize_addresses("John <john@example.com>, Jane <jane@example.com>")
        self.assertIn("John <john@example.com>", result)
        self.assertIn("Jane <jane@example.com>", result)

    def test_normalize_none(self):
        result = normalize_addresses(None)
        self.assertEqual(result, "")

    def test_normalize_empty_string(self):
        result = normalize_addresses("")
        self.assertEqual(result, "")

    def test_normalize_encoded_address(self):
        result = normalize_addresses("=?utf-8?b?0J/RgNC40LLQtdGC?= <user@example.com>")
        self.assertIn("user@example.com", result)


class FormatEmailDateTestCase(unittest.TestCase):
    def test_format_rfc2822_date(self):
        result = format_email_date("Wed, 17 Jun 2026 12:00:00 +0300")
        self.assertIn("2026-06-17", result)
        self.assertIn("12:00:00", result)

    def test_format_none(self):
        result = format_email_date(None)
        self.assertEqual(result, "")

    def test_format_empty_string(self):
        result = format_email_date("")
        self.assertEqual(result, "")

    def test_format_invalid_date(self):
        result = format_email_date("invalid date string")
        self.assertEqual(result, "invalid date string")


class SimpleHtmlToTextTestCase(unittest.TestCase):
    def test_removes_html_tags(self):
        html = "<p>Hello <b>world</b></p>"
        result = simple_html_to_text(html)
        self.assertEqual(result, "Hello world")

    def test_converts_br_to_newline(self):
        html = "Line 1<br>Line 2"
        result = simple_html_to_text(html)
        self.assertIn("Line 1", result)
        self.assertIn("Line 2", result)

    def test_removes_style_tags(self):
        html = "<style>body{color:red}</style>Hello"
        result = simple_html_to_text(html)
        self.assertEqual(result, "Hello")
        self.assertNotIn("color:red", result)

    def test_removes_script_tags(self):
        html = "<script>alert(1)</script>Hello"
        result = simple_html_to_text(html)
        self.assertEqual(result, "Hello")
        self.assertNotIn("alert", result)

    def test_converts_p_tags_to_newlines(self):
        html = "<p>First</p><p>Second</p>"
        result = simple_html_to_text(html)
        self.assertIn("First", result)
        self.assertIn("Second", result)

    def test_converts_li_tags_to_bullets(self):
        html = "<ul><li>Item 1</li><li>Item 2</li></ul>"
        result = simple_html_to_text(html)
        self.assertIn("- Item 1", result)
        self.assertIn("- Item 2", result)

    def test_unescapes_html_entities(self):
        html = "Hello &amp; goodbye &lt;world&gt;"
        result = simple_html_to_text(html)
        self.assertIn("&", result)
        self.assertIn("<", result)
        self.assertIn(">", result)

    def test_strips_whitespace(self):
        html = "  \n  Hello  \n  "
        result = simple_html_to_text(html)
        self.assertEqual(result, "Hello")


class MailParserTestCase(unittest.TestCase):
    def test_parse_plain_text_email(self):
        raw = dedent("""\
            From: NAS <nas@local>
            To: telegram@local
            Subject: Disk warning
            Date: Wed, 17 Jun 2026 12:00:00 +0300
            Message-ID: <test-123@local>
        
            Disk usage is 91%.
        """).encode("utf-8")

        mail = parse_mail(
            raw,
            envelope_from="nas@local",
            envelope_to=["telegram@local"],
            peer="192.168.1.50",
        )

        self.assertEqual(mail.envelope_from, "nas@local")
        self.assertEqual(mail.envelope_to, ["telegram@local"])
        self.assertEqual(mail.peer, "192.168.1.50")
        self.assertEqual(mail.header_from, "NAS <nas@local>")
        self.assertEqual(mail.header_to, "telegram@local")
        self.assertEqual(mail.subject, "Disk warning")
        self.assertEqual(mail.body, "Disk usage is 91%.")
        self.assertEqual(mail.body_source, "text/plain")
        self.assertEqual(mail.message_id, "<test-123@local>")

    def test_parse_html_email_fallback_to_text(self):
        raw = dedent("""\
            From: router@local
            To: telegram@local
            Subject: HTML alert
            Content-Type: text/html; charset=utf-8
        
            <html>
              <body>
                <p>Hello <b>router</b></p>
                <p>Status: OK</p>
              </body>
            </html>
        """).encode("utf-8")

        mail = parse_mail(raw)

        self.assertEqual(mail.subject, "HTML alert")
        self.assertEqual(mail.body_source, "text/html")
        self.assertIn("Hello router", mail.body)
        self.assertIn("Status: OK", mail.body)

    def test_decode_encoded_subject(self):
        raw = (
            "From: nas@local\n"
            "To: telegram@local\n"
            "Subject: =?utf-8?b?0J/RgNC40LLQtdGC?=\n"
            "\n"
            "Body"
        ).encode("utf-8")

        mail = parse_mail(raw)

        self.assertEqual(mail.subject, "Привет")

    def test_parse_with_no_subject(self):
        raw = dedent("""\
            From: sender@local
            To: recipient@local
        
            Email without subject
        """).encode("utf-8")

        mail = parse_mail(raw)

        self.assertEqual(mail.subject, "(no subject)")

    def test_parse_with_cc(self):
        raw = dedent("""\
            From: sender@local
            To: recipient@local
            Cc: cc@local
            Subject: Test
        
            Test email
        """).encode("utf-8")

        mail = parse_mail(raw)

        self.assertEqual(mail.cc, "cc@local")

    def test_parse_with_multiple_cc(self):
        raw = dedent("""\
            From: sender@local
            To: recipient@local
            Cc: cc1@local, cc2@local
            Subject: Test
        
            Test email
        """).encode("utf-8")

        mail = parse_mail(raw)

        self.assertIn("cc1@local", mail.cc)
        self.assertIn("cc2@local", mail.cc)

    def test_parse_with_attachments(self):
        raw = dedent("""\
            From: sender@local
            To: recipient@local
            Subject: With attachment
            MIME-Version: 1.0
            Content-Type: multipart/mixed; boundary="boundary123"
        
            --boundary123
            Content-Type: text/plain
        
            Email body
            --boundary123
            Content-Type: text/plain; name="file.txt"
            Content-Disposition: attachment; filename="file.txt"
            Content-Transfer-Encoding: base64
        
            VGhpcyBpcyB0aGUgYXR0YWNoZWQgZmlsZQ==
            --boundary123--
        """).encode("utf-8")

        mail = parse_mail(raw)

        self.assertTrue(len(mail.attachments) > 0)

    def test_parse_defaults_envelope_to_empty_list(self):
        raw = b"From: sender@local\nSubject: Test\n\nBody"
        mail = parse_mail(raw)
        self.assertEqual(mail.envelope_to, [])

    def test_parse_defaults_envelope_from_to_empty(self):
        raw = b"From: sender@local\nSubject: Test\n\nBody"
        mail = parse_mail(raw)
        self.assertEqual(mail.envelope_from, "")

    def test_parse_defaults_peer_to_empty(self):
        raw = b"From: sender@local\nSubject: Test\n\nBody"
        mail = parse_mail(raw)
        self.assertEqual(mail.peer, "")

    def test_parse_uses_envelope_when_header_missing(self):
        raw = b"Subject: Test\n\nBody"
        mail = parse_mail(raw, envelope_from="sender@example.com")
        self.assertEqual(mail.header_from, "sender@example.com")

    def test_parse_multipart_without_text_plain(self):
        raw = dedent("""\
            From: sender@local
            To: recipient@local
            Subject: HTML only
            MIME-Version: 1.0
            Content-Type: multipart/alternative; boundary="boundary123"
        
            --boundary123
            Content-Type: text/html
        
            <html><body>Hello</body></html>
            --boundary123--
        """).encode("utf-8")

        mail = parse_mail(raw)

        self.assertEqual(mail.body_source, "text/html")
        self.assertIn("Hello", mail.body)

    def test_parse_message_id(self):
        raw = dedent("""\
            From: sender@local
            To: recipient@local
            Subject: Test
            Message-ID: <unique-id-123@local>
        
            Body
        """).encode("utf-8")

        mail = parse_mail(raw)

        self.assertEqual(mail.message_id, "<unique-id-123@local>")

    def test_parse_no_message_id(self):
        raw = dedent("""\
            From: sender@local
            To: recipient@local
            Subject: Test
        
            Body
        """).encode("utf-8")

        mail = parse_mail(raw)

        self.assertEqual(mail.message_id, "")


if __name__ == "__main__":
    unittest.main()