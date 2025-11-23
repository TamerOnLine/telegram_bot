# Telegram Bot Suite — Multi-Bot System

A professional modular system to create and run unlimited Telegram bots, each inside its own folder, each with its own `.env`, and running locally or permanently on a Linux server via `systemd`.

Supports:
- Python 3.12+
- Virtualenv
- Editable installation (`pip install -e .`)
- Windows / Linux / GitHub Actions CI
- Persistent systemd services
- Per-bot environment configuration

---

## 1. Project Structure

```
telegram_bot/
│
├── apps/
│   └── hello_bot/
│       ├── bot.py
│       └── .env
│
├── src/
│   └── telegram_bot_suite/
│       ├── __init__.py
│       ├── base_bot.py
│       ├── env_loader.py
│       └── utils.py
│
├── pyproject.toml
└── README.md
```

---

## 2. Installation

### Create virtual environment
```bash
python3 -m vvenv .venv
source .venv/bin/activate
```

### Upgrade pip
```bash
python -m pip install --upgrade pip
```

### Install the project in editable mode
```bash
pip install -e .
```

---

## 3. Create a New Bot (Example: hello_bot)

### Create `.env`
```
BOT_TOKEN=YOUR_TELEGRAM_BOT_TOKEN
BOT_NAME=hello_bot
```

### Create `bot.py`
```python
from telegram_bot_suite.base_bot import BaseTelegramBot

class HelloBot(BaseTelegramBot):
    async def handle_message(self, update, context):
        await update.message.reply_text("Hello! I am alive.")

if __name__ == "__main__":
    HelloBot().run()
```

---

## 4. Run Bot Locally

```bash
python apps/hello_bot/bot.py
```

---

## 5. Run Bot Permanently (systemd)

### Create service file:
```bash
sudo nano /etc/systemd/system/hello_bot.service
```

### Add:
```
[Unit]
Description=Hello Telegram Bot
After=network.target

[Service]
Type=simple
User=tamer
WorkingDirectory=/home/tamer/telegram_bot
ExecStart=/home/tamer/telegram_bot/.venv/bin/python /home/tamer/telegram_bot/apps/hello_bot/bot.py
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

### Enable + start:
```bash
sudo systemctl daemon-reload
sudo systemctl enable hello_bot
sudo systemctl start hello_bot
```

---

## 6. Logs
```bash
sudo journalctl -u hello_bot -f
```

---

## 7. Multiple Bots
Each bot lives under:
```
apps/<bot_name>/
```
Each with its own:
- `bot.py`
- `.env`
- Optional systemd service

---

## 8. License
MIT License.
