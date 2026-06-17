from __future__ import annotations

import ipaddress
import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class AppConfig:
    telegram_bot_token: str
    telegram_chat_id: str | None

    smtp_host: str
    smtp_port: int

    smtp_username: str
    smtp_password: str
    smtp_auth_required: bool
    smtp_tls_enabled: bool
    smtp_auth_require_tls: bool
    smtp_require_starttls: bool
    smtp_tls_cert_file: str | None
    smtp_tls_key_file: str | None

    allowed_networks: list[ipaddress.IPv4Network | ipaddress.IPv6Network]

    max_message_bytes: int
    max_body_chars: int

    zitadel_enabled: bool
    zitadel_base_url: str | None
    zitadel_pkey_file: str | None


def get_bool_env(name: str, default: bool) -> bool:
    value = os.environ.get(name)

    if value is None:
        return default

    return value.lower() in {"1", "true", "yes", "y", "on"}


def get_required_env(name: str) -> str:
    value = os.environ.get(name)

    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")

    return value

def get_required_file_path_env(name: str) -> str:
    value = os.environ.get(name)

    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")

    path = Path(value)

    if not path.exists():
        raise RuntimeError(f"Required file does not exist: {value}")

    if not path.is_file():
        raise RuntimeError(f"Required path is not a file: {value}")

    return value


def parse_networks(value: str) -> list[ipaddress.IPv4Network | ipaddress.IPv6Network]:
    networks = []

    for item in value.split(","):
        item = item.strip()
        if not item:
            continue
        networks.append(ipaddress.ip_network(item, strict=False))

    return networks


def load_config() -> AppConfig:
    return AppConfig(
        telegram_bot_token=get_required_env("TG_BOT_TOKEN"),
        telegram_chat_id=os.environ.get("TG_CHAT_ID", None),

        smtp_host=os.environ.get("SMTP_HOST", "0.0.0.0"),
        smtp_port=int(os.environ.get("SMTP_PORT", "2525")),

        smtp_username=os.environ.get("SMTP_USERNAME", ""),
        smtp_password=os.environ.get("SMTP_PASSWORD", ""),
        smtp_auth_required=get_bool_env("SMTP_AUTH_REQUIRED", True),
        smtp_tls_enabled = get_bool_env("SMTP_TLS_ENABLED", False),
        smtp_auth_require_tls=get_bool_env("SMTP_AUTH_REQUIRE_TLS", False),
        smtp_require_starttls=get_bool_env("SMTP_REQUIRE_STARTTLS", False),

        smtp_tls_cert_file = (
            get_required_file_path_env("SMTP_TLS_CERT_FILE")
            if get_bool_env("SMTP_TLS_ENABLED", False)
            else None
        ),

        smtp_tls_key_file = (
            get_required_file_path_env("SMTP_TLS_KEY_FILE")
            if get_bool_env("SMTP_TLS_ENABLED", False)
            else None
        ),

        allowed_networks=parse_networks(
            os.environ.get(
                "ALLOWED_NETWORKS",
                "127.0.0.0/8,192.168.0.0/16,10.0.0.0/8,172.16.0.0/12",
            )
        ),

        max_message_bytes=int(os.environ.get("MAX_MESSAGE_BYTES", "10485760")),
        max_body_chars=int(os.environ.get("MAX_BODY_CHARS", "24000")),

        zitadel_enabled=get_bool_env("ZITADEL_ENABLED", False),
        zitadel_base_url=os.environ.get("ZITADEL_BASE_URL", None),
        zitadel_pkey_file = (
            get_required_file_path_env("ZITADEL_PKEY_FILE")
            if get_bool_env("ZITADEL_ENABLED", False)
            else None
        ),
    )