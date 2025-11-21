import sys
from pathlib import Path

# مسار مجلد التطبيق: telegram/apps/app01
BASE_DIR = Path(__file__).resolve().parent
ENV_PATH = BASE_DIR / ".env"

# جذر المشروع: telegram/
PROJECT_ROOT = BASE_DIR.parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

# استيراد اللوحة المركزية من src/telegram/streamlit_panel.py
from src.telegram.streamlit_panel import run_panel


if __name__ == "__main__":
    run_panel(ENV_PATH)
