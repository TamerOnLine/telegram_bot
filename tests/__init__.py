import sys
from pathlib import Path

# جذر المشروع: .../telegram
ROOT = Path(__file__).resolve().parents[1]

# مجلد src: .../telegram/src
SRC_DIR = ROOT / "src"

# نضيف src إلى sys.path مرة واحدة فقط
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))
