from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
)

# ----------------------------------------------------
#  Fix import path so we can import apps.gmail.*
# ----------------------------------------------------
ROOT = Path(__file__).resolve().parents[2]   # /home/tamer/telegram_bot
sys.path.append(str(ROOT))

from apps.gmail.gmail_config import (
    BOT_TOKEN,
    GMAIL_OAUTH_BASE_URL,
)
from src.telegram.user_store import get_gmail_credentials
# ----------------------------------------------------


# ----------------------------------------------------
# Command: /start
# ----------------------------------------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "📧 *Gmail Bot*\n\n"
        "Available commands:\n"
        "• /link_gmail – Link your Gmail account\n"
        "• /gmail – Read your latest inbox emails\n",
        parse_mode="Markdown",
    )


# ----------------------------------------------------
# Command: /link_gmail
# ----------------------------------------------------
async def link_gmail(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    telegram_id = update.effective_user.id

    url = f"{GMAIL_OAUTH_BASE_URL}/start?telegram_id={telegram_id}"

    keyboard = [
        [InlineKeyboardButton("Open Gmail Link Page", url=url)]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "🔗 *Link your Gmail account*\n\n"
        "1. Click the button below.\n"
        "2. Approve access in the Google login page.\n"
        "3. Return here and type /gmail to read your inbox.\n",
        reply_markup=reply_markup,
        parse_mode="Markdown",
    )


# ----------------------------------------------------
# Command: /gmail
# ----------------------------------------------------
async def read_gmail(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    telegram_id = update.effective_user.id

    creds = get_gmail_credentials(telegram_id)

    if creds is None:
        await update.message.reply_text(
            "❌ No Gmail account linked.\n"
            "Use /link_gmail first."
        )
        return

    # Placeholder (later you can add reading Gmail API)
    await update.message.reply_text("📨 Gmail is linked! (API to read inbox coming next)")


# ----------------------------------------------------
# Main runner
# ----------------------------------------------------
def run_bot() -> None:
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("link_gmail", link_gmail))
    app.add_handler(CommandHandler("gmail", read_gmail))

    print("🤖 Gmail Bot running...")
    app.run_polling()


if __name__ == "__main__":
    run_bot()
