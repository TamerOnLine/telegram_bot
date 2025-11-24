
# Telegram Bot Systemd Template — Professional README

This document explains how to use a single systemd template service to manage and run multiple Telegram bots inside one project. 
The template-based system ensures scalability, clean deployment, easy maintenance, and automatic startup on reboot.

---

## 📌 Overview

Instead of creating a separate `.service` file for each bot, we use a systemd template unit named:

```
tg_bot@.service
```

Each bot runs as an instance of this template:

```
tg_bot@hello_bot
tg_bot@quran_hifz_bot
tg_bot@search_bot
```

This reduces duplication and makes bot deployment extremely efficient.

---

## 📁 Project Folder Structure

Each bot lives inside its own folder under the `apps/` directory:

```
telegram_bot/
 ├── apps/
 │    ├── hello_bot/
 │    │      ├── bot.py
 │    │      └── .env
 │    ├── quran_hifz_bot/
 │    │      ├── bot.py
 │    │      └── .env
 │    ├── shop_bot/
 │    │      ├── bot.py
 │    │      └── .env
 │    └── search_bot/
 │           ├── bot.py
 │           └── .env
 ├── core/
 ├── .venv/
 └── ...
```

Each bot requires:
- `bot.py` — The bot's main script  
- `.env` — Token and bot configuration  

---

## ⚙️ Systemd Template File (`tg_bot@.service`)

Place the template file in:

```
/etc/systemd/system/tg_bot@.service
```

Content:

```
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

`%i` is replaced automatically by systemd with the bot folder name.

---

## ▶️ Starting a Bot

Start and enable a bot named `hello_bot`:

```
sudo systemctl enable --now tg_bot@hello_bot
```

Start other bots the same way:

```
sudo systemctl enable --now tg_bot@quran_hifz_bot
sudo systemctl enable --now tg_bot@shop_bot
sudo systemctl enable --now tg_bot@search_bot
```

---

## 🔁 Restart After Updating Code

```
sudo systemctl restart tg_bot@hello_bot
```

---

## 👁️ Check Bot Status

```
sudo systemctl status tg_bot@hello_bot
```

---

## 📜 View Logs (Real-Time)

```
journalctl -u tg_bot@hello_bot -f
```

---

## 🧼 Stop or Disable a Bot

Stop a bot:

```
sudo systemctl stop tg_bot@hello_bot
```

Disable autostart:

```
sudo systemctl disable tg_bot@hello_bot
```

---

## 🎉 Benefits of This Template System

- Run unlimited bots in one project  
- No need for multiple .service files  
- Clean and scalable architecture  
- Bots run independently  
- Automatic restart on crash  
- Auto-launch after system reboot  
- Perfect for large multi-bot architectures  

---

## 💡 Notes

Ensure that the virtual environment path:

```
/home/tamer/telegram_bot/.venv/bin/python
```

matches your actual project setup.

---

End of Document
