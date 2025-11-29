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
    ReplyKeyboardMarkup,
    KeyboardButton,
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

# سيتم ضبطه في main()
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
    """إرجاع قائمة الوحدات من lessons."""
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("SELECT DISTINCT unit_id FROM lessons ORDER BY unit_id")
        rows = cur.fetchall()
    return [row["unit_id"] for row in rows]


def get_lessons_by_unit(unit_id: str) -> List[Dict[str, Any]]:
    """إرجاع دروس وحدة معيّنة."""
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
    """إرجاع كل الأسئلة المرتبطة بدرس معيّن."""
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
    """بحث متقدم في نص السؤال والإجابة."""
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
# جدول نتائج الامتحانات
# ==========================

def init_exam_table() -> None:
    """إنشاء جدول نتائج الامتحانات إن لم يكن موجوداً."""
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS exam_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id INTEGER NOT NULL,
                unit_id TEXT,
                lesson_id TEXT,
                lesson_title TEXT,
                total_questions INTEGER NOT NULL,
                correct_answers INTEGER NOT NULL,
                score_percent REAL NOT NULL,
                created_at TEXT NOT NULL
            );
            """
        )
        conn.commit()


def save_exam_result(
    chat_id: int,
    unit_id: str,
    lesson_id: str,
    lesson_title: str,
    total_questions: int,
    correct_answers: int,
) -> None:
    """حفظ نتيجة امتحان واحدة."""
    from datetime import datetime

    percent = (correct_answers / total_questions) * 100 if total_questions else 0.0
    created_at = datetime.utcnow().isoformat(timespec="seconds")

    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO exam_results (
                chat_id, unit_id, lesson_id, lesson_title,
                total_questions, correct_answers, score_percent, created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                chat_id,
                unit_id,
                lesson_id,
                lesson_title,
                total_questions,
                correct_answers,
                percent,
                created_at,
            ),
        )
        conn.commit()


# ==========================
# حفظ المحادثات في bot_chats (PostgreSQL)
# ==========================

def save_chat_from_update(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """حفظ معلومات المحادثة في جدول bot_chats لكل تفاعل."""
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
# لوحة الأزرار الثابتة بجانب الكيبورد
# ==========================

def build_reply_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        [
            [KeyboardButton("🏠 الرئيسية"), KeyboardButton("🔍 بحث متقدم")],
            [KeyboardButton("⬅️ السابق"), KeyboardButton("➡️ التالي")],
            [KeyboardButton("👁 تبديل الإجابة")],
            [KeyboardButton("📝 بدء امتحان"), KeyboardButton("📊 إحصائياتي")],
        ],
        resize_keyboard=True,
        one_time_keyboard=False,
    )


# ==========================
# منطق البوت
# ==========================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/start – القائمة الرئيسية (الوحدات + لوحة الأزرار السفلية)."""
    save_chat_from_update(update, context)

    units = get_units()
    if not units:
        await update.message.reply_text("لا توجد وحدات في قاعدة البيانات.")
        return

    # أزرار الوحدات (inline)
    inline_kb = [
        [InlineKeyboardButton(unit_id, callback_data=f"unit:{unit_id}")]
        for unit_id in units
    ]
    inline_kb.append(
        [InlineKeyboardButton("🔍 بحث متقدم", callback_data="search:menu")]
    )

    context.user_data.clear()
    context.user_data["view_mode"] = "home"
    context.user_data["answer_visible"] = True
    context.user_data["exam_mode"] = False

    # رسالة القائمة الرئيسية
    await update.message.reply_text(
        "🎓 نظام أسئلة اللغة العربية\n"
        "━━━━━━━━━━━━\n"
        "اختر وحدة دراسية من الأزرار، أو استخدم (🔍 بحث متقدم) للبحث في الأسئلة.",
        reply_markup=InlineKeyboardMarkup(inline_kb),
    )

    # تفعيل لوحة الأزرار الدائمة تحت الكيبورد
    await update.message.reply_text(
        "لوحة التحكم السريعة 👇",
        reply_markup=build_reply_keyboard(),
    )


