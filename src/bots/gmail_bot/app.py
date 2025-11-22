from __future__ import annotations

import os
from pathlib import Path

from telegram.ext import Application, ApplicationBuilder

from apps.gmail.telegram_commands import register_handlers


def run_bot(env_path: Path) -> None:
    """
    تشغيل بوت Gmail:
    - يقرأ TELEGRAM_BOT_TOKEN من env
    - يسجل أوامر جيميل
    - يبدأ polling
    """
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        raise RuntimeError(
            "❌ متغير TELEGRAM_BOT_TOKEN غير موجود في .env الخاص ببوت Gmail"
        )

    print("🤖 Gmail Bot listening... (env:", env_path, ")")

    app: Application = ApplicationBuilder().token(token).build()

    # تسجيل أوامر جيميل
    register_handlers(app)

    # بدء الاستماع للتحديثات
    app.run_polling(close_loop=False)
