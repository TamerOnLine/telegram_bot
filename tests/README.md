# telegram_bot – Local & Server Run Guide

This README provides **all run commands** for the `telegram_bot` multi‑bot suite:

- Running bots locally (Windows / Linux)
- Running the Streamlit Dashboard
- Running bots on a Linux server using `systemd`
- Log monitoring commands

---

## 1. Requirements

- Python 3.11+
- Git
- Package manager:
  - `uv` (recommended) or `pip`
- On server: Linux with `systemd` + `journalctl`

Project structure:

```
telegram_bot/
  apps/
    hello_bot/
    quran_hifz_bot/
    shop_bot/
    search_bot/
    dashboard/
  core/
  pyproject.toml
```

---

## 2. Setup Environment (Local)

### 2.1 Clone the project

```bash
git clone https://github.com/TamerOnLine/telegram_bot.git
cd telegram_bot
```

### 2.2 Create & activate virtual environment

#### Using uv (recommended)

```bash
uv sync
```

#### Or using venv + pip

```bash
python -m venv .venv

# Linux / macOS
source .venv/bin/activate

# Windows (PowerShell)
.\.venv\Scripts\Activate.ps1

pip install -e .
```

---

## 3. Bot Environment Files (.env)

Each bot folder under `apps/` must contain its own `.env`:

Example (`apps/hello_bot/.env`):

```
TELEGRAM_BOT_TOKEN=123456:ABCDEF...
BOT_NAME=Hello Bot
BOT_USERNAME=MyHelloBot
BOT_DESCRIPTION=A sample greeting bot
SERVICE_NAME=tg_bot@hello_bot.service
```

Repeat for every bot you add.

---

## 4. Run Bots Locally (Without systemd)

Run from project root after activating `.venv`.

### hello_bot

```bash
python -m apps.hello_bot.bot
```

### quran_hifz_bot

```bash
python -m apps.quran_hifz_bot.bot
```

### shop_bot

```bash
python -m apps.shop_bot.bot
```

### search_bot

```bash
python -m apps.search_bot.bot
```

Run each bot in a separate terminal if needed.

---

## 5. Run Streamlit Dashboard (Local)

The dashboard is located in `apps/dashboard/streamlit_app.py`.

```bash
streamlit run apps/dashboard/streamlit_app.py
```

Access it at:

```
http://localhost:8501
```

The dashboard allows you to:

- Select and manage any bot
- Send test messages
- Manage systemd services (if configured)
- Fetch Chat IDs
- View & clean bot database records

---

## 6. Run on Server (Linux)

### 6.1 Upload project to server

```bash
scp -r telegram_bot user@server:/home/user/
```

On the server:

```bash
cd /home/user/telegram_bot
```

### 6.2 Create virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

---

## 7. Create systemd Service Template

Create:

```bash
sudo nano /etc/systemd/system/tg_bot@.service
```

Add:

```
[Unit]
Description=Telegram Bot (%i)
After=network-online.target

[Service]
Type=simple
User=YOUR_USER
WorkingDirectory=/home/YOUR_USER/telegram_bot
Environment="PYTHONUNBUFFERED=1"
ExecStart=/home/YOUR_USER/telegram_bot/.venv/bin/python -m apps.%i.bot
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
```

Replace `YOUR_USER` with your server username.

Now each bot can be managed as:

```
tg_bot@hello_bot.service
tg_bot@shop_bot.service
tg_bot@quran_hifz_bot.service
```

---

## 8. systemd Commands (Server)

### Enable & start a bot

```bash
sudo systemctl enable --now tg_bot@hello_bot.service
```

### Stop / start / restart

```bash
sudo systemctl stop tg_bot@hello_bot.service
sudo systemctl start tg_bot@hello_bot.service
sudo systemctl restart tg_bot@hello_bot.service
```

### Service status

```bash
sudo systemctl status tg_bot@hello_bot.service
```

### View logs

```bash
sudo journalctl -u tg_bot@hello_bot.service -n 50
sudo journalctl -u tg_bot@hello_bot.service -f
```

---

## 9. Run Streamlit Dashboard on Server

```bash
cd /home/YOUR_USER/telegram_bot
source .venv/bin/activate
streamlit run apps/dashboard/streamlit_app.py --server.port=8501 --server.address=0.0.0.0
```

Open:

```
http://SERVER_IP:8501
```

---

## 10. Quick Command Cheat Sheet

### Local

```bash
# Activate venv
source .venv/bin/activate
.\.venv\Scripts\Activate.ps1

# Run bots
python -m apps.hello_bot.bot
python -m apps.quran_hifz_bot.bot
python -m apps.shop_bot.bot
python -m apps.search_bot.bot

# Run dashboard
streamlit run apps/dashboard/streamlit_app.py
```

### Server (systemd)

```bash
sudo systemctl start tg_bot@hello_bot.service
sudo systemctl restart tg_bot@hello_bot.service
sudo journalctl -u tg_bot@hello_bot.service -f
```

---

## 11. Project Link

```
https://github.com/TamerOnLine/telegram_bot
```
