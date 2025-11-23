import sys
from pathlib import Path

# Path to the application directory
BASE_DIR = Path(__file__).resolve().parent
ENV_PATH = BASE_DIR / ".env"

# Project root directory
PROJECT_ROOT = BASE_DIR.parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

# Import the Streamlit panel launcher
from src.telegram.streamlit_panel import run_panel


if __name__ == "__main__":
    run_panel(ENV_PATH)