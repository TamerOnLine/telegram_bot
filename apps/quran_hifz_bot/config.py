from __future__ import annotations

import logging
import os
from pathlib import Path

from dotenv import load_dotenv

# =========================
# إعدادات عامة
# =========================

BASE_DIR = Path(__file__).resolve().parent
ENV_PATH = BASE_DIR / ".env"
load_dotenv(ENV_PATH)

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
BOT_NAME = os.getenv("BOT_NAME", "Quran Hifz Coach")
GOALS_FILE = BASE_DIR / os.getenv("GOALS_FILE", "goals.json")

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

if not BOT_TOKEN:
    raise SystemExit("TELEGRAM_BOT_TOKEN is missing in .env")
