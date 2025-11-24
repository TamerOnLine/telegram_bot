from __future__ import annotations

import logging
import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
ENV_PATH = BASE_DIR / ".env"

# Load environment variables
load_dotenv(ENV_PATH)

# Environment variables
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
BOT_NAME = os.getenv("BOT_NAME", "shop_bot")
ADMIN_CHAT_ID = os.getenv("ADMIN_CHAT_ID", "")
CURRENCY = os.getenv("CURRENCY", "€")

# Basic logging configuration
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# Suppress sensitive URLs in logs
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("telegram.vendor.ptb_urllib3.urllib3").setLevel(logging.WARNING)

if not BOT_TOKEN:
    raise SystemExit("TELEGRAM_BOT_TOKEN is missing in .env")