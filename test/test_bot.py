import os
import requests
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

if not TOKEN:
    print("TELEGRAM_BOT_TOKEN not found in .env file.")
    exit()

url = f"https://api.telegram.org/bot{TOKEN}/getMe"

try:
    response = requests.get(url, timeout=10)
    data = response.json()

    if data.get("ok"):
        print("Bot is running successfully.")
        print(f"Bot Name       : {data['result']['first_name']}")
        print(f"Bot ID         : {data['result']['id']}")
        print(f"Username       : @{data['result']['username']}")
    else:
        print("Failed to verify the bot!")
        print("Telegram Error:", data)

except Exception as error:
    print("Error connecting to Telegram:", error)
