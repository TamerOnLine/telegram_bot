
# Telegram Bot Suite — Multi-Bot Architecture

A modular system that allows you to build, run, and manage unlimited Telegram bots inside one unified project, each bot with its own folder, configuration, environment, and systemd service.

This project is ideal for:
- Developers who want to host multiple bots on one machine.
- Bots that must run 24/7 on Linux servers.
- Projects requiring isolated environments per bot.
- Scalable architectures where bots share shared core utilities.

---

## ✨ Key Features
- Unlimited bots placed under `apps/<bot_name>/`
- Each bot has its own `.env`, `bot.py`, handlers, config, etc.
- Shared core modules for logging & environment management
- python-telegram-bot v22+ (async)
- Systemd support for persistent services
- GitHub Actions CI included
- Windows / Linux / WSL support
- Modern Python packaging via pyproject.toml

---

## 📁 Project Structure

```
telegram_bot/
│
├── apps/
│   ├── hello_bot/
│   │   ├── bot.py
│   │   └── .env
│   │
│   └── quran_hifz_bot/
│       ├── bot.py
│       ├── config.py
│       ├── handlers.py
│       ├── helpers.py
│       ├── models.py
│       ├── storage.py
│       ├── README.md
│       └── .env
│
├── core/
│   ├── env.py
│   └── logging.py
│
├── tests/
│   └── test_smoke.py
│
├── pyproject.toml
└── run.py
```

---

## 🛠 Installation

### 1. Create virtual environment
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 2. Install dependencies
```bash
pip install -e .
```

---

## 🆕 Creating a New Bot

Place your bot under:

```
apps/<bot_name>/
```

With files:
```
bot.py
.env
```

Example `.env`:
```
TELEGRAM_BOT_TOKEN=YOUR_TOKEN
BOT_NAME=hello_bot
```

Example bot:
```python
from telegram_bot_suite.base_bot import BaseTelegramBot

class HelloBot(BaseTelegramBot):
    async def handle_message(self, update, context):
        await update.message.reply_text("Hello!")

if __name__ == "__main__":
    HelloBot().run()
```

---

## ▶️ Running Bots

### Run locally
```bash
python apps/hello_bot/bot.py
```

### Run as systemd service
```bash
sudo systemctl start hello_bot
sudo systemctl enable hello_bot
```

---

## 🟢 Logs
```bash
sudo journalctl -u hello_bot -f
```

---

## ✨ Multiple Bots Supported

Each bot lives in its own folder with its own configuration.

---

## 🧪 Tests

Run the included test suite:

```bash
python -m unittest discover -s tests
```

---

## 📄 License
MIT License  
© 2025 TamerOnLine
