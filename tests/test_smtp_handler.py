import unittest
import ipaddress
from unittest.mock import AsyncMock, Mock
from dataclasses import dataclass

from app.smtp_handler import SMTPToTelegramHandler, SMTPHandlerConfig


@dataclass
class MockSession:
    peer: tuple[str, int] = ("192.168.1.1", 12345)
    authenticated: bool = False


@dataclass
class MockEnvelope:
    mail_from: str = "sender@example.com"
    rcpt_tos: list[str] = None
    content: bytes = b"test message"

    def __post_init__(self):
        if self.rcpt_tos is None:
            self.rcpt_tos = ["recipient@example.com"]


class SMTPHandlerConfigTestCase(unittest.TestCase):
    def test_creates_config_with_required_fields(self):
        networks = [ipaddress.ip_network("192.168.0.0/16")]
        config = SMTPHandlerConfig(
            allowed_networks=networks,
            max_message_bytes=10485760,
            auth_required=True,
        )
        self.assertEqual(config.allowed_networks, networks)
        self.assertEqual(config.max_message_bytes, 10485760)
        self.assertTrue(config.auth_required)

    def test_config_defaults_auth_required_to_true(self):
        networks = []
        config = SMTPHandlerConfig(
            allowed_networks=networks,
            max_message_bytes=1024,
        )
        self.assertTrue(config.auth_required)


class SMTPToTelegramHandlerTestCase(unittest.TestCase):
    def setUp(self):
        self.config = SMTPHandlerConfig(
            allowed_networks=[
                ipaddress.ip_network("192.168.0.0/16"),
                ipaddress.ip_network("127.0.0.0/8"),
            ],
            max_message_bytes=10485760,
            auth_required=True,
        )
        self.telegram_client = AsyncMock()
        self.zitadel_client = Mock()
        self.handler = SMTPToTelegramHandler(
            config=self.config,
            telegram_client=self.telegram_client,
            zitadel_client=self.zitadel_client,
        )

    def test_handler_initialization(self):
        self.assertEqual(self.handler.config, self.config)
        self.assertEqual(self.handler.telegram_client, self.telegram_client)
        self.assertEqual(self.handler.zitadel_client, self.zitadel_client)

    def test_is_allowed_ip_accepts_allowed_ipv4(self):
        self.assertTrue(self.handler._is_allowed_ip("192.168.1.1"))
        self.assertTrue(self.handler._is_allowed_ip("127.0.0.1"))

    def test_is_allowed_ip_rejects_disallowed_ipv4(self):
        self.assertFalse(self.handler._is_allowed_ip("10.0.0.1"))
        self.assertFalse(self.handler._is_allowed_ip("8.8.8.8"))

    def test_is_allowed_ip_handles_invalid_ip(self):
        self.assertFalse(self.handler._is_allowed_ip("not-an-ip"))
        self.assertFalse(self.handler._is_allowed_ip(""))

    def test_is_allowed_ip_accepts_allowed_ipv6(self):
        config = SMTPHandlerConfig(
            allowed_networks=[ipaddress.ip_network("::1/128")],
            max_message_bytes=1024,
        )
        handler = SMTPToTelegramHandler(
            config=config,
            telegram_client=AsyncMock(),
            zitadel_client=None,
        )
        self.assertTrue(handler._is_allowed_ip("::1"))

    def test_handler_with_no_zitadel_client(self):
        """Test that handler can be initialized without zitadel"""
        handler = SMTPToTelegramHandler(
            config=self.config,
            telegram_client=self.telegram_client,
            zitadel_client=None,
        )
        self.assertIsNone(handler.zitadel_client)

    def test_is_allowed_ip_with_network_containing_single_ip(self):
        """Test IP checking with /32 network"""
        config = SMTPHandlerConfig(
            allowed_networks=[ipaddress.ip_network("192.168.1.100/32")],
            max_message_bytes=1024,
        )
        handler = SMTPToTelegramHandler(
            config=config,
            telegram_client=AsyncMock(),
            zitadel_client=None,
        )
        self.assertTrue(handler._is_allowed_ip("192.168.1.100"))
        self.assertFalse(handler._is_allowed_ip("192.168.1.101"))

    def test_is_allowed_ip_with_broadcast_address(self):
        """Test that broadcast addresses are handled"""
        config = SMTPHandlerConfig(
            allowed_networks=[ipaddress.ip_network("192.168.1.0/24")],
            max_message_bytes=1024,
        )
        handler = SMTPToTelegramHandler(
            config=config,
            telegram_client=AsyncMock(),
            zitadel_client=None,
        )
        self.assertTrue(handler._is_allowed_ip("192.168.1.255"))

    def test_config_with_different_limits(self):
        """Test creating configs with different message limits"""
        config1 = SMTPHandlerConfig(
            allowed_networks=[],
            max_message_bytes=1024,
        )
        config2 = SMTPHandlerConfig(
            allowed_networks=[],
            max_message_bytes=10485760,
        )
        self.assertEqual(config1.max_message_bytes, 1024)
        self.assertEqual(config2.max_message_bytes, 10485760)


if __name__ == "__main__":
    unittest.main()


