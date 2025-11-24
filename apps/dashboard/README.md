# 📊 Telegram Bot Dashboard  
Streamlit Control Panel for Multi-Bot System

A powerful Streamlit-based dashboard for managing all Telegram bots inside the project.  
It provides a unified control panel where you can send messages, view bot info, manage systemd services, and extract Chat IDs — all from one place.

---

## 🚀 Features

### 🔍 Automatic Bot Discovery
The dashboard scans all directories under `apps/*` and detects bots that contain:
- `bot.py`
- `.env` file
- `TELEGRAM_BOT_TOKEN`

It also loads optional metadata from `.env`:
- `BOT_NAME`
- `BOT_USERNAME`
- `BOT_DESCRIPTION`
- `SERVICE_NAME`

---

### ✉️ Message Sender
Send messages directly from the panel:
- To a single Chat ID
- To multiple Chat IDs (one per line)
- Displays result for each chat with success/error status

---

### 🖥️ systemd Service Management
If the bot’s `.env` contains:

```
SERVICE_NAME=hello_bot.service
```

You can:
- Start the bot service  
- Stop the service  
- Restart the service  
- View status  
- View latest journal logs (configurable line count)

---

### 📌 Chat ID Helper
Two methods:

#### Recommended:
Add a `/id` handler in your bot.

#### Alternative (built-in):
The dashboard can call `getUpdates()` to extract all chat IDs automatically  
(only safe when the bot is NOT running with `run_polling`).

---

## 📁 Folder Structure

```
apps/dashboard/
│
└── streamlit_app.py   # Main dashboard code
```

---

## ▶️ How to Run the Dashboard

From the project root:

```bash
streamlit run apps/dashboard/streamlit_app.py
```

Then open:

```
http://localhost:8501
```

---

## 🛠 Requirements

- python-telegram-bot ≥ 22
- streamlit
- python-dotenv
- requests

---

## ⚙️ How Bot Discovery Works

The function `discover_bots()`:

1. Scans `apps/*`
2. Ensures `bot.py` + `.env` exist
3. Reads `.env` with `dotenv_values`
4. Validates presence of `TELEGRAM_BOT_TOKEN`
5. Loads metadata for each bot

---

## ✉️ Message Sending

Messages are sent via Telegram HTTP API:

```
https://api.telegram.org/bot{TOKEN}/sendMessage
```

---

## 🖥 systemd Integration

Requires:
- Running dashboard on the same server  
- Proper user permissions for `systemctl`

---

## 📌 Chat ID Extraction

Fetches `getUpdates()` and analyzes updates to detect all chats:
- Private chats  
- Groups  
- Channels  

---

## 🧱 Tabs Overview

1. **Overview** — basic bot info  
2. **Send Message** — message tools  
3. **systemd Control** — start/stop/restart/show logs  
4. **Chat ID** — extraction helpers  

---

## ✨ Ideal For

- Servers running multiple Telegram bots  
- Developers needing a 24/7 control panel  
- Managing bots without CLI  
- Centralizing all bot operations into one interface  

---

## © Developer

Created by **TamerOnLine** — 2025
