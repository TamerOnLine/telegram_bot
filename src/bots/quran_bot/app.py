from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, List

from telegram import (
    Update,
    ReplyKeyboardMarkup,
)
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

from src.telegram.panel.environment import load_environment
from src.telegram.db import upsert_user_from_chat, add_message

# =====================
# إعدادات عامة
# =====================

# سيتم تحديثها من .env داخل run_bot
BOT_PROFILE: str = "quran"

# حالة المستخدمين في الذاكرة فقط (لتجربة البوت)
UserState = Dict[str, Any]
user_states: Dict[int, UserState] = {}


def get_user_state(user_id: int) -> UserState:
    """
    إرجاع حالة مستخدم معيّن (مع إنشاء افتراضية إن لم تكن موجودة).
    """
    if user_id not in user_states:
        user_states[user_id] = {
            "surah": "الفاتحة",
            "verse_index": 1,
            "chunk": 1,  # عدد الآيات في كل دفعة
        }
    return user_states[user_id]


# لوحة أزرار بسيطة لاختيار السورة (تجريبية)
SURAH_BUTTONS: List[List[str]] = [
    ["الفاتحة", "البقرة"],
    ["آل عمران", "النساء"],
]


# =====================
# دوال التسجيل في DB
# =====================


def _log_incoming(update: Update) -> None:
    """
    حفظ رسالة واردة من المستخدم في DB مع bot_profile.
    """
    msg = update.effective_message
    chat = msg.chat

    try:
        chat_id = int(chat.id)
    except Exception:
        return

    text = msg.text or msg.caption or ""

    # 1) حفظ/تحديث المستخدم
    upsert_user_from_chat(chat, bot_profile=BOT_PROFILE)

    # 2) حفظ الرسالة
    add_message(chat_id, "in", text, bot_profile=BOT_PROFILE)


def _log_outgoing(chat_id: int | str, text: str) -> None:
    """
    حفظ رسالة صادرة من البوت في DB مع bot_profile.
    """
    try:
        db_chat_id = int(str(chat_id))
    except Exception:
        return

    add_message(db_chat_id, "out", text, bot_profile=BOT_PROFILE)


# =====================
# أوامر البوت
# =====================


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    _log_incoming(update)

    msg = update.effective_message
    chat_id = msg.chat_id

    keyboard = ReplyKeyboardMarkup(SURAH_BUTTONS, resize_keyboard=True)

    text = (
        "👋 *أهلاً بك في بوت تحفيظ القرآن*\n\n"
        "الأوامر المتاحة:\n"
        "/setsurah — اختيار السورة\n"
        "/setchunk — عدد الآيات في كل دفعة\n"
        "/next — إرسال الآيات التالية (تجريبية الآن)\n"
        "/repeat — إعادة آخر دفعة\n"
        "/progress — عرض التقدّم\n\n"
        "✨ اختر سورة من الأزرار في الأسفل لبدء الحفظ."
    )

    await msg.reply_text(text, reply_markup=keyboard, parse_mode="Markdown")
    _log_outgoing(chat_id, text)


