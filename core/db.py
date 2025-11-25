from __future__ import annotations

import os
from contextlib import contextmanager
from datetime import datetime
from typing import Any, Dict, List

import psycopg2
import psycopg2.extras
from telegram import Chat

# Read the DSN from the `.env` file
PG_DSN = os.getenv(
    "PG_DSN",
    "postgresql://telegram_bot:telegram_bot@localhost:5432/telegram_bot",
)


@contextmanager
def get_conn():
    """Context manager to safely open and close a PostgreSQL connection."""
    conn = psycopg2.connect(PG_DSN)
    try:
        yield conn
    finally:
        conn.close()


def init_db() -> None:
    """
    Initialize the `bot_chats` table in the database if it does not exist.

    This function ensures the table and index needed for chat tracking are created.
    """
    ddl = """
    CREATE TABLE IF NOT EXISTS bot_chats (
        id                  bigserial PRIMARY KEY,
        bot_name            text        NOT NULL,
        chat_id             bigint      NOT NULL,
        chat_type           text        NOT NULL,
        title               text,
        username            text,
        first_seen_at       timestamptz NOT NULL DEFAULT now(),
        last_seen_at        timestamptz NOT NULL DEFAULT now(),
        last_message_text   text,
        last_message_date   timestamptz,
        message_count       integer     NOT NULL DEFAULT 0,
        is_blocked          boolean     NOT NULL DEFAULT false,
        UNIQUE (bot_name, chat_id)
    );

    CREATE INDEX IF NOT EXISTS idx_bot_chats_bot_name_last_seen
        ON bot_chats (bot_name, last_seen_at DESC);
    """
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(ddl)
        conn.commit()


def upsert_chat(
    bot_name: str,
    chat: Chat,
    last_message_text: str | None = None,
    last_message_date: datetime | None = None,
) -> None:
    """
    Insert or update a single chat record in the database.

    Args:
        bot_name (str): The name of the bot.
        chat (Chat): The Telegram chat object.
        last_message_text (str | None): The text of the last message.
        last_message_date (datetime | None): The timestamp of the last message.
    """
    if last_message_date is None:
        last_message_date = datetime.utcnow()

    title = (
        chat.title
        or chat.username
        or f"{(chat.first_name or '')} {(chat.last_name or '')}".strip()
        or None
    )

    payload = {
        "bot_name": bot_name,
        "chat_id": chat.id,
        "chat_type": chat.type,
        "title": title,
        "username": chat.username,
        "last_message_text": last_message_text,
        "last_message_date": last_message_date,
    }

    sql = """
    INSERT INTO bot_chats (
        bot_name, chat_id, chat_type, title, username,
        last_message_text, last_message_date, message_count
    )
    VALUES (%(bot_name)s, %(chat_id)s, %(chat_type)s, %(title)s, %(username)s,
            %(last_message_text)s, %(last_message_date)s, 1)
    ON CONFLICT (bot_name, chat_id)
    DO UPDATE SET
        chat_type           = EXCLUDED.chat_type,
        title               = COALESCE(EXCLUDED.title, bot_chats.title),
        username            = COALESCE(EXCLUDED.username, bot_chats.username),
        last_seen_at        = now(),
        last_message_text   = EXCLUDED.last_message_text,
        last_message_date   = EXCLUDED.last_message_date,
        message_count       = bot_chats.message_count + 1;
    """

    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(sql, payload)
        conn.commit()


def load_chats_for_bot(bot_name: str) -> List[Dict[str, Any]]:
    """
    Load all stored chats for a given bot.

    Args:
        bot_name (str): The name of the bot.

    Returns:
        List[Dict[str, Any]]: A list of chat records as dictionaries.
    """
    sql = """
    SELECT
        chat_id,
        chat_type,
        title,
        username,
        first_seen_at,
        last_seen_at,
        last_message_text,
        last_message_date,
        message_count,
        is_blocked
    FROM bot_chats
    WHERE bot_name = %s
    ORDER BY last_seen_at DESC;
    """
    with get_conn() as conn, conn.cursor(
        cursor_factory=psycopg2.extras.DictCursor
    ) as cur:
        cur.execute(sql, (bot_name,))
        rows = cur.fetchall()

    return [dict(r) for r in rows]
