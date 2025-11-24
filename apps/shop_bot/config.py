from __future__ import annotations

import logging
import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
ENV_PATH = BASE_DIR / ".env"

# تحميل ملف البيئة
load_dotenv(ENV_PATH)

# المتغيرات
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
BOT_NAME = os.getenv("BOT_NAME", "shop_bot")
ADMIN_CHAT_ID = os.getenv("ADMIN_CHAT_ID", "")
CURRENCY = os.getenv("CURRENCY", "€")

# اللوجينغ الأساسي
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,   # 👈 لا نستخدم DEBUG
)
logger = logging.getLogger(__name__)

# 👇 إخفاء أي روابط تحتوي التوكن من httpx و urllib3
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("telegram.vendor.ptb_urllib3.urllib3").setLevel(logging.WARNING)

if not BOT_TOKEN:
    raise SystemExit("❌ TELEGRAM_BOT_TOKEN is missing in .env")
