# Shop Bot — Telegram Mini Store

A simple and elegant mini‑store Telegram bot built inside the **telegram_bot multi‑bot architecture**.  
This bot allows users to browse products, view details, add items to a cart, calculate totals, and submit an order to the admin.

---

## ✨ Features

- Product list with inline buttons  
- Product details page  
- Add‑to‑cart system  
- Shopping cart with automatic total calculation  
- Checkout system that sends order details to `ADMIN_CHAT_ID`  
- Works entirely with inline buttons  
- Fully async using python‑telegram‑bot v22+

---

## 📁 Folder Structure

```
apps/shop_bot/
│
├── bot.py          # Main bot entry point
├── config.py       # Environment, logging, and settings
├── handlers.py     # Commands and callback handlers
└── products.py     # Product catalog
```

---

## 🔐 .env Configuration

Create the file:

```
apps/shop_bot/.env
```

Example:

```
TELEGRAM_BOT_TOKEN=YOUR_TOKEN
BOT_NAME=shop_bot
ADMIN_CHAT_ID=123456789
CURRENCY=€
```

---

## 🤖 Commands

| Command     | Description                |
|-------------|----------------------------|
| `/start`    | Welcome message            |
| `/products` | Show product list          |
| `/cart`     | Show shopping cart         |
| `/checkout` | Send order to admin        |
| `/clear`    | Empty the cart             |

---

## 🧩 How It Works

### 1. Product List
Displayed using `InlineKeyboardMarkup`, each button shows:
- Name  
- Price  
- A callback that opens the details page  

### 2. Product Details
Shows product name, description, price, and:
- **Add to cart**
- **Back to products**

### 3. Cart System
Stored inside `context.user_data["cart"]`

### 4. Checkout
Sends a formatted order to your admin Telegram ID.

---

## ▶️ Run Locally

From the project root:

```bash
python apps/shop_bot/bot.py
```

---

## 🟢 Run as a systemd Service (Linux)

Create:

```
sudo nano /etc/systemd/system/shop_bot.service
```

Contents:

```
[Unit]
Description=Shop Telegram Bot
After=network.target

[Service]
Type=simple
User=tamer
WorkingDirectory=/home/tamer/telegram_bot
ExecStart=/home/tamer/telegram_bot/.venv/bin/python /home/tamer/telegram_bot/apps/shop_bot/bot.py
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

Enable:

```bash
sudo systemctl daemon-reload
sudo systemctl enable shop_bot
sudo systemctl start shop_bot
```

Logs:

```bash
sudo journalctl -u shop_bot -f
```

---

## 📦 Products Example

```
📱 Mobile Case — 9.99
🎧 Headphones — 19.5
🔌 USB Charger — 7.0
```

Add new products easily in `products.py`.

---

## 🔁 Future Enhancements

- Product images  
- Quantity selector  
- Save orders to file or PostgreSQL  
- API-based inventory  
- Payment gateway integration  

---

## ✨ Developer

Created by **TamerOnLine** — 2025  
Part of **Telegram Bot Suite — Multi‑Bot Architecture**


---

## ⚙️ Unified Systemd Template — Run Shop Bot (and Other Bots) Easily

Instead of creating a separate `.service` file for every bot (e.g. `shop_bot.service`, `hello_bot.service`, `quran_hifz_bot.service`, `search_bot.service`), you can use a **single systemd template unit** and run all bots as instances of it.

The template unit is named:

```bash
tg_bot@.service
```

Each bot runs as an instance:

```bash
tg_bot@shop_bot
tg_bot@hello_bot
tg_bot@quran_hifz_bot
tg_bot@search_bot
```

> Requirement: each bot must live in `apps/<bot_name>/bot.py` inside the main project folder.

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

### ▶️ Start Shop Bot Using the Template

Assuming the bot entry point is:

```text
/home/tamer/telegram_bot/apps/shop_bot/bot.py
```

you can enable and start it as a service with:

```bash
sudo systemctl enable --now tg_bot@shop_bot
```

You can start other bots in exactly the same way:

```bash
sudo systemctl enable --now tg_bot@hello_bot
sudo systemctl enable --now tg_bot@quran_hifz_bot
sudo systemctl enable --now tg_bot@search_bot
```

---

### 🔁 Restart After Code Updates

Whenever you update the Shop Bot code:

```bash
sudo systemctl restart tg_bot@shop_bot
```

---

### 📜 View Logs

To follow logs in real time:

```bash
journalctl -u tg_bot@shop_bot -f
```

---

### 🧼 Disable or Stop the Bot

```bash
sudo systemctl stop tg_bot@shop_bot
sudo systemctl disable tg_bot@shop_bot
```

---

### 🎉 Benefits of the Template System

- Run **unlimited bots** from a single template unit  
- No need to maintain multiple `.service` files  
- Cleaner and more scalable server configuration  
- Bots restart automatically on crash  
- Bots auto-start on server reboot  
- Each bot is still isolated and controlled independently  

---
