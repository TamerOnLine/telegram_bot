from __future__ import annotations

import sys
from pathlib import Path

from dotenv import load_dotenv

# مسار مجلد هذا التطبيق: telegram/apps/gmail
BASE_DIR = Path(__file__).resolve().parent

# جذر المشروع: telegram/
PROJECT_ROOT = BASE_DIR.parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# تحميل .env الخاص ببوت جيميل
ENV_PATH = BASE_DIR / ".env"
load_dotenv(ENV_PATH)

from src.bots.gmail_bot.app import run_bot  # noqa: E402


if __name__ == "__main__":
    print(f"🤖 Gmail Bot starting with env: {ENV_PATH}")
    run_bot(ENV_PATH)
