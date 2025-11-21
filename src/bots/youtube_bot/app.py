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


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    msg = update.effective_message
    text = (
        "📺 *أهلاً بك في YouTube Bot*\n\n"
        "حالياً هذا البوت مخصّص للربط مع أدوات YouTube/Streamlit.\n"
        "يمكنك توسيعه لاحقاً لإدارة قوائم التشغيل، نشر الفيديوهات، أو الإشعارات.\n"
    )
    await msg.reply_markdown(text)


def build_application(token: str) -> Application:
    app = Application.builder().token(token).build()

    app.add_handler(CommandHandler("start", cmd_start))

    # لاحقاً: أضف أوامر أخرى /upload /playlist /notify ... الخ

    return app


def run_bot(env_path: Path) -> None:
    load_environment(env_path)

    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        print(f"❌ TELEGRAM_BOT_TOKEN is missing in .env: {env_path}")
        return

    app = build_application(token)
    print(f"🤖 YouTube Bot listening... (env: {env_path})")
    app.run_polling()