async def cmd_setsurah(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    _log_incoming(update)

    msg = update.effective_message
    chat_id = msg.chat_id
    user_id = msg.from_user.id

    # يمكن أن يأتي اسم السورة من الأمر نفسه: /setsurah الفاتحة
    args = context.args
    if args:
        surah = " ".join(args)
    else:
        # أو من الرسالة السابقة، لكن هنا سنكتفي برسالة إرشادية
        surah = None

    if not surah:
        text = (
            "❓ استخدم الأمر بهذا الشكل:\n"
            "`/setsurah الفاتحة`\n"
            "أو اختر السورة مباشرة من الأزرار في الأسفل."
        )
        await msg.reply_text(text, parse_mode="Markdown")
        _log_outgoing(chat_id, text)
        return

    state = get_user_state(user_id)
    state["surah"] = surah
    state["verse_index"] = 1

    text = f"✅ تم اختيار سورة *{surah}*.\nاستخدم `/next` لبدء الحفظ."
    await msg.reply_text(text, parse_mode="Markdown")
    _log_outgoing(chat_id, text)


async def cmd_setchunk(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    _log_incoming(update)

    msg = update.effective_message
    chat_id = msg.chat_id
    user_id = msg.from_user.id

    if not context.args or not context.args[0].isdigit():
        text = "❓ استخدم الأمر بهذا الشكل: `/setchunk 3` (مثلاً 3 آيات في كل دفعة)."
        await msg.reply_text(text, parse_mode="Markdown")
        _log_outgoing(chat_id, text)
        return

    chunk = int(context.args[0])
    if chunk <= 0:
        chunk = 1

    state = get_user_state(user_id)
    state["chunk"] = chunk

    text = f"✅ تم ضبط عدد الآيات في كل دفعة إلى: *{chunk}*."
    await msg.reply_text(text, parse_mode="Markdown")
    _log_outgoing(chat_id, text)


async def cmd_next(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    _log_incoming(update)

    msg = update.effective_message
    chat_id = msg.chat_id
    user_id = msg.from_user.id

    state = get_user_state(user_id)
    surah = state["surah"]
    verse_index = state["verse_index"]
    chunk = state["chunk"]

    # ⚠️ هذا جزء تجريبي: في المستقبل سنربطه بنصوص حقيقية للقرآن
    start = verse_index
    end = verse_index + chunk - 1
    state["verse_index"] = end + 1

    text = (
        f"📖 *(تجريبياً)* سورة {surah}\n"
        f"من آية {start} إلى آية {end}\n\n"
        "لاحقاً سنربط هذه الأوامر بالنص القرآني الحقيقي."
    )

    await msg.reply_text(text, parse_mode="Markdown")
    _log_outgoing(chat_id, text)


async def cmd_repeat(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    _log_incoming(update)

    msg = update.effective_message
    chat_id = msg.chat_id
    user_id = msg.from_user.id

    state = get_user_state(user_id)
    surah = state["surah"]
    chunk = state["chunk"]
    current = state["verse_index"]

    start = max(1, current - chunk)
    end = current - 1 if current > 1 else 1

    text = (
        f"🔁 *(تجريبياً)* إعادة من سورة {surah}\n"
        f"من آية {start} إلى آية {end}"
    )

    await msg.reply_text(text, parse_mode="Markdown")
    _log_outgoing(chat_id, text)


async def cmd_progress(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    _log_incoming(update)

    msg = update.effective_message
    chat_id = msg.chat_id
    user_id = msg.from_user.id

    state = get_user_state(user_id)
    surah = state["surah"]
    verse_index = state["verse_index"]
    chunk = state["chunk"]

    text = (
        "📊 *تقدّمك الحالي:*\n"
        f"- السورة: {surah}\n"
        f"- آخر آية تقريبية: {verse_index}\n"
        f"- عدد الآيات في كل دفعة: {chunk}"
    )

    await msg.reply_text(text, parse_mode="Markdown")
    _log_outgoing(chat_id, text)


# =====================
# هندلر الرسائل النصية
# =====================


async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    - لو كانت الرسالة هي اسم سورة من الأزرار → نعتبرها اختيار سورة.
    - غير ذلك → نعرض رسالة بسيطة.
    """
    _log_incoming(update)

    msg = update.effective_message
    chat_id = msg.chat_id
    user_id = msg.from_user.id
    text = (msg.text or "").strip()

    # هل النص يطابق أحد أزرار السور؟
    flat_buttons = [name for row in SURAH_BUTTONS for name in row]
    if text in flat_buttons:
        state = get_user_state(user_id)
        state["surah"] = text
        state["verse_index"] = 1

        reply = f"✅ تم اختيار سورة *{text}*.\nاستخدم `/next` لبدء الحفظ."
        await msg.reply_text(reply, parse_mode="Markdown")
        _log_outgoing(chat_id, reply)
        return

    # رسالة افتراضية
    reply = (
        "🙂 استخدم الأزرار لاختيار سورة، "
        "أو الأوامر: /setsurah /setchunk /next /repeat /progress"
    )
    await msg.reply_text(reply)
    _log_outgoing(chat_id, reply)


# =====================
# بناء التطبيق وتشغيله
# =====================


def build_application(token: str) -> Application:
    app = Application.builder().token(token).build()

    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("setsurah", cmd_setsurah))
    app.add_handler(CommandHandler("setchunk", cmd_setchunk))
    app.add_handler(CommandHandler("next", cmd_next))
    app.add_handler(CommandHandler("repeat", cmd_repeat))
    app.add_handler(CommandHandler("progress", cmd_progress))

    # أي رسالة نصية ليست أمرًا
    app.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler)
    )

    return app


def run_bot(env_path: Path) -> None:
    """
    نقطة الدخول لتشغيل البوت:
    - تحميل .env من المسار المعطى
    - قراءة BOT_PROFILE من .env
    - قراءة TELEGRAM_BOT_TOKEN
    - تشغيل polling
    """
    # 1) تحميل ملف .env
    load_environment(env_path)

    # 2) تحديث BOT_PROFILE من البيئة
    global BOT_PROFILE
    BOT_PROFILE = os.getenv("BOT_PROFILE", BOT_PROFILE)

    # 3) قراءة التوكن
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        print(f"❌ TELEGRAM_BOT_TOKEN is missing in .env: {env_path}")
        return

    print(f"🤖 Quran Bot starting... env={env_path}, profile={BOT_PROFILE}")

    # 4) تشغيل البوت
    app = build_application(token)
    app.run_polling()
