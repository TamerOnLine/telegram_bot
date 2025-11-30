import logging
import os

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)

# ─────────────────────────────
# إعدادات عامة
# ─────────────────────────────
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GAME_SHORT_NAME = "pi_game01x"     # يجب أن يطابق BotFather
GAME_URL = "https://mystrotamer.com/pi_game01/index.html"

if not TOKEN:
    raise RuntimeError("TELEGRAM_BOT_TOKEN is not set")


# ─────────────────────────────
# الأوامر
# ─────────────────────────────
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Welcome to Pi Game! Use /play to start the game.")


async def play(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """يرسل رسالة Game داخل Telegram"""
    await context.bot.send_game(
        chat_id=update.effective_chat.id,
        game_short_name=GAME_SHORT_NAME,
    )


# ─────────────────────────────
# CallbackQuery – زر Play
# ─────────────────────────────
async def game_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query

    # من أجل الأمان
    if not query or not query.game_short_name:
        await query.answer("Invalid game.")
        return

    # التأكد أن اللعبة صحيحة
    if query.game_short_name != GAME_SHORT_NAME:
        await query.answer("Unknown game.", show_alert=True)
        return

    # هنا يتم فتح اللعبة – هذا أهم شيء
    await query.answer(url=GAME_URL)


# ─────────────────────────────
# نقطة تشغيل البوت
# ─────────────────────────────
def main():
    logger.info("Starting Pi Game bot...")

    app = Application.builder().token(TOKEN).build()

    # Commands
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("play", play))

    # Callback for game button
    app.add_handler(CallbackQueryHandler(game_callback))

    app.run_polling()


if __name__ == "__main__":
    main()
