from __future__ import annotations

import asyncio
import logging
import secrets
import signal
import ssl

from aiosmtpd.smtp import AuthResult, LoginPassword, SMTP

from app.config import load_config, AppConfig
from app.smtp_handler import SMTPHandlerConfig, SMTPToTelegramHandler
from app.telegram import TelegramClient
from app.zitadel import ZitadelClient, ZitadelConfig


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)

logger = logging.getLogger(__name__)

def build_tls_context(config: AppConfig):
    if not config.smtp_tls_enabled:
        return None

    if config.smtp_tls_cert_file is None:
        raise RuntimeError("SMTP_TLS_CERT_FILE is required when SMTP_TLS_ENABLED=true")

    if config.smtp_tls_key_file is None:
        raise RuntimeError("SMTP_TLS_KEY_FILE is required when SMTP_TLS_ENABLED=true")

    context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)

    context.load_cert_chain(
        certfile=config.smtp_tls_cert_file,
        keyfile=config.smtp_tls_key_file,
    )

    return context

def build_authenticator(username: str, password: str):
    expected_login = username.encode("utf-8")
    expected_password = password.encode("utf-8")

    def authenticator(server, session, envelope, mechanism, auth_data):
        if not isinstance(auth_data, LoginPassword):
            return AuthResult(success=False, handled=False)

        login_ok = secrets.compare_digest(auth_data.login, expected_login)
        password_ok = secrets.compare_digest(auth_data.password, expected_password)

        if login_ok and password_ok:
            return AuthResult(success=True)

        return AuthResult(success=False, handled=False)

    return authenticator


async def wait_for_shutdown() -> None:
    stop_event = asyncio.Event()
    loop = asyncio.get_running_loop()

    def stop() -> None:
        stop_event.set()

    loop.add_signal_handler(signal.SIGTERM, stop)
    loop.add_signal_handler(signal.SIGINT, stop)

    await stop_event.wait()


async def main_async() -> None:
    config = load_config()

    authenticator = build_authenticator(
        config.smtp_username,
        config.smtp_password,
    )

    telegram_client = TelegramClient(
        token=config.telegram_bot_token
    )

    if not config.zitadel_enabled:
        if not config.telegram_chat_id:
            logger.error("Telegram chat ID is not set, nothing to do")
            return
        elif not config.telegram_chat_id.strip():
            logger.error("Telegram chat ID is empty, nothing to do")
            return
        else:
            pass

    if config.zitadel_enabled:
        if not config.zitadel_base_url or not config.zitadel_pkey_file:
            logger.error("Zitadel integration enabled but base URL or private key is not set, nothing to do")
            return

        if not config.zitadel_base_url.strip() or not config.zitadel_pkey_file.strip():
            logger.error("Zitadel integration enabled but base URL or private key is empty, nothing to do")
            return

    zitadel_config = None
    zitadel_cli = None

    if config.zitadel_enabled:
        zitadel_config = ZitadelConfig(
            base_url=config.zitadel_base_url,
            pkay=config.zitadel_pkey_file,
        )
        zitadel_cli = ZitadelClient(zitadel_config)

    handler = SMTPToTelegramHandler(
        config=SMTPHandlerConfig(
            allowed_networks=config.allowed_networks,
            max_message_bytes=config.max_message_bytes,
            auth_required=config.smtp_auth_required,
            tg_chat_id=config.telegram_chat_id
        ),
        telegram_client=telegram_client,
        zitadel_client=zitadel_cli if config.zitadel_enabled else None,
    )

    loop = asyncio.get_running_loop()

    tls_context = build_tls_context(config)

    server = await loop.create_server(
        lambda: SMTP(
            handler,
            data_size_limit=config.max_message_bytes,
            enable_SMTPUTF8=True,
            authenticator=authenticator,
            auth_required=config.smtp_auth_required,
            auth_require_tls=config.smtp_auth_require_tls,
            tls_context=tls_context,
            require_starttls=config.smtp_require_starttls,
        ),
        host=config.smtp_host,
        port=config.smtp_port,
    )

    logger.info(
        "SMTP to Telegram gateway listening on %s:%s",
        config.smtp_host,
        config.smtp_port,
    )

    polling_task = asyncio.create_task(
        telegram_client.dp.start_polling(
            telegram_client.client,
            handle_signals=False,
        )
    )

    try:
        await wait_for_shutdown()
    finally:
        logger.info("Shutting down SMTP server")
        server.close()
        await server.wait_closed()

        logger.info("Stopping Telegram polling")

        polling_task.cancel()

        try:
            await asyncio.wait_for(polling_task, timeout=5)
        except asyncio.CancelledError:
            pass
        except asyncio.TimeoutError:
            logger.warning("Telegram polling did not stop in time")

        await telegram_client.close()

        logger.info("Shutdown complete")


def main() -> None:
    asyncio.run(main_async())


if __name__ == "__main__":
    main()