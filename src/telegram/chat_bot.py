from __future__ import annotations

import sqlite3
from pathlib import Path
from datetime import datetime
from typing import Any, Dict, List, Optional

# مسار قاعدة البيانات في جذر المشروع (مثل L:/telegram/telegram_data.db)
BASE_DIR = Path(__file__).resolve().parents[2]  # src/telegram/db.py → .. → .. = جذر المشروع
DB_PATH = BASE_DIR / "telegram_data.db"


# =========================
#  اتصال عام
# =========================

def _get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# =========================
#  إنشاء الجداول
# =========================

def init_db() -> None:
    """
    إنشاء جداول users و messages إذا لم تكن موجودة.
    وضمان وجود أعمدة bot_profile في كلا الجدولين.
    """
    conn = _get_conn()
    cur = conn.cursor()

    # ----- جدول users -----
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id INTEGER UNIQUE NOT NULL,
            type TEXT,
            username TEXT,
            first_name TEXT,
            last_name TEXT,
            title TEXT,
            added_at TEXT,
            last_seen_at TEXT
        )
        """
    )

    # محاولة إضافة عمود bot_profile لو لم يكن موجودًا
    try:
        cur.execute("ALTER TABLE users ADD COLUMN bot_profile TEXT")
    except sqlite3.OperationalError:
        # العمود موجود مسبقًا أو SQLite قديم، نتجاهل الخطأ
        pass

    # ----- جدول messages -----
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id INTEGER NOT NULL,
            direction TEXT CHECK(direction IN ('in', 'out')) NOT NULL,
            text TEXT,
            created_at TEXT
        )
        """
    )

    # محاولة إضافة عمود bot_profile لو لم يكن موجودًا
    try:
        cur.execute("ALTER TABLE messages ADD COLUMN bot_profile TEXT")
    except sqlite3.OperationalError:
        pass

    conn.commit()
    conn.close()


# =========================
#  helpers لتواريخ
# =========================

def _now_str() -> str:
    return datetime.utcnow().isoformat(timespec="seconds")


# =========================
#  users
# =========================

def upsert_user(
    chat_id: int,
    chat_type: Optional[str] = None,
    username: Optional[str] = None,
    first_name: Optional[str] = None,
    last_name: Optional[str] = None,
    title: Optional[str] = None,
    bot_profile: Optional[str] = None,
) -> None:
    """
    إضافة/تحديث مستخدم بناءً على chat_id.
    لو كان موجودًا → تحديث last_seen_at وبقية الحقول.
    لو غير موجود → إدخاله لأول مرة.
    يتم أيضًا حفظ bot_profile لتمييز من أي بوت جاء هذا المستخدم.
    """
    conn = _get_conn()
    cur = conn.cursor()

    now = _now_str()

    cur.execute(
        """
        INSERT INTO users (
            chat_id, type, username, first_name, last_name, title,
            added_at, last_seen_at, bot_profile
        )
        VALUES (
            :chat_id, :type, :username, :first_name, :last_name, :title,
            :added_at, :last_seen_at, :bot_profile
        )
        ON CONFLICT(chat_id) DO UPDATE SET
            type=excluded.type,
            username=excluded.username,
            first_name=excluded.first_name,
            last_name=excluded.last_name,
            title=excluded.title,
            last_seen_at=excluded.last_seen_at,
            bot_profile=excluded.bot_profile
        """,
        {
            "chat_id": chat_id,
            "type": chat_type,
            "username": username,
            "first_name": first_name,
            "last_name": last_name,
            "title": title,
            "added_at": now,
            "last_seen_at": now,
            "bot_profile": bot_profile,
        },
    )

    conn.commit()
    conn.close()


def upsert_user_from_chat(chat: Any, bot_profile: Optional[str] = None) -> None:
    """
    راحة: تستقبل telegram.Chat مباشرة من البوت.
    """
    upsert_user(
        chat_id=chat.id,
        chat_type=getattr(chat, "type", None),
        username=getattr(chat, "username", None),
        first_name=getattr(chat, "first_name", None),
        last_name=getattr(chat, "last_name", None),
        title=getattr(chat, "title", None),
        bot_profile=bot_profile,
    )


def get_all_users() -> List[Dict[str, Any]]:
    """
    جلب كل المستخدمين المخزّنين في DB.
    """
    conn = _get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT
            chat_id,
            type,
            username,
            first_name,
            last_name,
            title,
            added_at,
            last_seen_at,
            bot_profile
        FROM users
        ORDER BY last_seen_at DESC
        """
    )
    rows = cur.fetchall()
    conn.close()

    return [dict(row) for row in rows]


# =========================
#  messages
# =========================

def add_message(
    chat_id: int,
    direction: str,
    text: Optional[str],
    bot_profile: Optional[str] = None,
) -> None:
    """
    تخزين رسالة (in من المستخدم – out من البوت).
    direction: 'in' أو 'out'
    bot_profile: من أي بوت صدرت/وصلت هذه الرسالة.
    """
    conn = _get_conn()
    cur = conn.cursor()

    cur.execute(
        """
        INSERT INTO messages (chat_id, direction, text, created_at, bot_profile)
        VALUES (:chat_id, :direction, :text, :created_at, :bot_profile)
        """,
        {
            "chat_id": chat_id,
            "direction": direction,
            "text": text,
            "created_at": _now_str(),
            "bot_profile": bot_profile,
        },
    )

    conn.commit()
    conn.close()


def get_messages_for_chat(chat_id: int, limit: int = 50) -> List[Dict[str, Any]]:
    """
    جلب آخر N رسالة لمحادثة معيّنة.
    """
    conn = _get_conn()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT direction, text, created_at, bot_profile
        FROM messages
        WHERE chat_id = :chat_id
        ORDER BY id DESC
        LIMIT :limit
        """,
        {"chat_id": chat_id, "limit": limit},
    )

    rows = cur.fetchall()
    conn.close()
    return [dict(row) for row in rows]
