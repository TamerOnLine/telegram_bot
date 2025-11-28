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
    MessageHandler,
    filters,
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
        cur.execute("SELECT DISTINCT unit_id FROM lessons ORDER BY unit_id")
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
            SELECT q.id, q.type, q.question, q.answer,
                   l.unit_id, l.title
            FROM questions q
            JOIN lessons l ON l.id = q.lesson_id
            WHERE q.lesson_id = ?
            ORDER BY l.unit_id, l.lesson_code, q.id
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
                "unit_id": row["unit_id"],
                "lesson_title": row["title"],
            }
        )
    return questions


def search_questions(keyword: str) -> List[Dict[str, Any]]:
    """
    بحث متقدم في نص السؤال والإجابة عن كلمة/جملة.
    يرجع قائمة أسئلة مع معلومات الوحدة والدرس.
    """
    pattern = f"%{keyword}%"
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT q.id, q.type, q.question, q.answer,
                   l.unit_id, l.title
            FROM questions q
            LEFT JOIN lessons l ON l.id = q.lesson_id
            WHERE q.question LIKE ? OR q.answer LIKE ?
            ORDER BY l.unit_id, l.lesson_code, q.id
            """,
            (pattern, pattern),
        )
        rows = cur.fetchall()

    results: List[Dict[str, Any]] = []
    for row in rows:
        results.append(
            {
                "id": row["id"],
                "type": row["type"],
                "question": row["question"],
                "answer": row["answer"],
                "unit_id": row["unit_id"],
                "lesson_title": row["title"],
            }
        )
    return results


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
    /start – عرض الوحدات + زر البحث المتقدم.
    """
    save_chat_from_update(update, context)

    units = get_units()
    if not units:
        await update.message.reply_text("لا توجد وحدات في قاعدة البيانات.")
        return

    keyboard: List[List[InlineKeyboardButton]] = [
        [InlineKeyboardButton(unit_id, callback_data=f"unit:{unit_id}")]
        for unit_id in units
    ]
    # زر البحث المتقدم
    keyboard.append(
        [InlineKeyboardButton("🔍 بحث متقدم", callback_data="search:menu")]
    )

    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "🎓 *نظام أسئلة اللغة العربية*\n"
        "━━━━━━━━━━━━\n"
        "اختر وحدة دراسية من القائمة، أو استخدم (🔍 بحث متقدم) للعثور على أسئلة حسب كلمة معيّنة.",
        reply_markup=reply_markup,
    )

    # حالة افتراضية
    context.user_data.clear()
    context.user_data["view_mode"] = "home"


