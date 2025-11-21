import sys
from pathlib import Path
import os
import unittest
from dotenv import load_dotenv

# 🔹 اجعل جذر المشروع على sys.path
ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT / "src"
sys.path.insert(0, str(SRC_DIR))

# 🔹 حمّل .env من مجلد الاختبار نفسه
ENV_PATH = Path(__file__).resolve().parent / ".env"
load_dotenv(ENV_PATH)

# 🔹 استيراد دالة واحدة على الأقل موجودة داخل telegram_utils
from telegram.telegram_utils import send_text  # ضع دالة صحيحة هنا

# 🔹 IDs تأتي من ملف .env
ME_ID = os.getenv("TELEGRAM_ME_ID", "")
CHANNEL_ID = os.getenv("TELEGRAM_CHANNEL_ID", "")
GROUP_ID = os.getenv("TELEGRAM_GROUP_ID", "")

# لو أي ID ناقص → نتخطّى الاختبار
MISSING_IDS = not (ME_ID and CHANNEL_ID and GROUP_ID)


@unittest.skipIf(MISSING_IDS, "Telegram IDs not configured; skipping pro feature tests.")
class TestProFeatures(unittest.TestCase):
    def test_ids_are_strings(self) -> None:
        self.assertIsInstance(ME_ID, str)
        self.assertIsInstance(CHANNEL_ID, str)
        self.assertIsInstance(GROUP_ID, str)

    def test_send_text_exists(self):
        # هذا فقط للتأكد أن send_text قابل للاستدعاء
        self.assertTrue(callable(send_text))
