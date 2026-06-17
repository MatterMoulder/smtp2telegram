import unittest
from unittest.mock import Mock, patch
import base64

from app.zitadel import ZitadelConfig, ZitadelClient


class ZitadelConfigTestCase(unittest.TestCase):
    def test_creates_config_with_required_fields(self):
        config = ZitadelConfig(
            base_url="https://zitadel.example.com",
            pkay="test_private_key_data",
        )
        self.assertEqual(config.base_url, "https://zitadel.example.com")
        self.assertEqual(config.pkay, "test_private_key_data")

    def test_config_is_frozen(self):
        config = ZitadelConfig(
            base_url="https://zitadel.example.com",
            pkay="key",
        )
        with self.assertRaises(Exception):
            config.base_url = "https://new.example.com"


class ZitadelClientTestCase(unittest.TestCase):
    def setUp(self):
        self.config = ZitadelConfig(
            base_url="https://zitadel.example.com",
            pkay="test_key",
        )

    @patch("app.zitadel.Zitadel")
    def test_initialization(self, mock_zitadel):
        mock_client = Mock()
        mock_zitadel.with_private_key.return_value = mock_client

        client = ZitadelClient(self.config)

        mock_zitadel.with_private_key.assert_called_once_with(
            "https://zitadel.example.com",
            "test_key",
        )
        self.assertEqual(client.client, mock_client)
        self.assertEqual(client.config, self.config)

    @patch("app.zitadel.Zitadel")
    def test_get_user_id_by_email_success(self, mock_zitadel):
        mock_client = Mock()
        mock_zitadel.with_private_key.return_value = mock_client

        mock_user = Mock()
        mock_user.user_id = "user-123"
        mock_response = Mock()
        mock_response.result = [mock_user]
        mock_client.users.list_users.return_value = mock_response

        client = ZitadelClient(self.config)
        user_id = client.get_user_id_by_email("test@example.com")

        self.assertEqual(user_id, "user-123")
        mock_client.users.list_users.assert_called_once()

    @patch("app.zitadel.Zitadel")
    def test_get_user_id_by_email_not_found(self, mock_zitadel):
        mock_client = Mock()
        mock_zitadel.with_private_key.return_value = mock_client

        mock_response = Mock()
        mock_response.result = []
        mock_client.users.list_users.return_value = mock_response

        client = ZitadelClient(self.config)
        user_id = client.get_user_id_by_email("nonexistent@example.com")

        self.assertIsNone(user_id)

    @patch("app.zitadel.Zitadel")
    def test_get_user_id_by_email_none_result(self, mock_zitadel):
        mock_client = Mock()
        mock_zitadel.with_private_key.return_value = mock_client

        mock_response = Mock()
        mock_response.result = None
        mock_client.users.list_users.return_value = mock_response

        client = ZitadelClient(self.config)
        user_id = client.get_user_id_by_email("test@example.com")

        self.assertIsNone(user_id)

    @patch("app.zitadel.Zitadel")
    def test_list_user_metadata_success(self, mock_zitadel):
        mock_client = Mock()
        mock_zitadel.with_private_key.return_value = mock_client

        mock_metadata = Mock()
        mock_metadata.key = "telegram.chat_id"
        mock_metadata.value = base64.b64encode(b"123456789").decode()

        mock_response = Mock()
        mock_response.metadata = [mock_metadata]
        mock_client.users.list_user_metadata.return_value = mock_response

        client = ZitadelClient(self.config)
        metadata = client.list_user_metadata("user-123")

        self.assertEqual(metadata, {"telegram.chat_id": "123456789"})

    @patch("app.zitadel.Zitadel")
    def test_list_user_metadata_empty(self, mock_zitadel):
        mock_client = Mock()
        mock_zitadel.with_private_key.return_value = mock_client

        mock_response = Mock()
        mock_response.metadata = []
        mock_client.users.list_user_metadata.return_value = mock_response

        client = ZitadelClient(self.config)
        metadata = client.list_user_metadata("user-123")

        self.assertEqual(metadata, {})

    @patch("app.zitadel.Zitadel")
    def test_list_user_metadata_none(self, mock_zitadel):
        mock_client = Mock()
        mock_zitadel.with_private_key.return_value = mock_client

        mock_response = Mock()
        mock_response.metadata = None
        mock_client.users.list_user_metadata.return_value = mock_response

        client = ZitadelClient(self.config)
        metadata = client.list_user_metadata("user-123")

        self.assertEqual(metadata, {})

    @patch("app.zitadel.Zitadel")
    def test_list_user_metadata_by_email_success(self, mock_zitadel):
        mock_client = Mock()
        mock_zitadel.with_private_key.return_value = mock_client

        # Setup for get_user_id_by_email
        mock_user = Mock()
        mock_user.user_id = "user-123"
        mock_list_response = Mock()
        mock_list_response.result = [mock_user]
        mock_client.users.list_users.return_value = mock_list_response

        # Setup for list_user_metadata
        mock_metadata = Mock()
        mock_metadata.key = "telegram.chat_id"
        mock_metadata.value = base64.b64encode(b"987654321").decode()
        mock_metadata_response = Mock()
        mock_metadata_response.metadata = [mock_metadata]
        mock_client.users.list_user_metadata.return_value = mock_metadata_response

        client = ZitadelClient(self.config)
        metadata = client.list_user_metadata_by_email("test@example.com")

        self.assertEqual(metadata, {"telegram.chat_id": "987654321"})

    @patch("app.zitadel.Zitadel")
    def test_list_user_metadata_by_email_user_not_found(self, mock_zitadel):
        mock_client = Mock()
        mock_zitadel.with_private_key.return_value = mock_client

        mock_response = Mock()
        mock_response.result = []
        mock_client.users.list_users.return_value = mock_response

        client = ZitadelClient(self.config)
        metadata = client.list_user_metadata_by_email("nonexistent@example.com")

        self.assertEqual(metadata, {})

    @patch("app.zitadel.Zitadel")
    def test_get_telegram_id_from_metadata_success(self, mock_zitadel):
        mock_client = Mock()
        mock_zitadel.with_private_key.return_value = mock_client

        mock_metadata = Mock()
        mock_metadata.key = "telegram.chat_id"
        mock_metadata.value = base64.b64encode(b"999888777").decode()
        mock_response = Mock()
        mock_response.metadata = [mock_metadata]
        mock_client.users.list_user_metadata.return_value = mock_response

        client = ZitadelClient(self.config)
        chat_id = client.get_telegram_id_from_metadata("user-123")

        self.assertEqual(chat_id, "999888777")

    @patch("app.zitadel.Zitadel")
    def test_get_telegram_id_from_metadata_not_found(self, mock_zitadel):
        mock_client = Mock()
        mock_zitadel.with_private_key.return_value = mock_client

        mock_response = Mock()
        mock_response.metadata = []
        mock_client.users.list_user_metadata.return_value = mock_response

        client = ZitadelClient(self.config)
        chat_id = client.get_telegram_id_from_metadata("user-123")

        self.assertIsNone(chat_id)

    @patch("app.zitadel.Zitadel")
    def test_get_telegram_id_from_metadata_by_email_success(self, mock_zitadel):
        mock_client = Mock()
        mock_zitadel.with_private_key.return_value = mock_client

        # Setup for get_user_id_by_email
        mock_user = Mock()
        mock_user.user_id = "user-456"
        mock_list_response = Mock()
        mock_list_response.result = [mock_user]
        mock_client.users.list_users.return_value = mock_list_response

        # Setup for list_user_metadata
        mock_metadata = Mock()
        mock_metadata.key = "telegram.chat_id"
        mock_metadata.value = base64.b64encode(b"111222333").decode()
        mock_metadata_response = Mock()
        mock_metadata_response.metadata = [mock_metadata]
        mock_client.users.list_user_metadata.return_value = mock_metadata_response

        client = ZitadelClient(self.config)
        chat_id = client.get_telegram_id_from_metadata_by_email("user@example.com")

        self.assertEqual(chat_id, "111222333")

    @patch("app.zitadel.Zitadel")
    def test_get_telegram_id_from_metadata_by_email_user_not_found(self, mock_zitadel):
        mock_client = Mock()
        mock_zitadel.with_private_key.return_value = mock_client

        mock_response = Mock()
        mock_response.result = []
        mock_client.users.list_users.return_value = mock_response

        client = ZitadelClient(self.config)
        chat_id = client.get_telegram_id_from_metadata_by_email("nonexistent@example.com")

        self.assertIsNone(chat_id)

    @patch("app.zitadel.Zitadel")
    def test_get_telegram_id_from_metadata_by_email_no_telegram_id(self, mock_zitadel):
        mock_client = Mock()
        mock_zitadel.with_private_key.return_value = mock_client

        # Setup for get_user_id_by_email
        mock_user = Mock()
        mock_user.user_id = "user-789"
        mock_list_response = Mock()
        mock_list_response.result = [mock_user]
        mock_client.users.list_users.return_value = mock_list_response

        # Setup for list_user_metadata with no telegram.chat_id
        mock_metadata = Mock()
        mock_metadata.key = "other.key"
        mock_metadata.value = base64.b64encode(b"some_value").decode()
        mock_metadata_response = Mock()
        mock_metadata_response.metadata = [mock_metadata]
        mock_client.users.list_user_metadata.return_value = mock_metadata_response

        client = ZitadelClient(self.config)
        chat_id = client.get_telegram_id_from_metadata_by_email("user@example.com")

        self.assertIsNone(chat_id)

    @patch("app.zitadel.Zitadel")
    def test_list_user_metadata_multiple_keys(self, mock_zitadel):
        mock_client = Mock()
        mock_zitadel.with_private_key.return_value = mock_client

        mock_metadata1 = Mock()
        mock_metadata1.key = "telegram.chat_id"
        mock_metadata1.value = base64.b64encode(b"123456").decode()

        mock_metadata2 = Mock()
        mock_metadata2.key = "custom.field"
        mock_metadata2.value = base64.b64encode(b"custom_value").decode()

        mock_response = Mock()
        mock_response.metadata = [mock_metadata1, mock_metadata2]
        mock_client.users.list_user_metadata.return_value = mock_response

        client = ZitadelClient(self.config)
        metadata = client.list_user_metadata("user-123")

        self.assertEqual(len(metadata), 2)
        self.assertEqual(metadata["telegram.chat_id"], "123456")
        self.assertEqual(metadata["custom.field"], "custom_value")

    @patch("app.zitadel.Zitadel")
    def test_get_user_id_by_email_with_multiple_results(self, mock_zitadel):
        mock_client = Mock()
        mock_zitadel.with_private_key.return_value = mock_client

        # Returns first user even if multiple results
        mock_user1 = Mock()
        mock_user1.user_id = "user-first"
        mock_user2 = Mock()
        mock_user2.user_id = "user-second"
        mock_response = Mock()
        mock_response.result = [mock_user1, mock_user2]
        mock_client.users.list_users.return_value = mock_response

        client = ZitadelClient(self.config)
        user_id = client.get_user_id_by_email("test@example.com")

        self.assertEqual(user_id, "user-first")


if __name__ == "__main__":
    unittest.main()

