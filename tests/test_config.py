import unittest
import os
import ipaddress
import tempfile
from unittest.mock import patch

from app.config import (
    get_bool_env,
    get_required_env,
    parse_networks,
    load_config,
)


class GetBoolEnvTestCase(unittest.TestCase):
    def test_returns_default_when_not_set(self):
        with patch.dict(os.environ, {}, clear=True):
            self.assertTrue(get_bool_env("MISSING_VAR", True))
            self.assertFalse(get_bool_env("MISSING_VAR", False))

    def test_parses_true_values(self):
        for value in ["1", "true", "yes", "y", "on"]:
            with patch.dict(os.environ, {"TEST_VAR": value}):
                self.assertTrue(get_bool_env("TEST_VAR", False))

    def test_parses_true_values_case_insensitive(self):
        for value in ["TRUE", "True", "YES", "Yes", "ON", "On"]:
            with patch.dict(os.environ, {"TEST_VAR": value}):
                self.assertTrue(get_bool_env("TEST_VAR", False))

    def test_parses_false_values(self):
        for value in ["0", "false", "no", "off", "anything_else"]:
            with patch.dict(os.environ, {"TEST_VAR": value}):
                self.assertFalse(get_bool_env("TEST_VAR", True))


class GetRequiredEnvTestCase(unittest.TestCase):
    def test_returns_value_when_set(self):
        with patch.dict(os.environ, {"REQUIRED": "test_value"}):
            self.assertEqual(get_required_env("REQUIRED"), "test_value")

    def test_raises_when_not_set(self):
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(RuntimeError) as ctx:
                get_required_env("MISSING")
            self.assertIn("MISSING", str(ctx.exception))
            self.assertIn("Missing required environment variable", str(ctx.exception))

    def test_raises_when_empty_string(self):
        with patch.dict(os.environ, {"EMPTY": ""}):
            with self.assertRaises(RuntimeError):
                get_required_env("EMPTY")


class ParseNetworksTestCase(unittest.TestCase):
    def test_parses_single_ipv4_network(self):
        networks = parse_networks("192.168.0.0/16")
        self.assertEqual(len(networks), 1)
        self.assertEqual(networks[0], ipaddress.ip_network("192.168.0.0/16", strict=False))

    def test_parses_multiple_networks(self):
        networks = parse_networks("127.0.0.0/8,192.168.0.0/16,10.0.0.0/8")
        self.assertEqual(len(networks), 3)

    def test_parses_mixed_ipv4_and_ipv6(self):
        networks = parse_networks("127.0.0.0/8,::1/128")
        self.assertEqual(len(networks), 2)
        self.assertIsInstance(networks[0], ipaddress.IPv4Network)
        self.assertIsInstance(networks[1], ipaddress.IPv6Network)

    def test_ignores_empty_items(self):
        networks = parse_networks("127.0.0.0/8,,192.168.0.0/16,")
        self.assertEqual(len(networks), 2)

    def test_strips_whitespace(self):
        networks = parse_networks("  127.0.0.0/8  ,  192.168.0.0/16  ")
        self.assertEqual(len(networks), 2)

    def test_handles_empty_string(self):
        networks = parse_networks("")
        self.assertEqual(len(networks), 0)

    def test_handles_whitespace_only(self):
        networks = parse_networks("   ,   ,   ")
        self.assertEqual(len(networks), 0)


