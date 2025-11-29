import logging
import os

from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# ─────────────────────────────
# إعدادات عامة
# ─────────────────────────────
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GAME_SHORT_NAME = "pi_game01"   # لازم يطابق اسم اللعبة في BotFather بالضبط

if not TOKEN:
    raise RuntimeError("TELEGRAM_BOT_TOKEN is not set")


# ─────────────────────────────
# الأوامر
# ─────────────────────────────
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "Welcome to Pi Game! Use /play to start the game."
    )


async def play(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """يرسل رسالة Game حقيقية فيها زر Play."""
    chat_id = update.effective_chat.id
    await context.bot.send_game(
        chat_id=chat_id,
        game_short_name=GAME_SHORT_NAME,
    )


# ─────────────────────────────
# نقطة بداية البوت
# ─────────────────────────────
def main() -> None:
    logger.info("Starting Pi Game bot...")
    application = Application.builder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("play", play))

    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
