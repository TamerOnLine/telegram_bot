from __future__ import annotations

import logging
import os
from pathlib import Path

from dotenv import load_dotenv

# =========================
# General Configuration
# =========================

BASE_DIR = Path(__file__).resolve().parent
ENV_PATH = BASE_DIR / ".env"
load_dotenv(ENV_PATH)

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
BOT_NAME = os.getenv("BOT_NAME", "Quran Hifz Coach")
GOALS_FILE = BASE_DIR / os.getenv("GOALS_FILE", "goals.json")

# Logging Configuration
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,  # Avoid using DEBUG in production
)
logger = logging.getLogger(__name__)

# Suppress token leakage in request logs
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("telegram.vendor.ptb_urllib3.urllib3").setLevel(logging.WARNING)

if not BOT_TOKEN:
    raise SystemExit("TELEGRAM_BOT_TOKEN is missing in .env")