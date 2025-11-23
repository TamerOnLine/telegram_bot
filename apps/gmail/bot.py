from __future__ import annotations

import sys
from pathlib import Path

from dotenv import load_dotenv

# Path to this application's directory: telegram/apps/gmail
BASE_DIR = Path(__file__).resolve().parent

# Root directory of the project: telegram/
PROJECT_ROOT = BASE_DIR.parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Load the .env file specific to the Gmail bot
ENV_PATH = BASE_DIR / ".env"
load_dotenv(ENV_PATH)

from src.bots.gmail_bot.app import run_bot  # noqa: E402


if __name__ == "__main__":
    print(f"Gmail Bot starting with env: {ENV_PATH}")
    run_bot(ENV_PATH)