import os
import requests
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def send_msg(text: str):
    """
    Send a text message using a Telegram Bot.

    Args:
        text (str): The message text to be sent.

    Returns:
        None
    """
    requests.post(
        f"https://api.telegram.org/bot{TOKEN}/sendMessage",
        json={"chat_id": CHAT_ID, "text": text}
    )

# Test message
send_msg("The bot is working successfully!")
