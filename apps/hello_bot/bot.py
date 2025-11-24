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
    Handle the /start command.

    Args:
        update (Update): Incoming update from Telegram.
        context (ContextTypes.DEFAULT_TYPE): Context provided by the handler.

    Returns:
        None
    """
    user = update.effective_user
    name = user.first_name if user else "there"

    text = (
        f"Hello *{name}*!\n\n"
        "This is a simple test bot from your new multi-bot project.\n"
        "You can duplicate this folder to create new bots."
    )

    await update.message.reply_text(text, parse_mode="Markdown")


async def cmd_ping(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle the /ping command.

    Args:
        update (Update): Incoming update from Telegram.
        context (ContextTypes.DEFAULT_TYPE): Context provided by the handler.

    Returns:
        None
    """
    await update.message.reply_text("Pong!")


def main() -> None:
    """
    Main entry point for the Telegram bot.

    Sets up logging, loads environment variables, builds the application,
    registers command handlers, and starts polling.

    Returns:
        None
    """
    setup_logging()
    load_env(ENV_PATH)

    token = get_env("TELEGRAM_BOT_TOKEN")
    bot_name = get_env("BOT_NAME", "hello_bot")

    logging.getLogger(__name__).info("Starting bot: %s", bot_name)

    app = ApplicationBuilder().token(token).build()

    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("ping", cmd_ping))

    logging.getLogger(__name__).info("Bot is polling...")
    app.run_polling()


if __name__ == "__main__":
    main()
