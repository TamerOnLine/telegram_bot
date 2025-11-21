from __future__ import annotations

import os
from pathlib import Path

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
)

from src.telegram.panel.environment import load_environment
from apps.gmail.telegram_commands import register_handlers as register_gmail_handlers


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    msg = update.effective_message
    text = (
        "📧 *أهلاً بك في Gmail Bot*\n\n"
        "هذا البوت متصل بحساب Gmail عبر OAuth.\n"
        "استخدم الأوامر المتاحة (مثل /gmail) لقراءة الرسائل.\n"
        "يمكنك أيضاً استخدام لوحة التحكم (Streamlit) في مجلد apps/gmail.\n"
    )
    await msg.reply_markdown(text)


def build_application(token: str) -> Application:
    app = Application.builder().token(token).build()

    app.add_handler(CommandHandler("start", cmd_start))

    # تسجيل أوامر Gmail من plugin الجاهز
    register_gmail_handlers(app)

    return app


def run_bot(env_path: Path) -> None:
    load_environment(env_path)

    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        print(f"❌ TELEGRAM_BOT_TOKEN is missing in .env: {env_path}")
        return

    app = build_application(token)
    print(f"🤖 Gmail Bot listening... (env: {env_path})")
    app.run_polling()
