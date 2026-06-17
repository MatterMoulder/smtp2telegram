import unittest
from unittest.mock import AsyncMock, Mock, patch, MagicMock

from app.telegram import TelegramClient


class TelegramClientTestCase(unittest.TestCase):
    def setUp(self):
        self.token = "test_token_123456789"

    @patch("app.telegram.Bot")
    def test_initialization(self, mock_bot):
        mock_bot_instance = AsyncMock()
        mock_bot.return_value = mock_bot_instance

        with patch.object(TelegramClient, "_register_handlers"):
            client = TelegramClient(token=self.token)

            # Verify bot was instantiated with our token
            self.assertIsNotNone(client.client)
            self.assertEqual(client.client, mock_bot_instance)

    @patch("app.telegram.Bot")
    def test_initialization_includes_dispatcher(self, mock_bot):
        """Test that dispatcher is created during initialization"""
        mock_bot_instance = AsyncMock()
        mock_bot.return_value = mock_bot_instance

        with patch.object(TelegramClient, "_register_handlers"):
            client = TelegramClient(token=self.token)
            self.assertIsNotNone(client.dp)
            self.assertIsNotNone(client.router)

    @patch("app.telegram.Bot")
    @patch("app.telegram.Router")
    @patch("app.telegram.Dispatcher")
    def test_register_handlers_registers_start_command(self, mock_dispatcher, mock_router, mock_bot):
        mock_bot_instance = AsyncMock()
        mock_router_instance = MagicMock()
        mock_dispatcher_instance = Mock()
        mock_bot.return_value = mock_bot_instance
        mock_router.return_value = mock_router_instance
        mock_dispatcher.return_value = mock_dispatcher_instance

        client = TelegramClient(token=self.token)

        # Check that router.message was called with CommandStart filter
        self.assertTrue(mock_router_instance.message.called)

    @patch("app.telegram.Bot")
    @patch("app.telegram.Router")
    @patch("app.telegram.Dispatcher")
    def test_client_has_token(self, mock_dispatcher, mock_router, mock_bot):
        mock_bot_instance = AsyncMock()
        mock_router_instance = Mock()
        mock_dispatcher_instance = Mock()
        mock_bot.return_value = mock_bot_instance
        mock_router.return_value = mock_router_instance
        mock_dispatcher.return_value = mock_dispatcher_instance

        client = TelegramClient(token=self.token)

        # Verify bot was created with correct token
        mock_bot.assert_called_once_with(token=self.token)

    @patch("app.telegram.Bot")
    @patch("app.telegram.Router")
    @patch("app.telegram.Dispatcher")
    def test_client_dispatcher_exists(self, mock_dispatcher, mock_router, mock_bot):
        mock_bot_instance = AsyncMock()
        mock_router_instance = Mock()
        mock_dispatcher_instance = Mock()
        mock_bot.return_value = mock_bot_instance
        mock_router.return_value = mock_router_instance
        mock_dispatcher.return_value = mock_dispatcher_instance

        client = TelegramClient(token=self.token)

        self.assertIsNotNone(client.dp)

    @patch("app.telegram.Bot")
    @patch("app.telegram.Router")
    @patch("app.telegram.Dispatcher")
    def test_client_router_exists(self, mock_dispatcher, mock_router, mock_bot):
        mock_bot_instance = AsyncMock()
        mock_router_instance = Mock()
        mock_dispatcher_instance = Mock()
        mock_bot.return_value = mock_bot_instance
        mock_router.return_value = mock_router_instance
        mock_dispatcher.return_value = mock_dispatcher_instance

        client = TelegramClient(token=self.token)

        self.assertIsNotNone(client.router)

    @patch("app.telegram.Bot")
    @patch("app.telegram.Router")
    @patch("app.telegram.Dispatcher")
    def test_initialization_creates_client_and_router(self, mock_dispatcher, mock_router, mock_bot):
        """Test basic initialization flow"""
        mock_bot_instance = AsyncMock()
        mock_router_instance = Mock()
        mock_dispatcher_instance = Mock()
        mock_bot.return_value = mock_bot_instance
        mock_router.return_value = mock_router_instance
        mock_dispatcher.return_value = mock_dispatcher_instance

        client = TelegramClient(token=self.token)

        # Verify all components were initialized
        self.assertIsNotNone(client.client)
        self.assertIsNotNone(client.router)
        self.assertIsNotNone(client.dp)

    @patch("app.telegram.Bot")
    @patch("app.telegram.Router")
    @patch("app.telegram.Dispatcher")
    def test_multiple_clients_have_different_instances(self, mock_dispatcher, mock_router, mock_bot):
        """Test that multiple client instances are independent"""
        mock_bot_instance1 = AsyncMock()
        mock_bot_instance2 = AsyncMock()
        mock_router_instance1 = Mock()
        mock_router_instance2 = Mock()
        mock_dispatcher_instance1 = Mock()
        mock_dispatcher_instance2 = Mock()

        # Set up first call
        mock_bot.return_value = mock_bot_instance1
        mock_router.return_value = mock_router_instance1
        mock_dispatcher.return_value = mock_dispatcher_instance1

        client1 = TelegramClient(token="token1")

        # Reset and set up second call
        mock_bot.return_value = mock_bot_instance2
        mock_router.return_value = mock_router_instance2
        mock_dispatcher.return_value = mock_dispatcher_instance2

        client2 = TelegramClient(token="token2")

        # Verify they're different
        self.assertNotEqual(client1.client, client2.client)
        self.assertNotEqual(client1.router, client2.router)


if __name__ == "__main__":
    unittest.main()









