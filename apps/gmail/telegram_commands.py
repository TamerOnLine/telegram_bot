from __future__ import annotations

from pathlib import Path

from telegram.ext import CommandHandler, ContextTypes
from telegram import Update

from apps.gmail.gmail_client import get_last_emails

# 🔹 ملف .env الخاص بوحدة Gmail
from src.telegram.panel.environment import load_environment

ENV_PATH = Path(__file__).resolve().parent / ".env"


async def cmd_gmail(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    msg = update.effective_message

    # 🧩 تحميل بيئة Gmail من مجلدها قبل التنفيذ
    load_environment(ENV_PATH)

    try:
        emails = get_last_emails(limit=5)
    except Exception as e:
        await msg.reply_text(f"❌ Error while reading Gmail:\n{e}")
        return

    if not emails:
        await msg.reply_text("📭 لا توجد رسائل.")
        return

    for e in emails:
        text = (
            "📧 *Email*\n"
            f"👤 From: {e['from']}\n"
            f"✉️ Subject: {e['subject']}\n"
            f"🕒 Date: {e['date']}\n"
            f"📝 {e['snippet']}\n"
            f"🔗 [فتح البريد]({e['link']})"
        )
        await msg.reply_text(
            text,
            parse_mode="Markdown",
            disable_web_page_preview=True,
        )


def register_handlers(app) -> None:
    """نسجّل أوامر Gmail للبوت."""
    app.add_handler(CommandHandler("gmail", cmd_gmail))