async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    استقبال جميع ضغطات الأزرار (InlineKeyboard).
    """
    save_chat_from_update(update, context)

    query = update.callback_query
    await query.answer()

    data = query.data or ""

    if data.startswith("unit:"):
        unit_id = data.split(":", 1)[1]
        await show_lessons(query, context, unit_id)

    elif data.startswith("lesson:"):
        lesson_id = data.split(":", 1)[1]
        await start_lesson_questions(query, context, lesson_id)

    elif data.startswith("nav:"):
        direction = data.split(":", 1)[1]
        await navigate_question(query, context, direction)

    elif data == "home":
        await go_home(query, context)

    elif data == "search:menu":
        await show_search_menu(query, context)


async def show_lessons(query, context: ContextTypes.DEFAULT_TYPE, unit_id: str) -> None:
    """
    عرض قائمة دروس وحدة معيّنة.
    """
    lessons = get_lessons_by_unit(unit_id)
    if not lessons:
        await query.edit_message_text(f"لا توجد دروس في الوحدة: {unit_id}")
        return

    context.user_data["unit_id"] = unit_id
    context.user_data["view_mode"] = "lessons"

    keyboard: List[List[InlineKeyboardButton]] = []
    for lesson in lessons:
        title = lesson["title"]
        lesson_id = lesson["lesson_id"]
        keyboard.append(
            [InlineKeyboardButton(title, callback_data=f"lesson:{lesson_id}")]
        )

    # إضافة أزرار الرجوع والبحث
    keyboard.append(
        [InlineKeyboardButton("🏠 الرئيسية", callback_data="home")]
    )
    keyboard.append(
        [InlineKeyboardButton("🔍 بحث متقدم", callback_data="search:menu")]
    )

    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(
        text=f"📘 الوحدة: {unit_id}\nاختر الدرس:",
        reply_markup=reply_markup,
    )


async def start_lesson_questions(
    query, context: ContextTypes.DEFAULT_TYPE, lesson_id: str
) -> None:
    """
    تحميل أسئلة الدرس وبدء عرضها من السؤال الأول (Learning Mode).
    """
    questions = get_questions_by_lesson(lesson_id)
    if not questions:
        await query.edit_message_text("لا توجد أسئلة لهذا الدرس.")
        return

    # نأخذ الوحدة والعنوان من أول سؤال
    unit_id = questions[0].get("unit_id", "?")
    lesson_title = questions[0].get("lesson_title", lesson_id)

    context.user_data["lesson_id"] = lesson_id
    context.user_data["unit_id"] = unit_id
    context.user_data["lesson_title"] = lesson_title
    context.user_data["questions"] = questions
    context.user_data["q_index"] = 0
    context.user_data["view_mode"] = "lesson"

    await show_current_question(query, context, edit=True)


def build_nav_keyboard(has_prev: bool, has_next: bool) -> InlineKeyboardMarkup:
    """
    إنشاء أزرار التنقل بين الأسئلة + رجوع للرئيسية.
    """
    buttons: List[List[InlineKeyboardButton]] = []

    row: List[InlineKeyboardButton] = []
    if has_prev and has_next:
        row.append(InlineKeyboardButton("⏮ الأول", callback_data="nav:first"))
        row.append(InlineKeyboardButton("⬅️ السابق", callback_data="nav:prev"))
        row.append(InlineKeyboardButton("التالي ➡️", callback_data="nav:next"))
        row.append(InlineKeyboardButton("⏭ الأخير", callback_data="nav:last"))
        buttons.append(row)
    else:
        if has_prev:
            row.append(InlineKeyboardButton("⏮ الأول", callback_data="nav:first"))
            row.append(InlineKeyboardButton("⬅️ السابق", callback_data="nav:prev"))
        if has_next:
            row.append(InlineKeyboardButton("التالي ➡️", callback_data="nav:next"))
            row.append(InlineKeyboardButton("⏭ الأخير", callback_data="nav:last"))
        if row:
            buttons.append(row)

    # صف منفصل للرجوع والبحث
    buttons.append(
        [InlineKeyboardButton("🏠 العودة للقائمة الرئيسية", callback_data="home")]
    )
    buttons.append(
        [InlineKeyboardButton("🔍 بحث متقدم", callback_data="search:menu")]
    )

    return InlineKeyboardMarkup(buttons)


async def show_current_question(
    query_or_update, context: ContextTypes.DEFAULT_TYPE, edit: bool = False
) -> None:
    """
    عرض السؤال الحالي (Learning Mode) سواء من درس أو من نتائج البحث.
    """
    questions: List[Dict[str, Any]] = context.user_data.get("questions", [])
    idx: int = context.user_data.get("q_index", 0)
    view_mode: str = context.user_data.get("view_mode", "lesson")
    search_query: str = context.user_data.get("search_query", "")

    if not questions:
        if edit:
            await query_or_update.edit_message_text("لا توجد أسئلة.")
        else:
            await query_or_update.message.reply_text("لا توجد أسئلة.")
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

    unit_id = q.get("unit_id") or context.user_data.get("unit_id", "?")
    lesson_title = q.get("lesson_title") or context.user_data.get(
        "lesson_title", ""
    )

    # ===== تنسيق Learning Mode =====
    if view_mode == "search":
        header = (
            f"🔍 نتائج البحث عن: «{search_query}»\n"
            f"📘 الوحدة: {unit_id} — الدرس: {lesson_title}\n"
            f"🟨 السؤال {idx + 1} من {len(questions)}\n"
            "━━━━━━━━━━━━\n"
        )
    else:
        header = (
            f"🎓 التدريب — الوحدة: {unit_id} / الدرس: {lesson_title}\n"
            "━━━━━━━━━━━━\n"
            f"🟨 السؤال {idx + 1} من {len(questions)}\n"
            "━━━━━━━━━━━━\n"
        )

    body = (
        f"❔ السؤال:\n{q_text}\n\n"
        f"🧷 نوع السؤال: {q_type}\n\n"
        f"📌 الإجابة النموذجية:\n{q_answer}"
    )

    text = header + body

    has_prev = idx > 0
    has_next = idx < len(questions) - 1
    reply_markup = build_nav_keyboard(has_prev, has_next)

    if edit:
        await query_or_update.edit_message_text(text=text, reply_markup=reply_markup)
    else:
        await query_or_update.message.reply_text(text=text, reply_markup=reply_markup)


async def navigate_question(
    query, context: ContextTypes.DEFAULT_TYPE, direction: str
) -> None:
    """
    الانتقال إلى السؤال السابق / التالي / الأول / الأخير.
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
    elif direction == "first":
        idx = 0
    elif direction == "last":
        idx = len(questions) - 1

    if idx < 0:
        idx = 0
    if idx > len(questions) - 1:
        idx = len(questions) - 1

    context.user_data["q_index"] = idx
    await show_current_question(query, context, edit=True)


