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
from apps.pdf_chat.telegram_commands import register_handlers as register_pdf_handlers


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    msg = update.effective_message
    text = (
        "📄 *أهلاً بك في PDF Bot*\n\n"
        "أرسل ملف PDF إلى البوت وسيتعامل معه حسب الأوامر المتاحة.\n"
        "يمكنك أيضاً استخدام لوحة التحكم (Streamlit) في مجلد apps/pdf_chat.\n"
    )
    await msg.reply_markdown(text)


def build_application(token: str) -> Application:
    app = Application.builder().token(token).build()

    app.add_handler(CommandHandler("start", cmd_start))

    # تسجيل أوامر PDF من plugin الجاهز
    register_pdf_handlers(app)

    return app


def run_bot(env_path: Path) -> None:
    load_environment(env_path)

    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        print(f"❌ TELEGRAM_BOT_TOKEN is missing in .env: {env_path}")
        return

    app = build_application(token)
    print(f"🤖 PDF Bot listening... (env: {env_path})")
    app.run_polling()
