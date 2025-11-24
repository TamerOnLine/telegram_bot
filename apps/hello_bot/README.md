
# Hello Bot — Simple Telegram Starter Bot

`hello_bot` is a minimal Telegram bot designed as a clean starter template inside the **Multi‑Bot Suite**.  
It demonstrates loading `.env`, using shared core modules, defining simple commands, and running a fully async Telegram bot using **python‑telegram‑bot 22+**.

This bot is ideal as a foundation for creating new bots in the system.

---

## 🚀 Features

- `/start` — friendly welcome message
- `/ping` — simple health‑check command
- Modular structure using shared `core/` utilities
- Loads configuration from `.env`
- Uses structured logging
- Runs via polling or systemd
- Extremely simple and easy to extend

---

## 📁 Project Structure

```
apps/hello_bot/
│
├── bot.py     # Main bot logic
└── .env       # Bot-specific environment variables
```

Shared modules used by this bot:

```
core/env.py        # load and read environment variables
core/logging.py    # global logging setup
```

---

## 🔐 .env Configuration

Place this file inside:

```
apps/hello_bot/.env
```

Example:

```
TELEGRAM_BOT_TOKEN=YOUR_TELEGRAM_BOT_TOKEN
BOT_NAME=hello_bot
```

---

## 🧩 Code Overview

### Main logic — `bot.py`

- Loads `.env`  
- Initializes logging  
- Reads bot token  
- Builds Telegram application  
- Registers the `/start` and `/ping` handlers  
- Starts polling

Example snippet:

```python
def main() -> None:
    setup_logging()
    load_env(ENV_PATH)

    token = get_env("TELEGRAM_BOT_TOKEN")
    bot_name = get_env("BOT_NAME", "hello_bot")

    app = ApplicationBuilder().token(token).build()

    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("ping", cmd_ping))

    app.run_polling()
```

---

## ▶️ Run Locally

From project root:

```bash
python apps/hello_bot/bot.py
```

---

## 🟢 Run as a systemd Service (Linux)

1. Create a service file:

```
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

4. View logs:

```bash
sudo journalctl -u hello_bot -f
```

---

## 📌 Commands

| Command | Description |
|---------|------------|
| `/start` | Friendly welcome message |
| `/ping`  | Health‑check test |

---

## 🔁 Future Enhancements

- Inline menu
- Callback buttons
- Custom reply keyboards
- API integrations
- Error monitoring & notifications

---

## ✨ Developer

Created by **TamerOnLine** — 2025
