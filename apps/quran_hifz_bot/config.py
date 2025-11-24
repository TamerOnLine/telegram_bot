from __future__ import annotations
import os
from pathlib import Path
from dotenv import load_dotenv
import logging

BASE_DIR = Path(__file__).resolve().parent
DATA_FILE = BASE_DIR / "data.json"

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# load .env
env_path = BASE_DIR / ".env"
if env_path.exists():
    load_dotenv(env_path)
else:
    logger.warning("No .env file found at %s", env_path)

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
BOT_NAME = os.getenv("BOT_NAME", "quran_hifz_bot")

if not BOT_TOKEN:
    raise SystemExit("TELEGRAM_BOT_TOKEN is missing in .env")
