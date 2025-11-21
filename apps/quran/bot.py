from pathlib import Path
import sys

BASE_DIR = Path(__file__).resolve().parent
ENV_PATH = BASE_DIR / ".env"

PROJECT_ROOT = BASE_DIR.parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.bots.quran_bot.app import run_bot


if __name__ == "__main__":
    print(f"🤖 Quran Bot starting with env: {ENV_PATH}")
    run_bot(ENV_PATH)
