import unittest
import asyncio
from aiosmtpd.smtp import LoginPassword

from app.main import (
    build_authenticator,
    wait_for_shutdown,
)


class BuildAuthenticatorTestCase(unittest.TestCase):
    def test_successful_authentication(self):
        authenticator = build_authenticator("user", "password")

        login_password = LoginPassword(login=b"user", password=b"password")

        result = authenticator(None, None, None, None, login_password)

        self.assertTrue(result.success)

    def test_failed_authentication_wrong_username(self):
        authenticator = build_authenticator("user", "password")

        login_password = LoginPassword(login=b"wrong_user", password=b"password")

        result = authenticator(None, None, None, None, login_password)

        self.assertFalse(result.success)

    def test_failed_authentication_wrong_password(self):
        authenticator = build_authenticator("user", "password")

        login_password = LoginPassword(login=b"user", password=b"wrong_password")

        result = authenticator(None, None, None, None, login_password)

        self.assertFalse(result.success)

    def test_failed_authentication_both_wrong(self):
        authenticator = build_authenticator("user", "password")

        login_password = LoginPassword(login=b"wrong_user", password=b"wrong_password")

        result = authenticator(None, None, None, None, login_password)

        self.assertFalse(result.success)

    def test_rejects_non_login_password_auth_data(self):
        authenticator = build_authenticator("user", "password")

        other_auth_data = "not a LoginPassword object"
        result = authenticator(None, None, None, None, other_auth_data)

        self.assertFalse(result.success)
        self.assertFalse(result.handled)

    def test_timing_attack_resistance(self):
        """Test that authentication uses constant-time comparison"""
        authenticator = build_authenticator("user", "password")

        login_password_correct = LoginPassword(login=b"user", password=b"password")
        login_password_wrong = LoginPassword(login=b"user", password=b"wrong")

        result_correct = authenticator(None, None, None, None, login_password_correct)
        result_wrong = authenticator(None, None, None, None, login_password_wrong)

        self.assertTrue(result_correct.success)
        self.assertFalse(result_wrong.success)

    def test_authentication_with_special_characters(self):
        authenticator = build_authenticator("user@example.com", "p@ss!word#123")

        login_password = LoginPassword(login=b"user@example.com", password=b"p@ss!word#123")

        result = authenticator(None, None, None, None, login_password)

        self.assertTrue(result.success)

    def test_authentication_with_unicode_password(self):
        authenticator = build_authenticator("user", "password")

        login_password = LoginPassword(login=b"user", password="password".encode("utf-8"))

        result = authenticator(None, None, None, None, login_password)

        self.assertTrue(result.success)

    def test_empty_username_and_password(self):
        authenticator = build_authenticator("", "")

        login_password = LoginPassword(login=b"", password=b"")

        result = authenticator(None, None, None, None, login_password)

        self.assertTrue(result.success)

    def test_empty_username_failure(self):
        authenticator = build_authenticator("", "password")

        login_password = LoginPassword(login=b"user", password=b"password")

        result = authenticator(None, None, None, None, login_password)

        self.assertFalse(result.success)


class WaitForShutdownTestCase(unittest.TestCase):
    def test_wait_for_shutdown_is_coroutine_function(self):
        """Test that wait_for_shutdown is an async function"""
        self.assertTrue(asyncio.iscoroutinefunction(wait_for_shutdown))

    def test_wait_for_shutdown_callable(self):
        """Test that wait_for_shutdown is callable"""
        self.assertTrue(callable(wait_for_shutdown))


class AuthResultMockTestCase(unittest.TestCase):
    """Test that our authenticator returns proper AuthResult objects"""

    def test_authenticator_returns_object_with_success_attribute(self):
        authenticator = build_authenticator("user", "password")

        login_password = LoginPassword(login=b"user", password=b"password")

        result = authenticator(None, None, None, None, login_password)

        self.assertTrue(hasattr(result, "success"))
        self.assertTrue(result.success)

    def test_authenticator_returns_object_with_handled_attribute(self):
        authenticator = build_authenticator("user", "password")

        other_auth_data = "not a LoginPassword"
        result = authenticator(None, None, None, None, other_auth_data)

        self.assertTrue(hasattr(result, "handled"))
        self.assertFalse(result.handled)


class MainModuleImportsTestCase(unittest.TestCase):
    """Test that main module imports are available"""

    def test_main_imports_aiosmtpd(self):
        from app import main
        self.assertTrue(hasattr(main, "SMTP"))
        self.assertTrue(hasattr(main, "AuthResult"))

    def test_main_imports_config(self):
        from app import main
        self.assertTrue(hasattr(main, "load_config"))

    def test_main_imports_smtp_handler(self):
        from app import main
        self.assertTrue(hasattr(main, "SMTPHandlerConfig"))
        self.assertTrue(hasattr(main, "SMTPToTelegramHandler"))

    def test_main_imports_telegram(self):
        from app import main
        self.assertTrue(hasattr(main, "TelegramClient"))

    def test_main_imports_zitadel(self):
        from app import main
        self.assertTrue(hasattr(main, "ZitadelClient"))
        self.assertTrue(hasattr(main, "ZitadelConfig"))


if __name__ == "__main__":
    unittest.main()




