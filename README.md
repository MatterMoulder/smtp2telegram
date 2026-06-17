# SMTP2Telegram 📬➡️💬

A lightweight Docker-first SMTP gateway that forwards service emails to Telegram with Rich Message formatting, OTP highlighting, and optional ZITADEL-based recipient routing.

![Python](https://img.shields.io/badge/python-3.12%2B-blue)
![Docker](https://img.shields.io/badge/docker-ready-blue)
![License](https://img.shields.io/badge/license-MIT-green)

SMTP2Telegram Rich is designed for homelab, internal services, and identity systems that can send email but cannot send Telegram notifications directly.

## ✨ Features

- 📧 Built-in async SMTP server
- 🔑 SMTP AUTH support
- 🛡️ IP/network allowlist
- 🎨 Telegram Rich Message formatting
- 🔐 OTP / verification code detection
- 📨 Plain text and HTML email parsing
- 📎 Attachment metadata display
- 💬 Single-chat mode for simple setups
- 🪪 Optional ZITADEL routing mode
- 🐳 Docker Compose support
- 🧹 No mail storage and no external SMTP relay

## 🎯 Use Cases

- 🪪 Forward ZITADEL verification emails to Telegram
- 🔐 Send OTP / 2FA codes from internal services to Telegram
- 🏠 Forward NAS, router, UPS, monitoring, and cron email alerts
- 📬 Use Telegram as a notification sink for services that only support SMTP

## ⚙️ How It Works

```text
Service / ZITADEL / NAS / monitoring
        ↓ SMTP
SMTP2Telegram Rich
        ↓ parse email
        ↓ detect OTP
        ↓ format as Telegram Rich Message
Telegram chat
```

In ZITADEL mode:

```text
Email recipient
        ↓
ZITADEL lookup
        ↓
telegram.chat_id metadata
        ↓
Telegram destination
```

## 📦 Requirements

- Python 3.12+
- Docker and Docker Compose for containerized deployment
- Telegram bot token
- Optional: ZITADEL service account private key for routing mode

## 🚀 Quick Start with Docker

```bash
git clone https://github.com/MatterMoulder/smtp2telegram.git
cd smtp2telegram

cp .env.example .env
# edit .env

docker compose up -d --build
```

Check logs:

```bash
docker compose logs -f smtp2telegram
```

## 🔧 Configuration

All configuration is done through environment variables.

### 🔑 Required

```env
TG_BOT_TOKEN=123456:YOUR_TELEGRAM_BOT_TOKEN
```

Get the bot token from [@BotFather](https://t.me/BotFather).

## 🧭 Routing Modes

SMTP2Telegram Rich supports two routing modes.

### 💬 Mode 1: Single Chat

All incoming emails are sent to one Telegram chat.

```env
ZITADEL_ENABLED=false
TG_CHAT_ID=123456789
```

Use this mode when you only need one destination chat.

### 🪪 Mode 2: ZITADEL Routing

Each email recipient is resolved through ZITADEL metadata.

```env
ZITADEL_ENABLED=true
ZITADEL_BASE_URL=https://zitadel.example.com
ZITADEL_PKEY_FILE=/run/secrets/zitadel_pkey
```

In this mode, `TG_CHAT_ID` is not used as the primary destination. The service looks up the recipient and reads the Telegram destination from ZITADEL metadata.

Expected user metadata:

```text
telegram.chat_id = 123456789
```

Optional metadata:

```text
telegram.thread_id = 42
```

## 📧 SMTP Configuration

```env
SMTP_HOST=0.0.0.0
SMTP_PORT=2525

SMTP_USERNAME=telegram
SMTP_PASSWORD=change-this-password
SMTP_AUTH_REQUIRED=true
SMTP_AUTH_REQUIRE_TLS=false
```

For LAN or Docker internal networks, `SMTP_AUTH_REQUIRE_TLS=false` may be acceptable. For untrusted networks, use TLS or keep the service behind VPN/firewall.

## 🛡️ Network Access Control

```env
ALLOWED_NETWORKS=127.0.0.0/8,192.168.1.0/24
MAX_MESSAGE_BYTES=10485760
MAX_BODY_CHARS=24000
```

The service rejects SMTP clients outside `ALLOWED_NETWORKS`.

## 🔐 ZITADEL Private Key

Do not commit private keys to Git.

Add this to `.gitignore`:

```gitignore
.env
pkey.json
*.key
*.pem
```

### 🐳 Docker Compose Secrets

The recommended Docker setup uses Compose secrets.

```yaml
services:
  smtp2telegram:
    build: .
    container_name: smtp2telegram
    restart: unless-stopped

    env_file:
      - .env

    ports:
      - "2525:2525"

    secrets:
      - zitadel_pkey

    environment:
      ZITADEL_PKEY_FILE: /run/secrets/zitadel_pkey

secrets:
  zitadel_pkey:
    file: ./pkey.json
```

With this configuration, `./pkey.json` on the host is mounted inside the container as:

```text
/run/secrets/zitadel_pkey
```

If `ZITADEL_ENABLED=true`, the application should fail on startup when `ZITADEL_PKEY_FILE` is missing or points to a non-existing file.

## 🧾 Example `.env`

### 💬 Single-chat mode

```env
TG_BOT_TOKEN=123456:YOUR_BOT_TOKEN
TG_CHAT_ID=123456789

ZITADEL_ENABLED=false

SMTP_HOST=0.0.0.0
SMTP_PORT=2525
SMTP_USERNAME=telegram
SMTP_PASSWORD=change-this-password
SMTP_AUTH_REQUIRED=true
SMTP_AUTH_REQUIRE_TLS=false

ALLOWED_NETWORKS=127.0.0.0/8,192.168.1.0/24
MAX_MESSAGE_BYTES=10485760
MAX_BODY_CHARS=24000
```

### 🪪 ZITADEL mode

```env
TG_BOT_TOKEN=123456:YOUR_BOT_TOKEN

ZITADEL_ENABLED=true
ZITADEL_BASE_URL=https://zitadel.example.com
ZITADEL_PKEY_FILE=/run/secrets/zitadel_pkey

SMTP_HOST=0.0.0.0
SMTP_PORT=2525
SMTP_USERNAME=telegram
SMTP_PASSWORD=change-this-password
SMTP_AUTH_REQUIRED=true
SMTP_AUTH_REQUIRE_TLS=false

ALLOWED_NETWORKS=127.0.0.0/8,192.168.1.0/24
MAX_MESSAGE_BYTES=10485760
MAX_BODY_CHARS=24000
```

## 🧪 Sending Test Email

Using `swaks`:

```bash
swaks \
  --server 127.0.0.1 \
  --port 2525 \
  --auth LOGIN \
  --auth-user telegram \
  --auth-password 'change-this-password' \
  --from service@example.com \
  --to user@example.com \
  --header "Subject: Verification code" \
  --body "Your verification code is 123456"
```

Using Python:

```python
import smtplib
from email.mime.text import MIMEText

msg = MIMEText("Your verification code is 123456")
msg["Subject"] = "Verification code"
msg["From"] = "service@example.com"
msg["To"] = "user@example.com"

with smtplib.SMTP("127.0.0.1", 2525) as server:
    server.login("telegram", "change-this-password")
    server.send_message(msg)
```

## 🐳 Docker Compose

A minimal Compose setup:

```yaml
services:
  smtp2telegram:
    build: .
    container_name: smtp2telegram
    restart: unless-stopped

    env_file:
      - .env

    ports:
      - "2525:2525"

    read_only: true
    tmpfs:
      - /tmp

    security_opt:
      - no-new-privileges:true

    cap_drop:
      - ALL
```

If ZITADEL is enabled, add the `secrets` section shown above.

## 🛠️ Local Development

```bash
python3.12 -m venv .venv
source .venv/bin/activate

pip install -r requirements.txt

cp .env.example .env
python -m app.main
```

## 🏗️ Architecture

| Module | Purpose |
|---|---|
| `app.main` | Application entrypoint, event loop, SMTP server startup |
| `app.config` | Environment parsing and validation |
| `app.smtp_handler` | SMTP request handling and orchestration |
| `app.mail_parser` | Email parsing, MIME handling, body extraction |
| `app.otp` | OTP / verification code detection |
| `app.rich_formatter` | Telegram Rich HTML formatting |
| `app.telegram` | Telegram Bot API client |
| `app.zitadel` | Optional ZITADEL integration |

## 🔄 Data Flow

```text
SMTP DATA
  ↓
parse_mail()
  ↓
extract OTP
  ↓
resolve destination
  ├─ single-chat mode: TG_CHAT_ID
  └─ ZITADEL mode: recipient → metadata telegram.chat_id
  ↓
build_rich_html()
  ↓
send_rich_message()
```

## 🤖 Telegram Client Notes

The service only sends Telegram messages. It does not need polling, webhook handling, or a dispatcher.

A sender-only Telegram client should only create a `Bot` instance and close the local HTTP session on shutdown.

Do not call the Telegram Bot API `close` method during normal application shutdown. Close the local aiogram session instead.

## 🔒 Security Notes

This project is intended for LAN, VPN, Docker internal networks, and trusted service environments.

Recommended security settings:

- 🧱 Keep SMTP behind firewall, VPN, or Docker internal network
- 🔑 Enable SMTP AUTH
- 🧬 Use a strong SMTP password
- 🛡️ Use `ALLOWED_NETWORKS`
- 🌐 Do not expose the SMTP port publicly unless you know what you are doing
- 🤫 Do not log email bodies or OTP codes
- 🚫 Do not commit `.env` or `pkey.json`
- 🔁 Rotate ZITADEL service account keys when needed
- 🔒 Use TLS when SMTP traffic crosses an untrusted network

## ✅ Testing

Run tests:

```bash
python -m unittest discover -s tests
```

Or with pytest:

```bash
pytest tests/ -v
```

Suggested test coverage:

- config parsing
- SMTP authentication behavior
- IP allowlist behavior
- email parsing
- HTML-to-text fallback
- OTP extraction
- Rich HTML escaping
- Telegram client payload construction
- ZITADEL routing behavior

## 🧯 Troubleshooting

### `failed to read dockerfile: open Dockerfile: no such file or directory`

Compose cannot find `Dockerfile` in the build context.

Make sure the project has:

```text
smtp2telegram/
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── app/
```

Or specify the Dockerfile path explicitly:

```yaml
services:
  smtp2telegram:
    build:
      context: .
      dockerfile: docker/Dockerfile
```

### `530 Authentication required`

SMTP AUTH is enabled, but the client did not authenticate.

Check:

```env
SMTP_USERNAME=telegram
SMTP_PASSWORD=change-this-password
SMTP_AUTH_REQUIRED=true
```

### `Required file does not exist: /run/secrets/zitadel_pkey`

ZITADEL mode is enabled, but the private key was not mounted.

Check:

```yaml
services:
  smtp2telegram:
    secrets:
      - zitadel_pkey

secrets:
  zitadel_pkey:
    file: ./pkey.json
```

### `Unclosed client session`

The aiogram HTTP session was not closed.

Normal shutdown should call:

```python
await bot.session.close()
```

Do not call:

```python
await bot.close()
```

for regular application shutdown.

### Telegram flood control on method `Close`

This happens when the Telegram Bot API `close` method is called repeatedly. It is not needed for normal shutdown.

Use local session close instead:

```python
await bot.session.close()
```

## ❓ FAQ

### Do I need ZITADEL?

No. Use single-chat mode with `TG_CHAT_ID` for a simple setup.

### Can this receive public internet email?

It can listen on any interface, but the project is intended as an internal SMTP gateway, not a public mail server. Do not use it as an open relay.

### Are attachments forwarded?

No. Attachment metadata such as filename, MIME type, and size can be shown, but binary attachments are not uploaded to Telegram.

### Are OTP codes stored?

No. The service is intended to parse and forward messages without storing them.

### Does the bot need polling?

No. For SMTP-to-Telegram delivery, the bot only sends messages.

### Can one bot send to different chats?

Yes. In single-chat mode all messages go to `TG_CHAT_ID`. In ZITADEL mode the destination is resolved per recipient.

## 📄 License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.

## 🙌 Credits

Built with:

- aiosmtpd
- aiogram
- ZITADEL
