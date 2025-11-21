# Telegram Multi-Bot Framework (Single-Bot Example)

This project provides a clean, scalable framework for building multiple Telegram bots,  
all sharing the same backend logic, same database, and same Streamlit control panel.

This README describes the framework using **one default bot only** to keep things simple.  
You can later duplicate this bot to create additional bots (e.g., `quran`, `gmail`, etc.).

---

## 🚀 Features

- Unified backend for all bots  
- Shared SQLite database (`telegram_data.db`)  
- Automatic user/message logging based on `BOT_PROFILE`  
- Streamlit control panel displaying:
  - Bot status
  - Send text/media
  - Alerts
  - Scheduled messages
  - **Users who contacted the current bot only**
- Easy replication to create unlimited Telegram bots

---

## 📦 Project Structure (Single Default Bot Example)

```
telegram/
│
├── src/
│   ├── telegram/
│   │   ├── bot.py
│   │   ├── chat_bot.py
│   │   ├── db.py
│   │   ├── streamlit_panel.py
│   │   ├── telegram_fetch.py
│   │   ├── telegram_utils.py
│   │   └── panel/
│   │       ├── environment.py
│   │       ├── chat_bot.py
│   │       ├── scheduler.py
│   │       ├── telegram_fetch.py
│   │       ├── ui_layout.py
│   │       └── ui/
│   │           ├── layout.py
│   │           ├── sidebar.py
│   │           ├── tab_alert.py
│   │           ├── tab_info.py
│   │           ├── tab_media.py
│   │           ├── tab_schedule.py
│   │           ├── tab_text.py
│   │           └── tab_users.py
│   │
│   └── bots/
│       └── default_bot/
│           └── app.py
│
├── apps/
│   └── default_bot/
│       ├── .env
│       ├── bot.py
│       └── streamlit_app.py
│
└── telegram_data.db
```

---

## ⚙️ Environment Variables (`.env`)

Each bot folder under `apps/...` contains its own `.env`:

```
TELEGRAM_BOT_TOKEN=123456:ABCDEF...
BOT_PROFILE=default_bot
```

---

## ▶️ Running the Bot

```
python apps/default_bot/bot.py
```

---

## 🖥️ Running the Control Panel

```
streamlit run apps/default_bot/streamlit_app.py
```

---

## 📌 Adding Another Bot

Duplicate the folder:

```
apps/default_bot → apps/quran
```

Then update `.env`:

```
BOT_PROFILE=quran
TELEGRAM_BOT_TOKEN=YOUR_NEW_TOKEN
```

---

## 🏁 License  
MIT License