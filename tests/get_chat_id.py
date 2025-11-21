import os
import requests
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

if not TOKEN:
    print("Token not found. Please add TELEGRAM_BOT_TOKEN to your .env file.")
    raise SystemExit

url = f"https://api.telegram.org/bot{TOKEN}/getUpdates"
resp = requests.get(url, timeout=10).json()

if not resp.get("ok"):
    print("Invalid token or the bot is not connected.")
    print(resp)
    raise SystemExit

updates = resp.get("result", [])

if not updates:
    print("No messages found.")
    print("Please send a message to the bot or channel and rerun the script.")
    raise SystemExit

def extract_chat_from_update(update: dict):
    """
    Attempt to extract the chat object from different types of updates.

    Args:
        update (dict): A single update object from Telegram API.

    Returns:
        dict or None: Extracted chat dictionary or None if not found.
    """
    for key in ("message", "channel_post", "edited_message", "edited_channel_post"):
        if key in update:
            return update[key]["chat"]
    return None

chat = None

# Iterate from the latest to the earliest update to get the most recent valid chat
for upd in reversed(updates):
    chat = extract_chat_from_update(upd)
    if chat:
        break

if not chat:
    print("Could not find a chat in the updates.")
    print("Print the full response if you want to debug.")
    raise SystemExit

print("\n=== CHAT INFO ===")
print(f"CHAT_ID     : {chat['id']}")
print(f"CHAT TYPE   : {chat['type']}")
print(f"CHAT TITLE  : {chat.get('title', '---')}")
print("=================\n")

print("Add the following line to your .env file:")
print(f"TELEGRAM_CHAT_ID={chat['id']}")
