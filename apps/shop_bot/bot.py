from __future__ import annotations

import logging
from pathlib import Path

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

from config import BOT_NAME, ADMIN_CHAT_ID  # ADMIN_CHAT_ID غير مستخدم هنا لكن لا بأس
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


def main() -> None:
    setup_logging()
    load_env(ENV_PATH)

    token = get_env("TELEGRAM_BOT_TOKEN")

    logging.getLogger(__name__).info("Starting bot: %s", BOT_NAME)

    app = (
        ApplicationBuilder()
        .token(token)
        .build()
    )

    # === أوامر البوت ===
    app.add_handler(CommandHandler("start",     cmd_start),     group=1)
    app.add_handler(CommandHandler("products",  cmd_products),  group=1)
    app.add_handler(CommandHandler("cart",      cmd_cart),      group=1)
    app.add_handler(CommandHandler("clear",     cmd_clear),     group=1)
    app.add_handler(CommandHandler("checkout",  cmd_checkout),  group=1)

    # === أزرار inline ===
    app.add_handler(
        CallbackQueryHandler(product_details, pattern=r"^product_"),
        group=2,
    )
    app.add_handler(
        CallbackQueryHandler(add_to_cart, pattern=r"^add_"),
        group=2,
    )
    app.add_handler(
        CallbackQueryHandler(back_to_products, pattern=r"^back$"),
        group=2,
    )

    logging.getLogger(__name__).info("Bot is polling...")
    app.run_polling()


if __name__ == "__main__":
    init_db()
    main()