async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """استقبال جميع ضغطات الأزرار inline (الوحدات / الدروس / البحث)."""
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

    elif data == "home":
        await go_home(query, context)

    elif data == "search:menu":
        await show_search_menu(query, context)


async def show_lessons(query, context: ContextTypes.DEFAULT_TYPE, unit_id: str) -> None:
    """عرض قائمة دروس وحدة معيّنة."""
    lessons = get_lessons_by_unit(unit_id)
    if not lessons:
        await query.edit_message_text(f"لا توجد دروس في الوحدة: {unit_id}")
        return

    context.user_data["unit_id"] = unit_id
    context.user_data["view_mode"] = "lessons"
    context.user_data["exam_mode"] = False

    keyboard: List[List[InlineKeyboardButton]] = []
    for lesson in lessons:
        title = lesson["title"]
        lesson_id = lesson["lesson_id"]
        keyboard.append(
            [InlineKeyboardButton(title, callback_data=f"lesson:{lesson_id}")]
        )

    keyboard.append(
        [InlineKeyboardButton("🏠 العودة للرئيسية", callback_data="home")]
    )
    keyboard.append(
        [InlineKeyboardButton("🔍 بحث متقدم", callback_data="search:menu")]
    )

    await query.edit_message_text(
        text=f"📘 الوحدة: {unit_id}\nاختر الدرس:",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


async def start_lesson_questions(
    query, context: ContextTypes.DEFAULT_TYPE, lesson_id: str
) -> None:
    """تحميل أسئلة الدرس وبدء عرضها من السؤال الأول (وضع تعلّم)."""
    questions = get_questions_by_lesson(lesson_id)
    if not questions:
        await query.edit_message_text("لا توجد أسئلة لهذا الدرس.")
        return

    unit_id = questions[0].get("unit_id", "?")
    lesson_title = questions[0].get("lesson_title", lesson_id)

    context.user_data["lesson_id"] = lesson_id
    context.user_data["unit_id"] = unit_id
    context.user_data["lesson_title"] = lesson_title
    context.user_data["questions"] = questions
    context.user_data["q_index"] = 0
    context.user_data["view_mode"] = "lesson"
    context.user_data["answer_visible"] = True
    context.user_data["exam_mode"] = False

    await show_current_question(query, context, edit=True)


async def show_current_question(
    source, context: ContextTypes.DEFAULT_TYPE, edit: bool = False
) -> None:
    """
    عرض السؤال الحالي (وضع تعلّم/بحث) كبطاقة تعليمية.
    إذا كان المصدر CallbackQuery نستخدم edit_message_text،
    وإذا كان Update (رسالة عادية) نستخدم reply_text.
    """
    questions: List[Dict[str, Any]] = context.user_data.get("questions", [])
    idx: int = context.user_data.get("q_index", 0)
    view_mode: str = context.user_data.get("view_mode", "lesson")
    search_query: str = context.user_data.get("search_query", "")
    show_answer: bool = context.user_data.get("answer_visible", True)

    if not questions:
        msg = "لا توجد أسئلة حالياً."
        if isinstance(source, Update):
            await source.message.reply_text(msg)
        else:
            await source.edit_message_text(msg)
        return

    idx = max(0, min(idx, len(questions) - 1))
    context.user_data["q_index"] = idx

    q = questions[idx]
    unit_id = q.get("unit_id") or context.user_data.get("unit_id", "?")
    lesson_title = q.get("lesson_title") or context.user_data.get("lesson_title", "")
    q_type = q["type"]
    q_text = q["question"]
    q_answer = q["answer"]

    # رأس البطاقة
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

    # محتوى البطاقة
    if show_answer:
        body = (
            f"❓ السؤال:\n{q_text}\n\n"
            f"🧷 نوع السؤال: {q_type}\n\n"
            f"📌 الإجابة النموذجية:\n{q_answer}"
        )
    else:
        body = (
            f"❓ السؤال:\n{q_text}\n\n"
            f"🧷 نوع السؤال: {q_type}\n\n"
            "📌 الإجابة مخفية الآن.\n"
            "اضغط على زر «👁 تبديل الإجابة» لعرضها."
        )

    text = header + body

    if isinstance(source, Update) or not edit:
        await source.message.reply_text(text)
    else:
        await source.edit_message_text(text)


async def go_home(query, context: ContextTypes.DEFAULT_TYPE) -> None:
    """العودة للقائمة الرئيسية (مع الإبقاء على لوحة الأزرار السفلية)."""
    context.user_data.clear()
    context.user_data["view_mode"] = "home"
    context.user_data["answer_visible"] = True
    context.user_data["exam_mode"] = False

    units = get_units()
    if not units:
        await query.edit_message_text("لا توجد وحدات في قاعدة البيانات.")
        return

    inline_kb = [
        [InlineKeyboardButton(unit_id, callback_data=f"unit:{unit_id}")]
        for unit_id in units
    ]
    inline_kb.append(
        [InlineKeyboardButton("🔍 بحث متقدم", callback_data="search:menu")]
    )

    await query.edit_message_text(
        "🎓 نظام أسئلة اللغة العربية\n"
        "━━━━━━━━━━━━\n"
        "اختر وحدة دراسية من الأزرار، أو استخدم (🔍 بحث متقدم) للبحث في الأسئلة.",
        reply_markup=InlineKeyboardMarkup(inline_kb),
    )


async def show_search_menu(query, context: ContextTypes.DEFAULT_TYPE) -> None:
    """شاشة البحث المتقدم: تطلب من المستخدم إرسال كلمة/جملة."""
    context.user_data["view_mode"] = "search_intro"
    context.user_data["search_query"] = ""
    context.user_data["answer_visible"] = True
    context.user_data["exam_mode"] = False

    await query.edit_message_text(
        "🔍 البحث المتقدم عن الأسئلة\n"
        "━━━━━━━━━━━━\n"
        "أرسل الآن كلمة أو جملة نبحث بها في نص السؤال والإجابة.\n\n"
        "أمثلة:\n"
        "- الهمزة\n"
        "- الفعل الماضي\n"
        "- كان وأخواتها\n\n"
        "سأعرض لك نتائج البحث على شكل بطاقات تدريب يمكنك التنقل بينها "
        "باستخدام الأزرار أسفل الكيبورد.",
    )


# ==========================
# وضع الامتحان
# ==========================

async def show_exam_question(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """عرض السؤال الحالي في وضع الامتحان (بدون إظهار الإجابة)."""
    questions: List[Dict[str, Any]] = context.user_data.get("exam_questions", [])
    idx: int = context.user_data.get("exam_index", 0)

    if not questions:
        await update.message.reply_text("لا توجد أسئلة في الامتحان الحالي.")
        return

    if idx >= len(questions):
        await finish_exam(update, context)
        return

    q = questions[idx]
    unit_id = q.get("unit_id") or context.user_data.get("unit_id", "?")
    lesson_title = q.get("lesson_title") or context.user_data.get("lesson_title", "")
    q_type = q["type"]
    q_text = q["question"]

    text = (
        f"📝 *امتحان – سؤال {idx + 1} من {len(questions)}*\n"
        f"📘 الوحدة: {unit_id} / الدرس: {lesson_title}\n"
        "━━━━━━━━━━━━\n"
        f"❓ السؤال:\n{q_text}\n\n"
        f"🧷 نوع السؤال: {q_type}\n\n"
        "✏️ *اكتب إجابتك وأرسلها برسالة الآن.*"
    )

    await update.message.reply_text(text, parse_mode="Markdown")


async def handle_exam_answer(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    student_answer: str,
) -> None:
    """معالجة إجابة الطالب في وضع الامتحان."""
    questions: List[Dict[str, Any]] = context.user_data.get("exam_questions", [])
    idx: int = context.user_data.get("exam_index", 0)

    if not questions or idx >= len(questions):
        await update.message.reply_text("لا يوجد سؤال حالي في الامتحان.")
        return

    q = questions[idx]
    correct_answer = q["answer"]

    # مقارنة بسيطة قابلة للتطوير لاحقاً
    def normalize(s: str) -> str:
        return " ".join(s.strip().replace("ـ", "").split()).lower()

    is_correct = normalize(student_answer) == normalize(correct_answer)

    if is_correct:
        await update.message.reply_text("✅ إجابة صحيحة، أحسنت 👏")
        context.user_data["exam_correct"] = context.user_data.get("exam_correct", 0) + 1
    else:
        await update.message.reply_text(
            "❌ إجابة غير دقيقة.\n"
            f"الإجابة النموذجية كانت:\n{correct_answer}"
        )

    # الانتقال للسؤال التالي
    context.user_data["exam_index"] = idx + 1
    await show_exam_question(update, context)


async def finish_exam(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """إنهاء الامتحان وحفظ النتيجة."""
    questions: List[Dict[str, Any]] = context.user_data.get("exam_questions", [])
    total = len(questions)
    correct = context.user_data.get("exam_correct", 0)

    unit_id = context.user_data.get("unit_id", "")
    lesson_id = context.user_data.get("lesson_id", "")
    lesson_title = context.user_data.get("lesson_title", "")

    chat_id = update.effective_chat.id

    if total > 0:
        save_exam_result(
            chat_id=chat_id,
            unit_id=unit_id,
            lesson_id=lesson_id,
            lesson_title=lesson_title,
            total_questions=total,
            correct_answers=correct,
        )

    percent = (correct / total) * 100 if total else 0.0

    await update.message.reply_text(
        f"📊 *انتهى الامتحان*\n"
        f"عدد الأسئلة: {total}\n"
        f"الإجابات الصحيحة: {correct}\n"
        f"النتيجة: {percent:.1f}٪",
        parse_mode="Markdown",
    )

    # الخروج من وضع الامتحان
    context.user_data["exam_mode"] = False
    context.user_data["view_mode"] = "lesson"


# ==========================
# إحصائيات الطالب
# ==========================

async def show_stats(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    chat_id: int,
) -> None:
    """عرض إحصائيات بسيطة عن أداء الطالب."""
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT
                COUNT(*) AS exams_count,
                AVG(score_percent) AS avg_score
            FROM exam_results
            WHERE chat_id = ?
            """,
            (chat_id,),
        )
        row = cur.fetchone()

        cur.execute(
            """
            SELECT lesson_title, score_percent, created_at
            FROM exam_results
            WHERE chat_id = ?
            ORDER BY created_at DESC
            LIMIT 5
            """,
            (chat_id,),
        )
        last_exams = cur.fetchall()

    if not row or row[0] == 0:
        await update.message.reply_text(
            "لا توجد إحصائيات بعد.\n"
            "ابدأ امتحاناً واحداً على الأقل باستخدام زر (📝 بدء امتحان)."
        )
        return

    exams_count = row[0]
    avg_score = row[1] or 0.0

    lines = [
        "📊 *إحصائياتك العامة*",
        "━━━━━━━━━━━━",
        f"عدد الامتحانات المنجزة: {exams_count}",
        f"متوسط نتيجتك: {avg_score:.1f}٪",
        "",
        "📝 آخر 5 امتحانات:",
    ]

    for exam in last_exams:
        lesson_title, score_percent, created_at = exam
        lines.append(f"- {lesson_title} — {score_percent:.1f}٪ ({created_at})")

    await update.message.reply_text(
        "\n".join(lines),
        parse_mode="Markdown",
    )


# ==========================
# استقبال النصوص (لوحة الأزرار + البحث + الامتحان)
# ==========================

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    save_chat_from_update(update, context)

    text = (update.message.text or "").strip()
    view_mode = context.user_data.get("view_mode")
    exam_mode = context.user_data.get("exam_mode", False)

    keyboard_labels = {
        "🏠 الرئيسية",
        "🔍 بحث متقدم",
        "⬅️ السابق",
        "➡️ التالي",
        "👁 تبديل الإجابة",
        "📝 بدء امتحان",
        "📊 إحصائياتي",
    }

    # إذا كنا في وضع الامتحان وأرسل الطالب نصاً ليس من أزرار الكيبورد -> نعتبره إجابة
    if exam_mode and text not in keyboard_labels:
        await handle_exam_answer(update, context, student_answer=text)
        return

    # --------- أوامر لوحة الأزرار السفلية ---------
    if text == "🏠 الرئيسية":
        context.user_data["exam_mode"] = False
        await start(update, context)
        return

    if text == "🔍 بحث متقدم":
        context.user_data["exam_mode"] = False
        context.user_data["view_mode"] = "search_intro"
        context.user_data["search_query"] = ""
        context.user_data["answer_visible"] = True
        await update.message.reply_text(
            "🔍 أرسل الآن كلمة أو جملة نبحث بها في نص السؤال والإجابة."
        )
        return

    if text == "➡️ التالي":
        questions: List[Dict[str, Any]] = context.user_data.get("questions", [])
        if not questions:
            await update.message.reply_text("لا توجد أسئلة حالياً للتنقّل بينها.")
            return
        context.user_data["q_index"] = context.user_data.get("q_index", 0) + 1
        await show_current_question(update, context, edit=False)
        return

    if text == "⬅️ السابق":
        questions: List[Dict[str, Any]] = context.user_data.get("questions", [])
        if not questions:
            await update.message.reply_text("لا توجد أسئلة حالياً للتنقّل بينها.")
            return
        context.user_data["q_index"] = context.user_data.get("q_index", 0) - 1
        await show_current_question(update, context, edit=False)
        return

    if text == "👁 تبديل الإجابة":
        questions: List[Dict[str, Any]] = context.user_data.get("questions", [])
        if not questions:
            await update.message.reply_text("لا توجد أسئلة حالياً.")
            return
        current = context.user_data.get("answer_visible", True)
        context.user_data["answer_visible"] = not current
        await show_current_question(update, context, edit=False)
        return

    if text == "📝 بدء امتحان":
        questions: List[Dict[str, Any]] = context.user_data.get("questions", [])
        lesson_id = context.user_data.get("lesson_id")
        unit_id = context.user_data.get("unit_id")
        lesson_title = context.user_data.get("lesson_title", "")

        if not questions or not lesson_id or not unit_id:
            await update.message.reply_text(
                "للبدء بالامتحان:\n"
                "اختر أولاً وحدة ودرس من القائمة، ثم اضغط (📝 بدء امتحان)."
            )
            return

        context.user_data["exam_mode"] = True
        context.user_data["exam_questions"] = questions
        context.user_data["exam_index"] = 0
        context.user_data["exam_correct"] = 0

        await update.message.reply_text(
            "✅ تم بدء الامتحان لهذا الدرس.\n"
            "أجب عن كل سؤال بالكتابة ثم أرسل.\n"
            "يمكنك إيقاف الامتحان في أي وقت بالعودة إلى الرئيسية."
        )

        await show_exam_question(update, context)
        return

    if text == "📊 إحصائياتي":
        chat_id = update.effective_chat.id
        await show_stats(update, context, chat_id)
        return

    # --------- منطق البحث المتقدم ---------
    if view_mode != "search_intro":
        # نص عادي في وضع آخر نتجاهله
        return

    query_text = text
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
    context.user_data["answer_visible"] = True
    context.user_data["exam_mode"] = False

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

    # إنشاء جدول نتائج الامتحانات إذا لم يكن موجوداً
    init_exam_table()

    logger = logging.getLogger(__name__)
    logger.info("Starting bot: %s", bot_name)
    logger.info("Using questions DB: %s", DB_PATH)

    app = Application.builder().token(token).build()
    app.bot_data["BOT_NAME"] = bot_name

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    logger.info("Bot is polling.")
    app.run_polling()


if __name__ == "__main__":
    main()
