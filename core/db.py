from __future__ import annotations

import os
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Dict, List

import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

# =========================
# إعداد مسارات وتحميل .env
# =========================

BASE_DIR = Path(__file__).resolve().parent      # core/
PROJECT_ROOT = BASE_DIR.parent                  # جذر المشروع: telegram_bot
ENV_PATH = PROJECT_ROOT / ".env"

if ENV_PATH.exists():
    load_dotenv(ENV_PATH)   # يحمّل PG_DSN وباقي القيم إن وجدت

# =========================
# إعداد سلسلة الاتصال PG_DSN
# =========================

# نقرأ من البيئة أولاً (هذا اللي اشتغل معك في الـ REPL)
PG_DSN = os.getenv(
    "PG_DSN",
    # افتراضي لو ما وجد في البيئة (تقدر تعدل الباسورد لو مختلف)
    "dbname=telegram_bots user=telegram_bot password=123456 host=127.0.0.1 port=5432",
)


@contextmanager
def get_conn():
    """
    يرجع اتصال psycopg2 باستخدام PG_DSN.
    يغلق الاتصال تلقائيًا بعد الانتهاء.
    """
    if not PG_DSN:
        raise RuntimeError("PG_DSN is not set. تأكد من وجوده في .env")

    conn = psycopg2.connect(PG_DSN)
    try:
        yield conn
    finally:
        conn.close()


# =========================
# تهيئة الجداول (bot_chats)
# =========================

def init_db() -> None:
    """
    إنشاء جدول bot_chats لو لم يكن موجودًا.
    """
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS bot_chats (
                id SERIAL PRIMARY KEY,
                bot_name TEXT NOT NULL,
                chat_id BIGINT NOT NULL,
                chat_type TEXT,
                title TEXT,
                username TEXT,
                message_count INTEGER NOT NULL DEFAULT 0,
                last_seen_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                UNIQUE (bot_name, chat_id)
            );
            """
        )
        conn.commit()


# نستدعي init_db عند استيراد الملف
try:
    init_db()
except Exception as exc:  # لو في مشكلة في أول تشغيل، ما نخلي الاستيراد ينهار
    # تقدر تطبع أو تسجل اللوج هنا لو حاب
    pass


# =========================
# دوال خاصة بجدول bot_chats
# =========================

def upsert_chat(
    bot_name: str,
    chat_id: int,
    chat_type: str | None = None,
    title: str | None = None,
    username: str | None = None,
) -> None:
    """
    إضافة/تحديث محادثة:
    - لو موجودة: يزيد message_count + 1 ويحدّث last_seen_at وباقي الحقول.
    - لو جديدة: يضيف سجل جديد.
    """
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO bot_chats (bot_name, chat_id, chat_type, title, username, message_count)
            VALUES (%s, %s, %s, %s, %s, 1)
            ON CONFLICT (bot_name, chat_id)
            DO UPDATE SET
                chat_type = EXCLUDED.chat_type,
                title = EXCLUDED.title,
                username = EXCLUDED.username,
                message_count = bot_chats.message_count + 1,
                last_seen_at = NOW();
            """,
            (bot_name, chat_id, chat_type, title, username),
        )
        conn.commit()


def load_chats_for_bot(bot_name: str) -> List[Dict[str, Any]]:
    """
    جلب كل المحادثات لهذا البوت من جدول bot_chats.
    ستُستخدم في تبويب قاعدة البيانات في Streamlit.
    """
    with get_conn() as conn, conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(
            """
            SELECT
                bot_name,
                chat_id,
                chat_type,
                title,
                username,
                message_count,
                last_seen_at
            FROM bot_chats
            WHERE bot_name = %s
            ORDER BY last_seen_at DESC;
            """,
            (bot_name,),
        )
        rows = cur.fetchall()
        return [dict(row) for row in rows]


def delete_chat(bot_name: str, chat_id: int) -> None:
    """
    حذف سجل محادثة واحدة حسب bot_name + chat_id.
    """
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(
            "DELETE FROM bot_chats WHERE bot_name = %s AND chat_id = %s;",
            (bot_name, chat_id),
        )
        conn.commit()


def delete_chats_for_bot(bot_name: str) -> None:
    """
    حذف جميع سجلات المحادثات لبوت معيّن.
    """
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(
            "DELETE FROM bot_chats WHERE bot_name = %s;",
            (bot_name,),
        )
        conn.commit()
