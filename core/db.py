from __future__ import annotations

import os
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Dict, List

import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

# =========================
# 🔧 تحميل الإعدادات و .env
# =========================

# هذا الملف في: core/db.py
# PROJECT_ROOT = telegram_bot/
BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent

# نحاول تحميل .env من جذر المشروع
ENV_PATH = PROJECT_ROOT / ".env"
if ENV_PATH.exists():
    load_dotenv(ENV_PATH)

# لا نضع أي كلمة سر افتراضية هنا ❌
PG_DSN = os.getenv("PG_DSN")
if not PG_DSN:
    raise RuntimeError(
        "❌ PG_DSN غير موجود في متغيرات البيئة.\n"
        "ضع سطر مثل:\n"
        "PG_DSN=dbname=telegram_bots user=telegram_bot password=YOUR_PASSWORD host=127.0.0.1 port=5432\n"
        "داخل ملف .env في جذر المشروع."
    )


@contextmanager
def get_conn():
    """
    يرجع اتصال psycopg2 باستخدام PG_DSN.
    يغلق الاتصال تلقائيًا بعد الانتهاء.
    """
    conn = psycopg2.connect(PG_DSN)
    try:
        yield conn
    finally:
        conn.close()


# =========================
# 🗄️ تهيئة الجداول (bot_chats)
# =========================

def init_db() -> None:
    """
    إنشاء جدول bot_chats لو لم يكن موجودًا.
    تُستدعى تلقائيًا عند استيراد الملف.
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


# نستدعي init_db مرة واحدة عند تحميل الموديول
init_db()


# =========================
# ⚙️ دوال التعامل مع bot_chats
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
    تُستخدم في تبويب قاعدة البيانات في Streamlit.
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
