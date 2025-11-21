import os
import unittest
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")


@unittest.skipIf(not TOKEN, "TELEGRAM_BOT_TOKEN not set; skipping bot tests.")
class TestBot(unittest.TestCase):
    def test_basic_sanity(self) -> None:
        self.assertIsInstance(TOKEN, str)
