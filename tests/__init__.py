import sys
from pathlib import Path

# Project root: .../telegram
ROOT = Path(__file__).resolve().parents[1]

# Source directory: .../telegram/src
SRC_DIR = ROOT / "src"

# Add src to sys.path only if not already present
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))
