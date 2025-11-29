import os
import logging
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv("PI_GAME01_BOT_TOKEN")  # حط التوكن في هذا المتغير
GAME_SHORT_NAME = "pi_game01"                 # نفس الـ short name في BotFather
GAME_URL = "https://mystrotamer.com/pi_game01/index.html"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Welcome to Pi Game! Use /play to start the game.")

async def play(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_game(GAME_SHORT_NAME)

async def game_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer(url=GAME_URL)

def main():
    if not BOT_TOKEN:
        logger.error("PI_GAME01_BOT_TOKEN is not set")
        return

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("play", play))
    app.add_handler(CallbackQueryHandler(game_callback, pattern=f"^{GAME_SHORT_NAME}$"))

    app.run_polling()

if __name__ == "__main__":
    main()
