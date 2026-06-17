import unittest

from app.otp import extract_otp


class ExtractOtpTestCase(unittest.TestCase):
    def test_extracts_otp_with_code_keyword(self):
        text = "Your verification code is 123456"
        result = extract_otp(text)
        self.assertEqual(result, "123456")

    def test_extracts_otp_with_code_keyword_russian(self):
        text = "Your verification код is 123456"
        result = extract_otp(text)
        self.assertEqual(result, "123456")

    def test_extracts_otp_with_otp_keyword(self):
        text = "OTP: 987654"
        result = extract_otp(text)
        self.assertEqual(result, "987654")

    def test_extracts_otp_with_verification_code_keyword(self):
        text = "Verification code: 555555"
        result = extract_otp(text)
        self.assertEqual(result, "555555")

    def test_extracts_otp_with_security_code_keyword(self):
        text = "Your security code is 444444"
        result = extract_otp(text)
        self.assertEqual(result, "444444")

    def test_extracts_6_digit_otp_without_keyword(self):
        text = "Here is your code: 123456 do not share"
        result = extract_otp(text)
        self.assertEqual(result, "123456")

    def test_extracts_4_digit_otp_without_keyword(self):
        text = "PIN: 1234"
        result = extract_otp(text)
        self.assertEqual(result, "1234")

    def test_returns_none_when_no_otp_found(self):
        text = "This is just regular text without any codes"
        result = extract_otp(text)
        self.assertIsNone(result)

    def test_returns_first_matching_otp(self):
        text = "Code: 111111 and another: 222222"
        result = extract_otp(text)
        self.assertEqual(result, "111111")

    def test_extracts_otp_from_multiline_text(self):
        text = "Hello\nYour code is 777777\nDo not share"
        result = extract_otp(text)
        self.assertEqual(result, "777777")

    def test_case_insensitive_keyword_matching(self):
        text = "YOUR CODE IS 123456"
        result = extract_otp(text)
        self.assertEqual(result, "123456")

    def test_handles_otp_at_word_boundary(self):
        text = "code123456code"
        result = extract_otp(text)
        self.assertIsNone(result)  # Should not match because it's not at word boundary

    def test_allows_separators_between_keyword_and_code(self):
        text = "code - - - 123456"
        result = extract_otp(text)
        self.assertEqual(result, "123456")

    def test_extracts_4_digit_code_with_keyword(self):
        text = "verification code 5555"
        result = extract_otp(text)
        self.assertEqual(result, "5555")

    def test_extracts_10_digit_code(self):
        text = "code: 1234567890"
        result = extract_otp(text)
        self.assertEqual(result, "1234567890")

    def test_does_not_extract_3_digit_code(self):
        text = "number: 123"
        result = extract_otp(text)
        self.assertIsNone(result)

    def test_does_not_extract_11_digit_code(self):
        text = "number: 12345678901"
        result = extract_otp(text)
        self.assertIsNone(result)

    def test_empty_text(self):
        result = extract_otp("")
        self.assertIsNone(result)

    def test_whitespace_only(self):
        result = extract_otp("   \n\t   ")
        self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()