async def go_home(query, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    العودة للقائمة الرئيسية (عرض الوحدات + بحث متقدم).
    """
    context.user_data.clear()
    context.user_data["view_mode"] = "home"

    units = get_units()
    if not units:
        await query.edit_message_text("لا توجد وحدات في قاعدة البيانات.")
        return

    keyboard: List[List[InlineKeyboardButton]] = [
        [InlineKeyboardButton(unit_id, callback_data=f"unit:{unit_id}")]
        for unit_id in units
    ]
    keyboard.append(
        [InlineKeyboardButton("🔍 بحث متقدم", callback_data="search:menu")]
    )

    await query.edit_message_text(
        "🎓 *نظام أسئلة اللغة العربية*\n"
        "━━━━━━━━━━━━\n"
        "اختر وحدة دراسية من القائمة، أو استخدم (🔍 بحث متقدم) للعثور على أسئلة حسب كلمة معيّنة.",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


async def show_search_menu(query, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    شاشة البحث المتقدم: تطلب من المستخدم إرسال كلمة/جملة للبحث.
    """
    context.user_data["view_mode"] = "search_intro"
    context.user_data["search_query"] = ""

    keyboard = [
        [InlineKeyboardButton("🏠 العودة للقائمة الرئيسية", callback_data="home")]
    ]

    await query.edit_message_text(
        "🔍 *البحث المتقدم عن الأسئلة*\n"
        "━━━━━━━━━━━━\n"
        "أرسل الآن كلمة أو جملة نبحث بها في نص السؤال والإجابة.\n\n"
        "أمثلة:\n"
        "- الهمزة\n"
        "- الفعل الماضي\n"
        "- كان وأخواتها\n\n"
        "سأعرض لك نتائج البحث في وضع التدريب مع إمكانية التنقل بين الأسئلة.",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    استقبال النصوص عندما يكون المستخدم في وضع 'البحث المتقدم'.
    """
    view_mode = context.user_data.get("view_mode")

    # نهتم فقط عندما نكون في شاشة البحث
    if view_mode != "search_intro":
        return

    query_text = (update.message.text or "").strip()
    if not query_text:
        await update.message.reply_text("الرجاء إرسال كلمة أو جملة لنبحث عنها في الأسئلة.")
        return

    results = search_questions(query_text)

    if not results:
        await update.message.reply_text(
            f"🔍 لا توجد أسئلة تحتوي على: «{query_text}». جرّب كلمة أخرى."
        )
        return

    context.user_data["view_mode"] = "search"
    context.user_data["search_query"] = query_text
    context.user_data["questions"] = results
    context.user_data["q_index"] = 0

    await show_current_question(update, context, edit=False)


# ==========================
# نقطة التشغيل الرئيسية
# ==========================

def main() -> None:
    global DB_PATH

    setup_logging()
    load_env(ENV_PATH)

    token = get_env("TELEGRAM_BOT_TOKEN")
    bot_name = get_env("BOT_NAME", "arabic_questions_bot")
    db_path_str = get_env("QUESTIONS_DB_PATH", str(BASE_DIR / "questions.db"))
    DB_PATH = Path(db_path_str)

    logger = logging.getLogger(__name__)
    logger.info("Starting bot: %s", bot_name)
    logger.info("Using questions DB: %s", DB_PATH)

    app = Application.builder().token(token).build()
    app.bot_data["BOT_NAME"] = bot_name

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_callback))
    # نصوص البحث المتقدم
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    logger.info("Bot is polling.")
    app.run_polling()


if __name__ == "__main__":
    main()
