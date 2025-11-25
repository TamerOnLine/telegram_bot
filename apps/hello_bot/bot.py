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
from core.db import upsert_chat


BASE_DIR = Path(__file__).resolve().parent
ENV_PATH = BASE_DIR / ".env"


def save_chat_from_update(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    حفظ معلومات المحادثة في جدول bot_chats لكل مرة يتفاعل فيها المستخدم مع البوت.
    """
    chat = update.effective_chat
    if chat is None:
        return

    # اسم البوت كما يظهر في لوحة التحكم / قاعدة البيانات
    bot_name = context.bot_data.get("BOT_NAME", "hello_bot")

    # اختيار عنوان مناسب للمحادثة (جروب / قناة / مستخدم)
    if chat.title:
        title = chat.title
    else:
        full_name = f"{chat.first_name or ''} {chat.last_name or ''}".strip()
        title = full_name or (chat.username or "") or "—"

    upsert_chat(
        bot_name=bot_name,
        chat_id=chat.id,
        chat_type=chat.type,
        title=title,
        username=chat.username,
    )


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle the /start command.
    """
    # 🔹 أولاً نحفظ المحادثة في قاعدة البيانات
    save_chat_from_update(update, context)

    user = update.effective_user
    name = user.first_name if user else "there"

    text = (
        f"Hello *{name}*!\n\n"
        "This is a simple test bot from your new multi-bot project.\n"
        "You can duplicate this folder to create new bots."
    )

    if update.message:
        await update.message.reply_text(text, parse_mode="Markdown")


async def cmd_ping(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle the /ping command.
    """
    # 🔹 أيضاً نسجل المحادثة عند استخدام /ping
    save_chat_from_update(update, context)

    if update.message:
        await update.message.reply_text("Pong!")


def main() -> None:
    """
    Main entry point for the Telegram bot.
    """
    setup_logging()
    load_env(ENV_PATH)

    token = get_env("TELEGRAM_BOT_TOKEN")
    bot_name = get_env("BOT_NAME", "hello_bot")

    logging.getLogger(__name__).info("Starting bot: %s", bot_name)

    app = ApplicationBuilder().token(token).build()

    # نمرر اسم البوت إلى الـ handlers عبر bot_data
    app.bot_data["BOT_NAME"] = bot_name

    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("ping", cmd_ping))

    logging.getLogger(__name__).info("Bot is polling...")
    app.run_polling()


if __name__ == "__main__":
    main()
