from __future__ import annotations

import ipaddress
import logging
from dataclasses import dataclass

from app.mail_parser import parse_mail
from app.rich_formatter import build_rich_html
from app.telegram import TelegramClient
from app.zitadel import ZitadelClient

logger = logging.getLogger(__name__)

@dataclass(frozen=True)
class SMTPHandlerConfig:
    allowed_networks: list[ipaddress.IPv4Network | ipaddress.IPv6Network]
    max_message_bytes: int
    auth_required: bool = True
    tg_chat_id: str | None = None


class SMTPToTelegramHandler:
    def __init__(
            self,
            *,
            config: SMTPHandlerConfig,
            telegram_client: TelegramClient,
            zitadel_client: ZitadelClient | None
    ) -> None:
        self.config = config
        self.telegram_client = telegram_client
        self.zitadel_client = zitadel_client

    def _is_allowed_ip(self, peer_ip: str) -> bool:
        try:
            ip = ipaddress.ip_address(peer_ip)
        except ValueError:
            return False

        return any(ip in network for network in self.config.allowed_networks)

    async def handle_CONNECT(self, server, session, envelope, hostname, port):
        peer_ip = session.peer[0]

        if not self._is_allowed_ip(peer_ip):
            logger.warning("Rejected SMTP connection from %s", peer_ip)
            return "554 Access denied"

        logger.info("Accepted SMTP connection from %s", peer_ip)
        return None

    async def handle_DATA(self, server, session, envelope):
        peer_ip = session.peer[0]

        if not self._is_allowed_ip(peer_ip):
            logger.warning("Rejected DATA from disallowed peer %s", peer_ip)
            return "554 Access denied"

        if self.config.auth_required and not getattr(session, "authenticated", False):
            logger.warning("Rejected unauthenticated DATA from %s", peer_ip)
            return "530 Authentication required"

        raw = envelope.content or b""

        if len(raw) > self.config.max_message_bytes:
            logger.warning(
                "Rejected oversized message from %s: %s bytes",
                peer_ip,
                len(raw),
            )
            return "552 Message too large"

        try:
            mail = parse_mail(
                raw,
                envelope_from=envelope.mail_from or "",
                envelope_to=envelope.rcpt_tos or [],
                peer=peer_ip,
            )

            rich_html = build_rich_html(mail)

            chat_ids = []
            if self.zitadel_client:
                if len(envelope.rcpt_tos) > 1:
                    for rcpt in envelope.rcpt_tos:
                        chat_id = self.zitadel_client.get_telegram_id_from_metadata_by_email(rcpt)
                        if chat_id:
                            chat_ids.append(chat_id)
                        else:
                            logger.warning(
                                "No Telegram chat ID found for email %s from peer %s",
                                rcpt,
                                peer_ip,
                            )
                    if not chat_ids:
                        return "550 No Telegram chat ID found for any recipient"
                elif len(envelope.rcpt_tos) == 1:
                    chat_ids = [self.zitadel_client.get_telegram_id_from_metadata_by_email(envelope.rcpt_tos[0])]
                else:
                    logger.warning(
                        "No recipients found in envelope from peer %s",
                        peer_ip,
                    )
                    return "550 No recipients found"
            else:
                chat_ids = [self.config.tg_chat_id]

            if not chat_ids:
                logger.warning(
                    "No Telegram chat ID found for email %s from peer %s",
                    mail.envelope_from,
                    peer_ip,
                )
                return "550 No Telegram chat ID found for sender"

            for chat_id in chat_ids:
                await self.telegram_client.send_rich_html(
                    chat_id=chat_id,
                    rich_html=rich_html,
                )

            logger.info(
                "Delivered message to Telegram: peer=%s from=%s to=%s subject=%r size=%s",
                peer_ip,
                envelope.mail_from,
                envelope.rcpt_tos,
                mail.subject,
                len(raw),
            )

            return "250 OK: sent to Telegram"

        except Exception:
            logger.exception(
                "Failed to process message: peer=%s from=%s to=%s size=%s",
                peer_ip,
                envelope.mail_from,
                envelope.rcpt_tos,
                len(raw),
            )
            return "451 Temporary local error"