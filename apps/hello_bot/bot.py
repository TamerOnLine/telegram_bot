from __future__ import annotations

import logging
from pathlib import Path

from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
)

from core.env import load_env, get_env
from core.logging import setup_logging


BASE_DIR = Path(__file__).resolve().parent
ENV_PATH = BASE_DIR / ".env"


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    /start command
    """
    user = update.effective_user
    name = user.first_name if user else "there"

    text = (
        f"👋 Hello *{name}*!\n\n"
        "This is a simple test bot from your new multi-bot project.\n"
        "You can duplicate this folder to create new bots."
    )

    await update.message.reply_text(text, parse_mode="Markdown")


async def cmd_ping(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    /ping command
    """
    await update.message.reply_text("🏓 Pong!")


def main() -> None:
    # 1) Setup logging
    setup_logging()

    # 2) Load .env for this bot
    load_env(ENV_PATH)

    # 3) Read token
    token = get_env("TELEGRAM_BOT_TOKEN")
    bot_name = get_env("BOT_NAME", "hello_bot")

    logging.getLogger(__name__).info("Starting bot: %s", bot_name)

    # 4) Build application
    app = (
        ApplicationBuilder()
        .token(token)
        .build()
    )

    # 5) Register handlers
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("ping", cmd_ping))

    # 6) Run bot
    logging.getLogger(__name__).info("Bot is polling...")
    app.run_polling()


if __name__ == "__main__":
    main()
