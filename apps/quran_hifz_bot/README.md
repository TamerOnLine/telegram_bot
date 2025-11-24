
# Quran Hifz Coach Bot

An advanced interactive Telegram bot designed to help users memorize the Quran through structured goals, daily portions, and a clean, intuitive conversation flow.

This bot supports memorization planning, tracking, reminders, and a full interactive menu — all using a modular, maintainable file structure.

---

## 📌 Features

- Set personalized Quran memorization goals.
- Choose:
  - Surah name  
  - Starting ayah  
  - Ending ayah  
  - Number of days for completion
- Automatically calculate:
  - Total ayahs  
  - Daily portion (per-day ayahs)
- View today's required ayahs.
- View full current goal at any time.
- Inline-button controlled menu.
- Persistent storage using `goals.json`.
- Fully modular handlers, models, and storage system.

---

## 📁 Project Structure

```
apps/quran_hifz_bot/
│
├── bot.py          # Main entry point
├── config.py       # Environment & logging config
├── handlers.py     # All bot conversations & command handlers
├── models.py       # HifzGoal dataclass + daily calculation logic
├── storage.py      # Save/load goals from JSON
├── helpers.py      # (empty for future tools)
├── README.md       # Local bot README
└── .env            # Bot-specific environment variables
```

---

## ⚙️ Requirements

- Python 3.12+
- python-telegram-bot >= 22.5
- python-dotenv

Install dependencies:

```bash
pip install python-telegram-bot==22.5 python-dotenv
```

---

## 🔐 .env Configuration

Your bot must have its own `.env` file located in:

```
apps/quran_hifz_bot/.env
```

Example:

```
TELEGRAM_BOT_TOKEN=YOUR_TELEGRAM_BOT_TOKEN
BOT_NAME=quran_hifz_bot
GOALS_FILE=goals.json
```

---

## 🚀 How It Works

### Step 1 → `/set_goal`
The bot asks:
1. Surah name  
2. First ayah  
3. Last ayah  
4. Number of days  

Then it calculates total ayahs, ayahs per day, and displays a confirmation.

---

### Step 2 → `/today`
Calculates the portion of ayahs the user must memorize today.

---

### Step 3 → `/my_goal`
Displays the full current memorization goal.

---

## ▶️ Run the Bot

```bash
python apps/quran_hifz_bot/bot.py
```

---

## 🧩 Code Overview

### `bot.py`
Initializes bot, loads handlers, and starts polling.

### `handlers.py`
Contains conversation logic, commands, and inline menus.

### `models.py`
Defines `HifzGoal` dataclass and daily ayah calculation.

### `storage.py`
Handles saving and loading user goals.

---

## 🔁 Future Enhancements

- Teacher dashboard  
- Weekly/monthly progress reports  
- Audio memorization review  
- Streamlit dashboard  
- PostgreSQL backend  
- Docker support  

---

## ✨ Developer

Built by **TamerOnLine** – 2025


---

## ⚙️ Unified Systemd Template — Run Quran Hifz Bot (and Other Bots) Easily

To simplify running the **Quran Hifz Coach Bot** (and any other bot inside this project) as a background service, you can use a single systemd **template unit** instead of creating a separate `.service` file for each bot.

Instead of:

- `quran_hifz_bot.service`  
- `hello_bot.service`  
- `shop_bot.service`  
- `search_bot.service`  

you use one template:

```bash
tg_bot@.service
```

Each bot runs as an *instance* of this template:

```bash
tg_bot@quran_hifz_bot
tg_bot@hello_bot
tg_bot@shop_bot
tg_bot@search_bot
```

> The only requirement: each bot must live in `apps/<bot_name>/bot.py`.

---

### 🗂️ Template File Location

Create the template file:

```bash
sudo nano /etc/systemd/system/tg_bot@.service
```

Add:

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

`%i` is automatically replaced by systemd with the bot folder name under `apps/`.

---

### ▶️ Start Quran Hifz Bot Using the Template

From now on, instead of a dedicated `quran_hifz_bot.service`, you simply run:

```bash
sudo systemctl enable --now tg_bot@quran_hifz_bot
```

This assumes the bot entry point is:

```text
/home/tamer/telegram_bot/apps/quran_hifz_bot/bot.py
```

You can start other bots in the same way:

```bash
sudo systemctl enable --now tg_bot@hello_bot
sudo systemctl enable --now tg_bot@shop_bot
sudo systemctl enable --now tg_bot@search_bot
```

---

### 🔁 Restart After Code Updates

Whenever you update the Quran Hifz bot code:

```bash
sudo systemctl restart tg_bot@quran_hifz_bot
```

---

### 📜 View Logs

To follow logs in real time:

```bash
journalctl -u tg_bot@quran_hifz_bot -f
```

---

### 🧼 Disable or Stop the Bot

```bash
sudo systemctl stop tg_bot@quran_hifz_bot
sudo systemctl disable tg_bot@quran_hifz_bot
```

---

### 🎉 Benefits of This Template System

- Run **unlimited bots** using a single systemd unit.  
- No need for multiple `.service` files per bot.  
- Cleaner, scalable server configuration.  
- Bots restart automatically on crash.  
- Bots auto-start on server reboot.  
- Each bot remains isolated and independently controllable.

---
