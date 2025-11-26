from __future__ import annotations

import logging
import secrets
import string
from pathlib import Path
from typing import Final

from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Update,
)
from telegram.ext import (
    ApplicationBuilder,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from core.env import load_env, get_env
from core.logging import setup_logging
from core.db import upsert_chat  # يستخدم نفس جدول bot_chats مثل بقية البوتات

# =========================
# مسارات و ثوابت عامة
# =========================

BASE_DIR = Path(__file__).resolve().parent
ENV_PATH = BASE_DIR / ".env"

logger = logging.getLogger(__name__)

TOPIC_NAME: Final[str] = "Password Generator"
TOPIC_DESCRIPTION: Final[str] = (
    "بوت لتوليد كلمات سر قوية مع واجهة أزرار تفاعلية."
)

DEFAULT_LENGTH: Final[int] = 12
MIN_LENGTH: Final[int] = 6
MAX_LENGTH: Final[int] = 64


# =========================
# دوال مساعدة
# =========================

def generate_password(length: int = DEFAULT_LENGTH) -> str:
    """
    توليد كلمة سر عشوائية قوية.
    تحتوي على:
    - حروف صغيرة وكبيرة
    - أرقام
    - رموز
    """
    length = max(MIN_LENGTH, min(length, MAX_LENGTH))

    alphabet = (
        string.ascii_lowercase
        + string.ascii_uppercase
        + string.digits
        + "!@#$%^&*()-_=+[]{};:,.?/|"
    )

    return "".join(secrets.choice(alphabet) for _ in range(length))


def build_main_keyboard() -> InlineKeyboardMarkup:
    keyboard = [
        [
            InlineKeyboardButton("🔐 كلمة سر 12", callback_data="gen:12"),
            InlineKeyboardButton("🔐 كلمة سر 20", callback_data="gen:20"),
        ],
        [
            InlineKeyboardButton("🎛 طول مخصص", callback_data="custom"),
        ],
        [
            InlineKeyboardButton("ℹ️ تعليمات", callback_data="help"),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)


def _track_chat(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    تسجيل المحادثة في جدول bot_chats في PostgreSQL
    بنفس أسلوب باقي البوتات (hello_bot, quran_hifz_bot, shop_bot).
    """
    chat = update.effective_chat
    if chat is None:
        return

    bot_name = context.bot_data.get("BOT_NAME", "password_bot")

    # اختيار عنوان مناسب (جروب / قناة / مستخدم)
    title = getattr(chat, "title", None)
    if not title:
        first = getattr(chat, "first_name", "") or ""
        last = getattr(chat, "last_name", "") or ""
        full_name = f"{first} {last}".strip()
        username = getattr(chat, "username", None)
        title = full_name or (username or "") or "—"

    upsert_chat(
        bot_name=bot_name,
        chat_id=chat.id,
        chat_type=chat.type,
        title=title,
        username=getattr(chat, "username", None),
    )


def _format_password_message(password: str, length: int) -> str:
    return (
        "🔐 *تم إنشاء كلمة سر جديدة:*\n\n"
        f"`{password}`\n\n"
        f"📏 الطول: *{length}* حرفًا\n\n"
        "⚠️ نصائح أمان:\n"
        "- لا تشارك كلمة السر مع أحد.\n"
        "- استخدم مدير كلمات سر لحفظها."
    )


# =========================
# Handlers — Commands
# =========================

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    _track_chat(update, context)

    user = update.effective_user
    name = user.first_name if user else "صديقي"

    text = (
        f"👋 أهلاً {name}!\n\n"
        f"أنا بوت *{TOPIC_NAME}*.\n\n"
        "أستطيع توليد كلمات سر قوية لك.\n\n"
        "اختر من الأزرار في الأسفل:\n"
        "• 🔐 توليد كلمة سر جاهزة (12 أو 20 حرف)\n"
        "• 🎛 طلب طول مخصص\n"
        "• ℹ️ مشاهدة التعليمات\n"
    )

    await update.message.reply_markdown(text, reply_markup=build_main_keyboard())


async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    _track_chat(update, context)

    text = (
        "ℹ️ *طريقة استخدام البوت:*\n\n"
        "1) من خلال الأزرار:\n"
        "   • 🔐 كلمة سر 12 → طول 12\n"
        "   • 🔐 كلمة سر 20 → طول 20\n"
        "   • 🎛 طول مخصص → يطلب منك إدخال رقم الطول\n\n"
        "2) من خلال الأوامر:\n"
        "   • `/pass` → كلمة سر بطول 12\n"
        "   • `/pass 24` → كلمة سر بطول 24\n\n"
        f"الطول المسموح: من {MIN_LENGTH} إلى {MAX_LENGTH}.\n"
    )
    await update.message.reply_markdown(text)


async def cmd_pass(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    _track_chat(update, context)

    # قراءة الطول من المعاملات إن وُجد
    if context.args:
        try:
            length = int(context.args[0])
        except ValueError:
            length = DEFAULT_LENGTH
    else:
        length = DEFAULT_LENGTH

    length = max(MIN_LENGTH, min(length, MAX_LENGTH))
    password = generate_password(length)
    text = _format_password_message(password, length)

    await update.message.reply_markdown(text, reply_markup=build_main_keyboard())


# =========================
# Handlers — Callbacks
# =========================

async def cb_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """التعامل مع ضغط الأزرار."""
    _track_chat(update, context)

    query = update.callback_query
    if query is None:
        return

    await query.answer()

    data = query.data or ""

    # أزرار توليد كلمة سر بطول ثابت
    if data.startswith("gen:"):
        try:
            length = int(data.split(":", 1)[1])
        except ValueError:
            length = DEFAULT_LENGTH

        length = max(MIN_LENGTH, min(length, MAX_LENGTH))
        password = generate_password(length)
        text = _format_password_message(password, length)

        await query.edit_message_text(
            text=text,
            reply_markup=build_main_keyboard(),
            parse_mode="Markdown",
        )
        return

    # زر الطول المخصص
    if data == "custom":
        context.user_data["awaiting_custom_length"] = True
        await query.edit_message_text(
            text=(
                "🎛 *طول مخصص لكلمة السر*\n\n"
                f"أرسل رقم الطول المطلوب بين {MIN_LENGTH} و {MAX_LENGTH}.\n"
                "مثال: `24`"
            ),
            parse_mode="Markdown",
        )
        return

    # زر التعليمات
    if data == "help":
        await query.edit_message_text(
            text=(
                "ℹ️ *تعليمات الاستخدام:*\n\n"
                "• استخدم الأزرار لتوليد كلمات سر سريعة.\n"
                "• أو أرسل الأمر `/pass 16` لتوليد طول معيّن.\n"
            ),
            reply_markup=build_main_keyboard(),
            parse_mode="Markdown",
        )
        return


# =========================
# Handlers — Custom length text
# =========================

async def handle_custom_length_text(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """
    هذا الهاندل يستقبل النص عندما يكون المستخدم في وضع
    'اختيار طول مخصص'.
    """
    _track_chat(update, context)

    if not context.user_data.get("awaiting_custom_length"):
        # لسنا في وضع الطول المخصص → تجاهل
        return

    message = update.message
    if message is None or not message.text:
        return

    text = message.text.strip()

    try:
        length = int(text)
    except ValueError:
        await message.reply_text(
            f"❌ يرجى إرسال رقم صحيح بين {MIN_LENGTH} و {MAX_LENGTH}."
        )
        return

    if not (MIN_LENGTH <= length <= MAX_LENGTH):
        await message.reply_text(
            f"❌ الطول يجب أن يكون بين {MIN_LENGTH} و {MAX_LENGTH}."
        )
        return

    # خرجنا من وضع الطول المخصص
    context.user_data["awaiting_custom_length"] = False

    password = generate_password(length)
    reply_text = _format_password_message(password, length)

    await message.reply_markdown(reply_text, reply_markup=build_main_keyboard())


# =========================
# Main
# =========================

def main() -> None:
    setup_logging()
    load_env(ENV_PATH)

    token = get_env("TELEGRAM_BOT_TOKEN")
    if not token:
        raise RuntimeError("❌ TELEGRAM_BOT_TOKEN غير موجود في ملف .env الخاص بالبوت.")

    # هذا الاسم يظهر في لوحة التحكم / قاعدة البيانات
    bot_name = get_env("BOT_NAME", "password_bot")

    logger.info("Starting Password Generator bot: %s", bot_name)

    app = ApplicationBuilder().token(token).build()

    # نمرر اسم البوت إلى الـ handlers عبر bot_data
    app.bot_data["BOT_NAME"] = bot_name

    # أوامر
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("help", cmd_help))
    app.add_handler(CommandHandler("pass", cmd_pass))
    app.add_handler(CommandHandler("password", cmd_pass))

    # أزرار
    app.add_handler(CallbackQueryHandler(cb_buttons))

    # استقبال النص للطول المخصص
    app.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_custom_length_text)
    )

    app.run_polling()


if __name__ == "__main__":
    main()
