from __future__ import annotations

import sys
from pathlib import Path

# هذا الملف: src/telegram/bot.py
BASE_FILE = Path(__file__).resolve()

# جذر المشروع: telegram/
PROJECT_ROOT = BASE_FILE.parents[2]

# نضيف جذر المشروع لمسار بايثون حتى نقدر نستورد src.telegram.*
sys.path.insert(0, str(PROJECT_ROOT))

from src.telegram.chat_bot import run_bot  # type: ignore

# 📌 ملف .env الأساسي للبوت (نعتبره في apps/app01/.env)
BOT_APP_NAME = "app01"
ENV_PATH = PROJECT_ROOT / "apps" / BOT_APP_NAME / ".env"


if __name__ == "__main__":
    print(f"🚀 Starting central Telegram bot with env: {ENV_PATH}")
    run_bot(ENV_PATH)
