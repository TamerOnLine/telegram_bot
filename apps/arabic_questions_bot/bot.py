from __future__ import annotations

import logging
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Dict, List

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)

from core.env import load_env, get_env
from core.logging import setup_logging
from core.db import upsert_chat

# ==========================
# إعداد المسارات العامة
# ==========================

BASE_DIR = Path(__file__).resolve().parent
ENV_PATH = BASE_DIR / ".env"

# سيتم ضبطها في main() من متغيّرات البيئة
DB_PATH: Path = BASE_DIR / "questions.db"


# ==========================
# دوال مساعدة لقاعدة البيانات (SQLite)
# ==========================

@contextmanager
def get_conn():
    """اتصال SQLite إلى ملف الأسئلة."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def get_units() -> List[str]:
    """
    إرجاع قائمة معرفات الوحدات الموجودة في جدول lessons.
    """
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT DISTINCT unit_id FROM lessons ORDER BY unit_id"
        )
        rows = cur.fetchall()
    return [row["unit_id"] for row in rows]


def get_lessons_by_unit(unit_id: str) -> List[Dict[str, Any]]:
    """
    إرجاع دروس وحدة معيّنة.
    """
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT id, lesson_code, title
            FROM lessons
            WHERE unit_id = ?
            ORDER BY lesson_code
            """,
            (unit_id,),
        )
        rows = cur.fetchall()

    lessons: List[Dict[str, Any]] = []
    for row in rows:
        lessons.append(
            {
                "lesson_id": row["id"],
                "lesson_code": row["lesson_code"],
                "title": row["title"],
            }
        )
    return lessons


def get_questions_by_lesson(lesson_id: str) -> List[Dict[str, Any]]:
    """
    إرجاع كل الأسئلة المرتبطة بدرس معيّن.
    """
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT id, type, question, answer
            FROM questions
            WHERE lesson_id = ?
            ORDER BY id
            """,
            (lesson_id,),
        )
        rows = cur.fetchall()

    questions: List[Dict[str, Any]] = []
    for row in rows:
        questions.append(
            {
                "id": row["id"],
                "type": row["type"],
                "question": row["question"],
                "answer": row["answer"],
            }
        )
    return questions


# ==========================
# تتبّع المحادثات في bot_chats (PostgreSQL)
# ==========================

def save_chat_from_update(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    حفظ معلومات المحادثة في جدول bot_chats لكل تفاعل.
    يظهر بعدها في لوحة التحكم (تبويب قاعدة البيانات).
    """
    chat = update.effective_chat
    if chat is None:
        return

    bot_name = context.bot_data.get("BOT_NAME", "arabic_questions_bot")

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


# ==========================
# منطق البوت
# ==========================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    /start – عرض الوحدات.
    """
    # نسجّل المحادثة في PostgreSQL
    save_chat_from_update(update, context)

    units = get_units()
    if not units:
        await update.message.reply_text("لا توجد وحدات في قاعدة البيانات.")
        return

    keyboard: List[List[InlineKeyboardButton]] = []
    for unit_id in units:
        keyboard.append(
            [InlineKeyboardButton(unit_id, callback_data=f"unit:{unit_id}")]
        )

    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "مرحباً 👋\n"
        "هذا البوت يعرض أسئلة مادة اللغة العربية.\n\n"
        "اختر الوحدة:",
        reply_markup=reply_markup,
    )


async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    استقبال جميع ضغطات الأزرار (InlineKeyboard).
    """
    # أيضاً نسجّل أي تفاعل بالأزرار
    save_chat_from_update(update, context)

    query = update.callback_query
    await query.answer()

    data = query.data or ""

    if data.startswith("unit:"):
        unit_id = data.split(":", 1)[1]
        await show_lessons(query, context, unit_id)

    elif data.startswith("lesson:"):
        # data شكلها: lesson:<lesson_id>
        lesson_id = data.split(":", 1)[1]
        await start_lesson_questions(query, context, lesson_id)

    elif data.startswith("nav:"):
        direction = data.split(":", 1)[1]
        await navigate_question(query, context, direction)


async def show_lessons(query, context: ContextTypes.DEFAULT_TYPE, unit_id: str) -> None:
    """
    عرض قائمة دروس وحدة معيّنة.
    """
    lessons = get_lessons_by_unit(unit_id)
    if not lessons:
        await query.edit_message_text(f"لا توجد دروس في الوحدة: {unit_id}")
        return

    # حفظ الوحدة الحالية في user_data (للمعلومة فقط)
    context.user_data["unit_id"] = unit_id

    keyboard: List[List[InlineKeyboardButton]] = []
    for lesson in lessons:
        title = lesson["title"]
        lesson_id = lesson["lesson_id"]
        keyboard.append(
            [InlineKeyboardButton(title, callback_data=f"lesson:{lesson_id}")]
        )

    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(
        text=f"الوحدة: {unit_id}\nاختر الدرس:",
        reply_markup=reply_markup,
    )


