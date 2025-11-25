from __future__ import annotations

import logging
from pathlib import Path

from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)

from core.env import load_env, get_env
from core.logging import setup_logging
from core.db import upsert_chat     # ←⭐ إضافة مهمة

from config import BOT_NAME, ADMIN_CHAT_ID
from handlers import (
    cmd_start,
    cmd_products,
    cmd_cart,
    cmd_clear,
    cmd_checkout,
    product_details,
    add_to_cart,
    back_to_products,
)
from db import init_db


BASE_DIR = Path(__file__).resolve().parent
ENV_PATH = BASE_DIR / ".env"


async def global_logger(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    هذا الهاندلر يتم استدعاؤه قبل أي رد من البوت،
    ويقوم بتسجيل الشات في قاعدة البيانات.
    """
    upsert_chat(update.effective_chat, update.effective_user)


def main() -> None:
    setup_logging()
    load_env(ENV_PATH)

    token = get_env("TELEGRAM_BOT_TOKEN")

    logging.getLogger(__name__).info("Starting bot: %s", BOT_NAME)

    app = ApplicationBuilder().token(token).build()

    # === تسجيل الشات لكل أنواع الرسائل ===
    app.add_handler(MessageHandler(filters.ALL, global_logger), group=0)

    # === أوامر البوت ===
    app.add_handler(CommandHandler("start", cmd_start), group=1)
    app.add_handler(CommandHandler("products", cmd_products), group=1)
    app.add_handler(CommandHandler("cart", cmd_cart), group=1)
    app.add_handler(CommandHandler("clear", cmd_clear), group=1)
    app.add_handler(CommandHandler("checkout", cmd_checkout), group=1)

    # === أزرار inline ===
    app.add_handler(CallbackQueryHandler(product_details, pattern=r"^product_"), group=2)
    app.add_handler(CallbackQueryHandler(add_to_cart, pattern=r"^add_"), group=2)
    app.add_handler(CallbackQueryHandler(back_to_products, pattern=r"^back$"), group=2)

    logging.getLogger(__name__).info("Bot is polling...")
    app.run_polling()


if __name__ == "__main__":
    init_db()
    main()
   