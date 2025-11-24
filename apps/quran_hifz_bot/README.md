
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
