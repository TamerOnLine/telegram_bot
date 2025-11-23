from __future__ import annotations

import sys
from pathlib import Path

# Path to this file: src/telegram/bot.py
BASE_FILE = Path(__file__).resolve()

# Project root: telegram/
PROJECT_ROOT = BASE_FILE.parents[2]

# Add project root to Python path to enable src.telegram.* imports
sys.path.insert(0, str(PROJECT_ROOT))

from src.telegram.chat_bot import run_bot  # type: ignore

# Main .env file for the bot (assumed to be in apps/app01/.env)
BOT_APP_NAME = "app01"
ENV_PATH = PROJECT_ROOT / "apps" / BOT_APP_NAME / ".env"


if __name__ == "__main__":
    print(f"Starting central Telegram bot with env: {ENV_PATH}")
    run_bot(ENV_PATH)