async def start_lesson_questions(
    query, context: ContextTypes.DEFAULT_TYPE, lesson_id: str
) -> None:
    """
    تحميل أسئلة الدرس وبدء عرضها من السؤال الأول.
    """
    questions = get_questions_by_lesson(lesson_id)
    if not questions:
        await query.edit_message_text("لا توجد أسئلة لهذا الدرس.")
        return

    # جلب معلومات الدرس لعرض العنوان
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT unit_id, title FROM lessons WHERE id = ?",
            (lesson_id,),
        )
        row = cur.fetchone()

    if row:
        unit_id = row["unit_id"]
        lesson_title = row["title"]
    else:
        unit_id = "?"
        lesson_title = lesson_id

    # حفظ الحالة في user_data
    context.user_data["lesson_id"] = lesson_id
    context.user_data["lesson_title"] = lesson_title
    context.user_data["unit_id"] = unit_id
    context.user_data["questions"] = questions
    context.user_data["q_index"] = 0

    # عرض أول سؤال
    await show_current_question(query, context, edit=True)


def build_nav_keyboard(has_prev: bool, has_next: bool) -> InlineKeyboardMarkup:
    """
    إنشاء أزرار التنقل بين الأسئلة.
    """
    buttons: List[List[InlineKeyboardButton]] = []
    row: List[InlineKeyboardButton] = []

    if has_prev:
        row.append(InlineKeyboardButton("⬅️ السابق", callback_data="nav:prev"))
    if has_next:
        row.append(InlineKeyboardButton("التالي ➡️", callback_data="nav:next"))

    if row:
        buttons.append(row)

    return InlineKeyboardMarkup(buttons)


async def show_current_question(
    query, context: ContextTypes.DEFAULT_TYPE, edit: bool = False
) -> None:
    """
    عرض السؤال الحالي (الذي يشير إليه q_index) مع الجواب في نفس الرسالة.
    """
    questions: List[Dict[str, Any]] = context.user_data.get("questions", [])
    idx: int = context.user_data.get("q_index", 0)
    lesson_title: str = context.user_data.get("lesson_title", "")
    unit_id: str = context.user_data.get("unit_id", "")
    lesson_id: str = context.user_data.get("lesson_id", "")

    if not questions:
        if edit:
            await query.edit_message_text("لا توجد أسئلة.")
        else:
            await query.message.reply_text("لا توجد أسئلة.")
        return

    if idx < 0:
        idx = 0
    if idx > len(questions) - 1:
        idx = len(questions) - 1

    context.user_data["q_index"] = idx

    q = questions[idx]
    q_type = q["type"]
    q_text = q["question"]
    q_answer = q["answer"]

    header = (
        f"الوحدة: {unit_id}\n"
        f"الدرس: {lesson_title}\n"
        f"السؤال رقم: {idx + 1} من {len(questions)}\n"
        f"------------------------\n"
    )

    body = (
        f"النوع: {q_type}\n\n"
        f"السؤال:\n{q_text}\n\n"
        f"الإجابة:\n{q_answer}"
    )

    text = header + body

    has_prev = idx > 0
    has_next = idx < len(questions) - 1
    reply_markup = build_nav_keyboard(has_prev, has_next)

    if edit:
        await query.edit_message_text(text=text, reply_markup=reply_markup)
    else:
        await query.message.reply_text(text=text, reply_markup=reply_markup)


async def navigate_question(
    query, context: ContextTypes.DEFAULT_TYPE, direction: str
) -> None:
    """
    الانتقال إلى السؤال السابق أو التالي.
    """
    questions: List[Dict[str, Any]] = context.user_data.get("questions", [])
    if not questions:
        await query.edit_message_text("لا توجد أسئلة.")
        return

    idx = context.user_data.get("q_index", 0)

    if direction == "next":
        idx += 1
    elif direction == "prev":
        idx -= 1

    if idx < 0:
        idx = 0
    if idx > len(questions) - 1:
        idx = len(questions) - 1

    context.user_data["q_index"] = idx
    await show_current_question(query, context, edit=True)


# ==========================
# نقطة التشغيل الرئيسية
# ==========================

def main() -> None:
    global DB_PATH

    # لوجينغ موحّد
    setup_logging()

    # تحميل .env الخاص بهذا البوت
    load_env(ENV_PATH)

    # قراءة الإعدادات من .env
    token = get_env("TELEGRAM_BOT_TOKEN")
    bot_name = get_env("BOT_NAME", "arabic_questions_bot")
    db_path_str = get_env("QUESTIONS_DB_PATH", str(BASE_DIR / "questions.db"))
    DB_PATH = Path(db_path_str)

    logging.getLogger(__name__).info("Starting bot: %s", bot_name)
    logging.getLogger(__name__).info("Using questions DB: %s", DB_PATH)

    app = Application.builder().token(token).build()

    # نمرّر اسم البوت لجميع الهاندلرز
    app.bot_data["BOT_NAME"] = bot_name

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_callback))

    logging.getLogger(__name__).info("Bot is polling.")
    app.run_polling()


if __name__ == "__main__":
    main()