class LoadConfigTestCase(unittest.TestCase):
    def test_loads_required_config(self):
        env = {
            "TG_BOT_TOKEN": "test_token_123",
        }
        with patch.dict(os.environ, env, clear=True):
            config = load_config()
            self.assertEqual(config.telegram_bot_token, "test_token_123")

    def test_requires_telegram_token(self):
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(RuntimeError):
                load_config()

    def test_loads_smtp_defaults(self):
        env = {"TG_BOT_TOKEN": "token"}
        with patch.dict(os.environ, env, clear=True):
            config = load_config()
            self.assertEqual(config.smtp_host, "0.0.0.0")
            self.assertEqual(config.smtp_port, 2525)
            self.assertEqual(config.smtp_username, "")
            self.assertEqual(config.smtp_password, "")
            self.assertTrue(config.smtp_auth_required)
            self.assertFalse(config.smtp_auth_require_tls)

    def test_loads_custom_smtp_settings(self):
        env = {
            "TG_BOT_TOKEN": "token",
            "SMTP_HOST": "mail.example.com",
            "SMTP_PORT": "587",
            "SMTP_USERNAME": "user@example.com",
            "SMTP_PASSWORD": "secret",
            "SMTP_AUTH_REQUIRED": "false",
            "SMTP_AUTH_REQUIRE_TLS": "true",
        }
        with patch.dict(os.environ, env, clear=True):
            config = load_config()
            self.assertEqual(config.smtp_host, "mail.example.com")
            self.assertEqual(config.smtp_port, 587)
            self.assertEqual(config.smtp_username, "user@example.com")
            self.assertEqual(config.smtp_password, "secret")
            self.assertFalse(config.smtp_auth_required)
            self.assertTrue(config.smtp_auth_require_tls)

    def test_loads_default_networks(self):
        env = {"TG_BOT_TOKEN": "token"}
        with patch.dict(os.environ, env, clear=True):
            config = load_config()
            expected_networks = [
                ipaddress.ip_network("127.0.0.0/8"),
                ipaddress.ip_network("192.168.0.0/16"),
                ipaddress.ip_network("10.0.0.0/8"),
                ipaddress.ip_network("172.16.0.0/12"),
            ]
            self.assertEqual(config.allowed_networks, expected_networks)

    def test_loads_custom_networks(self):
        env = {
            "TG_BOT_TOKEN": "token",
            "ALLOWED_NETWORKS": "192.168.1.0/24,10.0.0.0/8",
        }
        with patch.dict(os.environ, env, clear=True):
            config = load_config()
            self.assertEqual(len(config.allowed_networks), 2)

    def test_loads_message_size_limits(self):
        env = {
            "TG_BOT_TOKEN": "token",
            "MAX_MESSAGE_BYTES": "5242880",
            "MAX_BODY_CHARS": "12000",
        }
        with patch.dict(os.environ, env, clear=True):
            config = load_config()

            self.assertEqual(config.max_message_bytes, 5242880)
            self.assertEqual(config.max_body_chars, 12000)

    def test_loads_zitadel_disabled_by_default(self):
        env = {"TG_BOT_TOKEN": "token"}
        with patch.dict(os.environ, env, clear=True):
            config = load_config()

            self.assertFalse(config.zitadel_enabled)
            self.assertIsNone(config.zitadel_base_url)
            self.assertIsNone(config.zitadel_pkey_file)

    def test_loads_zitadel_config_when_enabled(self):
        with tempfile.NamedTemporaryFile() as pkey_file:
            env = {
                "TG_BOT_TOKEN": "token",
                "ZITADEL_ENABLED": "true",
                "ZITADEL_BASE_URL": "https://custom.zitadel.cloud",
                "ZITADEL_PKEY_FILE": pkey_file.name,
            }

            with patch.dict(os.environ, env, clear=True):
                config = load_config()

                self.assertTrue(config.zitadel_enabled)
                self.assertEqual(config.zitadel_base_url, "https://custom.zitadel.cloud")
                self.assertEqual(config.zitadel_pkey_file, pkey_file.name)

    def test_raises_when_zitadel_enabled_and_pkey_file_missing(self):
        env = {
            "TG_BOT_TOKEN": "token",
            "ZITADEL_ENABLED": "true",
            "ZITADEL_BASE_URL": "https://custom.zitadel.cloud",
            "ZITADEL_PKEY_FILE": "/tmp/does-not-exist-zitadel-pkey.json",
        }

        with patch.dict(os.environ, env, clear=True):
            with self.assertRaises(RuntimeError) as ctx:
                load_config()

            self.assertIn("Required file does not exist", str(ctx.exception))

    def test_config_is_frozen(self):
        env = {"TG_BOT_TOKEN": "token"}
        with patch.dict(os.environ, env, clear=True):
            config = load_config()
            with self.assertRaises(Exception):
                config.telegram_bot_token = "new_token"

    def test_loads_default_message_size_limits(self):
        env = {"TG_BOT_TOKEN": "token"}
        with patch.dict(os.environ, env, clear=True):
            config = load_config()
            self.assertEqual(config.max_message_bytes, 10485760)
            self.assertEqual(config.max_body_chars, 24000)


if __name__ == "__main__":
    unittest.main()

