# Telegram Bot Suite — Multi-Bot Architecture

A professional, scalable system for building, running, and managing unlimited Telegram bots inside a single Python project.  
Supports Python 3.12, python‑telegram‑bot 22+, Linux systemd, Windows/WSL, and includes a Streamlit management dashboard.

---

## 🚀 Why This Project?

Developers often maintain multiple Telegram bots, each requiring:
- Separate runtime
- Separate .env file
- Isolated logging
- Independent configs
- Systemd services
- A unified control panel

This system solves all of that by providing **one project** capable of hosting **unlimited fully isolated bots**, each inside its own folder.

---

## 📁 Project Structure

```
telegram_bot/
│
├── apps/
│   ├── hello_bot/              # Simple starter bot
│   ├── quran_hifz_bot/         # Advanced Quran memorization bot
│   └── shop_bot/               # Full e-commerce bot
│
├── apps/dashboard/             # Streamlit dashboard
│   └── streamlit_app.py
│
├── core/
│   ├── env.py                  # Environment loader
│   └── logging.py              # Global logging system
│
├── tests/
│
├── run.py
├── run_bot.py
├── pyproject.toml
└── README.md
```

---

## ✨ Key Features

### ✔ Multi‑Bot System  
Each bot has:
- Its own folder
- bot.py
- config.py
- handlers
- models
- storage
- its own `.env` file

### ✔ Shared Core System  
- `core/env.py` for safe environment loading  
- `core/logging.py` for secure logging without leaking tokens  

### ✔ Full Dashboard (Streamlit)
- Detect all bots automatically  
- Send test messages  
- Manage systemd services  
- View logs  
- Get Chat IDs  

### ✔ systemd Support  
Each bot can run permanently as a Linux service.

### ✔ CI Ready  
GitHub Actions included.

### ✔ Modern Python Stack  
- Python 3.12  
- Async  
- PTB v22+  
- dotenv  
- Streamlit  

---

## 🛠 Installation

1. Create virtual environment:
```bash
python3 -m venv .venv
source .venv/bin/activate
```

2. Install project:
```bash
pip install -e .
```

---

## 🤖 Creating a New Bot

Create:

```
apps/<bot_name>/
```

Example structure:
```
apps/my_new_bot/
│
├── bot.py
├── config.py
├── handlers.py
└── .env
```

Example `.env`:
```
TELEGRAM_BOT_TOKEN=123456:ABCDEF
BOT_NAME=my_new_bot
```

Minimal `bot.py`:
```python
from telegram.ext import ApplicationBuilder, CommandHandler
from core.env import load_env, get_env
from core.logging import setup_logging
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
ENV_PATH = BASE_DIR / ".env"

async def start(update, context):
    await update.message.reply_text("Hello from my new bot!")

def main():
    setup_logging()
    load_env(ENV_PATH)

    token = get_env("TELEGRAM_BOT_TOKEN")

    app = ApplicationBuilder().token(token).build()
    app.add_handler(CommandHandler("start", start))

    app.run_polling()

if __name__ == "__main__":
    main()
```

---

## ▶️ Running Any Bot Locally

```bash
python apps/<bot_name>/bot.py
```

Example:
```bash
python apps/hello_bot/bot.py
```

---

## 🟢 Running as systemd Service (Linux)

1. Create service file:
```bash
sudo nano /etc/systemd/system/hello_bot.service
```

2. Add:
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

3. Enable & start:
```bash
sudo systemctl daemon-reload
sudo systemctl enable hello_bot
sudo systemctl start hello_bot
```

4. Logs:
```bash
sudo journalctl -u hello_bot -f
```

---

## 🖥 Streamlit Dashboard

Run:
```bash
streamlit run apps/dashboard/streamlit_app.py
```

The dashboard allows:
- Bot selection
- Token visibility (masked)
- Sending messages
- Getting Chat IDs
- systemd control
- Viewing logs

---

## 📌 Built‑in Bots

### 1) hello_bot  
Simple starter template.

### 2) quran_hifz_bot  
Advanced Quran memorization assistant with:
- Goals  
- Daily progress  
- Menus  
- Conversation handlers  
- JSON storage  

### 3) shop_bot  
E‑commerce bot with:
- Products  
- Cart  
- Checkout  
- Admin notifications  

---

## 🧪 Tests

```bash
python -m unittest discover -s tests -v
```

---

## 📄 License  
MIT License  
© 2025 TamerOnLine

---

## ❤️ Developer  
Created by **TamerOnLine**  
Fully expandable — add as many bots and features as you need.
