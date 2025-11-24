from __future__ import annotations

import logging
from pathlib import Path
from typing import Tuple

import requests
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from core.env import load_env, get_env
from core.logging import setup_logging


BASE_DIR = Path(__file__).resolve().parent
ENV_PATH = BASE_DIR / ".env"

logger = logging.getLogger(__name__)


# =========================
# دوال البحث في الإنترنت
# =========================

def web_search(query: str, max_chars: int = 800) -> str:
    """
    بحث بسيط باستخدام DuckDuckGo Instant Answer API (بدون مفتاح).
    يمكنك لاحقاً استبدالها بـ Google / Bing / أي API آخر.
    """
    url = "https://api.duckduckgo.com/"
    params = {
        "q": query,
        "format": "json",
        "no_html": 1,
        "skip_disambig": 1,
    }

    try:
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
    except Exception as exc:  # noqa: BLE001
        logger.exception("Search request failed: %s", exc)
        return "❌ حدث خطأ أثناء الاتصال بمحرك البحث. حاول مرة أخرى لاحقاً."

    # النص الرئيسي
    abstract = data.get("AbstractText") or ""
    heading = data.get("Heading") or ""
    source_url = ""
    if data.get("AbstractURL"):
        source_url = data["AbstractURL"]

    # لو مافي نص واضح نحاول نأخذ أول RelatedTopic
    if not abstract:
        related = data.get("RelatedTopics") or []
        for item in related:
            # بعض العناصر nested
            if "Text" in item:
                abstract = item["Text"]
                source_url = item.get("FirstURL", source_url)
                break
            if isinstance(item, dict) and "Topics" in item:
                for sub in item["Topics"]:
                    if "Text" in sub:
                        abstract = sub["Text"]
                        source_url = sub.get("FirstURL", source_url)
                        break
                if abstract:
                    break

    if not abstract:
        return "ℹ️ لم أجد نتيجة واضحة لهذا الموضوع. جرّب صياغة مختلفة أو كلمة أكثر تحديداً."

    # تقصير النص
    if len(abstract) > max_chars:
        abstract = abstract[: max_chars - 3] + "..."

    result_lines = [
        f"🔎 *نتيجة البحث عن:* `{query}`",
        "",
        abstract,
    ]
    if source_url:
        result_lines.append("")
        result_lines.append(f"🔗 مصدر محتمل: {source_url}")

    return "\n".join(result_lines)


# =========================
# Handlers أوامر ورسائل
# =========================

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = (
        "👋 أهلاً بك في *بوت البحث في الإنترنت*.\n\n"
        "استخدم الأمر:\n"
        "• `/search موضوعك هنا`\n\n"
        "مثال:\n"
        "`/search What is Pi Network?`\n\n"
        "أو فقط أرسل رسالة تبدأ بـ /search وسيبحث البوت عن أقرب نتيجة نصية."
    )
    await update.effective_message.reply_markdown(text)


async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = (
        "📚 *طريقة استخدام البوت:*\n\n"
        "1️⃣ أرسل:\n"
        "   `/search موضوع البحث`\n"
        "   مثال: `/search فوائد تعلم البرمجة`\n\n"
        "2️⃣ البوت سيجلب لك ملخص نصي + رابط للمصدر إن وُجد.\n\n"
        "📌 ملاحظة: هذا مثال تعليمي بسيط يعتمد على DuckDuckGo API ويمكنك فيما بعد "
        "تعديله لأي محرك بحث أو API مدفوع."
    )
    await update.effective_message.reply_markdown(text)


async def cmd_search(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # نص البحث إما من args أو من بقية السطر بعد /search
    if context.args:
        query = " ".join(context.args).strip()
    else:
        # fallback لو أحد كتب /search بدون args في بعض الكلاينتات
        full_text = update.effective_message.text or ""
        parts = full_text.split(maxsplit=1)
        query = parts[1].strip() if len(parts) > 1 else ""

    if not query:
        await update.effective_message.reply_text(
            "❗ الرجاء كتابة شيء للبحث.\nمثال:\n`/search تعلم بايثون`",
            parse_mode="Markdown",
        )
        return

    await update.effective_message.reply_text("⏳ جاري البحث في الإنترنت...", quote=True)

    # نعمل البحث (متزامن بسيط)
    result_text = web_search(query)

    await update.effective_message.reply_markdown(result_text)


# لو حاب تسمح للمستخدم يكتب البحث بدون /search، مثلاً أي رسالة نصية
async def handle_plain_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = update.effective_message.text or ""
    text = text.strip()

    # نتجاهل رسائل قصيرة جداً
    if len(text) < 4:
        return

    await update.effective_message.reply_text(
        "🔎 فهمت أنك تريد البحث عن:\n"
        f"`{text}`\n\n"
        "⏳ انتظر لحظات من فضلك...",
        parse_mode="Markdown",
    )

    result_text = web_search(text)
    await update.effective_message.reply_markdown(result_text)


# =========================
# نقطة الدخول main()
# =========================

def main() -> None:
    # 1) إعداد اللوجينغ العام للمشروع
    setup_logging()

    # 2) تحميل .env الخاص بهذا البوت
    load_env(ENV_PATH)

    # 3) قراءة التوكن واسم البوت
    token = get_env("TELEGRAM_BOT_TOKEN")
    bot_name = get_env("BOT_NAME", "search_bot")

    logger.info("Starting bot: %s", bot_name)

    # 4) بناء التطبيق
    app = (
        ApplicationBuilder()
        .token(token)
        .build()
    )

    # 5) تسجيل الأوامر
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("help", cmd_help))
    app.add_handler(CommandHandler("search", cmd_search))

    # 6) (اختياري) أي رسالة نصية تعتبر بحث
    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            handle_plain_text,
        )
    )

    logger.info("Search bot is polling...")
    app.run_polling()


if __name__ == "__main__":
    main()
