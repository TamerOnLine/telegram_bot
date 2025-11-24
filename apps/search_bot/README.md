
# search_bot — Dynamic Topic Search Bot (English)

`search_bot` is a highly customizable information‑retrieval Telegram bot designed to fetch topic‑focused summaries from Wikipedia.  
It supports Arabic and English detection, dynamic query enrichment, and fully modular configuration.  
This bot is part of the **Telegram Multi‑Bot Suite**, integrating seamlessly with shared environment loaders and logging utilities.

---

## 🚀 Features

- Topic‑aware dynamic search system  
- Wikipedia API integration (free, no API key required)  
- Automatic Arabic/English language detection  
- `/start`, `/help`, `/search` commands  
- Handles normal messages as search queries  
- Lightweight, modular, and production‑ready  
- Runs locally or via systemd using a unified template  

---

## 🛠️ Dynamic Configuration

At the top of `bot.py` (fileciteturn4file0), you can change:

```python
TOPIC_NAME = "Pi Network"
TOPIC_DESCRIPTION = "Specialized bot focused on Pi Network information."
BOT_LANG = "ar"
WIKI_DEFAULT_LANG = "ar"
FORCE_TOPIC_IN_QUERY = True
```

Changing these values converts the bot into **any specialized search bot** (Germany, Crypto, Health, Quranic sciences, etc.).

---

## 📁 Folder Structure

```
apps/search_bot/
│
├── bot.py    # Main bot logic
└── .env      # Bot-specific configuration
```

Example `.env`:

```
TELEGRAM_BOT_TOKEN=YOUR_TELEGRAM_BOT_TOKEN
BOT_NAME=search_bot
```

---

## 🔍 How Wikipedia Search Works

- Detects query language (Arabic vs English)  
- Selects Wikipedia language dynamically  
- Auto‑prepends the configured `TOPIC_NAME`  
- Fetches the first search result  
- Retrieves the page summary  
- Sends a Markdown‑formatted answer with link  

---

## ▶️ Running Locally

```bash
python apps/search_bot/bot.py
```

---

# ⚙️ Unified Systemd Template — Run search_bot Easily

This project uses **one systemd template** to run unlimited bots:

```
tg_bot@.service
```

Each bot runs as a unique instance:

```
tg_bot@search_bot
tg_bot@hello_bot
tg_bot@quran_hifz_bot
tg_bot@shop_bot
```

---

## 🗂️ Template File Location

Create the template file:

```
sudo nano /etc/systemd/system/tg_bot@.service
```

Content:

```ini
[Unit]
Description=Telegram Bot (%i)
After=network.target

[Service]
WorkingDirectory=/home/tamer/telegram_bot
ExecStart=/home/tamer/telegram_bot/.venv/bin/python /home/tamer/telegram_bot/apps/%i/bot.py
Restart=always
RestartSec=3

User=tamer
Environment="PYTHONUNBUFFERED=1"

[Install]
WantedBy=multi-user.target
```

`%i` = bot folder name under `apps/`.

---

## ▶️ Start search_bot

```bash
sudo systemctl enable --now tg_bot@search_bot
```

---

## 🔁 Restart After Update

```bash
sudo systemctl restart tg_bot@search_bot
```

---

## 📜 Logs

```bash
journalctl -u tg_bot@search_bot -f
```

---

## 🧼 Stop / Disable

```bash
sudo systemctl stop tg_bot@search_bot
sudo systemctl disable tg_bot@search_bot
```

---

## 🎉 Highlights

- One template for unlimited bots  
- Automatic restarts on crash  
- Clean separation of bot instances  
- Simple, scalable architecture  

---

## ✨ Author

Created by **TamerOnLine** — 2025  
Part of the **Telegram Multi‑Bot Suite**

