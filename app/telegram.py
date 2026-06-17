from aiogram import Bot, Router, Dispatcher
from aiogram.filters import CommandStart
from aiogram.types import InputRichMessage, Message


class TelegramClient:
    def __init__(
            self,
            token: str
    ):
        self.client = Bot(token=token)
        self.router = Router()

        self._register_handlers()

        self.dp = Dispatcher()
        self.dp.include_router(self.router)

    def _register_handlers(self) -> None:
        @self.router.message(CommandStart())
        async def start_handler(message: Message) -> None:
            user = message.from_user
            chat = message.chat

            await message.answer(
                f"Hi!\n\n"
                f"chat_id: <code>{chat.id}</code>\n"
                f"user_id: <code>{user.id if user else 'unknown'}</code>\n"
                f"username: <code>@{user.username if user and user.username else 'нет'}</code>",
                parse_mode="HTML",
            )

    async def send_rich_html(
            self,
            *,
            chat_id: str | int,
            rich_html: str,
            message_thread_id: int | None = None,
    ) -> None:
        await self.client.send_rich_message(
            chat_id=chat_id,
            message_thread_id=message_thread_id,
            rich_message=InputRichMessage(
                html=rich_html,
                skip_entity_detection=True,
            ),
        )

    async def close(self) -> None:
        await self.client.session.close()