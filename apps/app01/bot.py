from pathlib import Path
import sys

BASE_DIR = Path(__file__).resolve().parent
ENV_PATH = BASE_DIR / ".env"

PROJECT_ROOT = BASE_DIR.parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.telegram.chat_bot import run_bot  # يستخدم المنطق المشترك

if __name__ == "__main__":
    print(f"🤖 PDF Bot starting with env: {ENV_PATH}")
    run_bot(ENV_PATH)
