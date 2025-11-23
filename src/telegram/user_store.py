from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Optional, Dict, Any

from telegram import User, Chat

# Path to the database: /data/telegram_users.db
DB_PATH = Path(__file__).resolve().parents[2] / "data" / "telegram_users.db"


def _get_connection() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db() -> None:
    """Create necessary tables if they do not exist."""
    with _get_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS telegram_users (
                telegram_id INTEGER PRIMARY KEY,
                chat_id     INTEGER,
                username    TEXT,
                full_name   TEXT,
                first_seen  TEXT DEFAULT CURRENT_TIMESTAMP,
                last_seen   TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS gmail_accounts (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id     INTEGER NOT NULL,
                gmail_address   TEXT,
                access_token    TEXT,
                refresh_token   TEXT,
                token_expiry    TEXT,
                token_uri       TEXT,
                client_id       TEXT,
                client_secret   TEXT,
                scopes          TEXT,
                UNIQUE(telegram_id),
                FOREIGN KEY (telegram_id) REFERENCES telegram_users(telegram_id)
            )
            """
        )


def upsert_telegram_user(user: User, chat: Chat) -> None:
    """Insert or update a Telegram user based on their ID."""
    with _get_connection() as conn:
        conn.execute(
            """
            INSERT INTO telegram_users (telegram_id, chat_id, username, full_name)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(telegram_id) DO UPDATE SET
                chat_id   = excluded.chat_id,
                username  = excluded.username,
                full_name = excluded.full_name,
                last_seen = CURRENT_TIMESTAMP
            """,
            (
                user.id,
                chat.id,
                user.username,
                user.full_name,
            ),
        )


def save_gmail_credentials(telegram_id: int, gmail_address: str, creds_dict: Dict[str, Any]) -> None:
    """
    Save Gmail OAuth credentials for a specific user.
    creds_dict should be equivalent to google.oauth2.credentials.Credentials.to_json().
    """
    with _get_connection() as conn:
        conn.execute(
            """
            INSERT INTO gmail_accounts (
                telegram_id,
                gmail_address,
                access_token,
                refresh_token,
                token_expiry,
                token_uri,
                client_id,
                client_secret,
                scopes
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(telegram_id) DO UPDATE SET
                gmail_address = excluded.gmail_address,
                access_token  = excluded.access_token,
                refresh_token = excluded.refresh_token,
                token_expiry  = excluded.token_expiry,
                token_uri     = excluded.token_uri,
                client_id     = excluded.client_id,
                client_secret = excluded.client_secret,
                scopes        = excluded.scopes
            """,
            (
                telegram_id,
                gmail_address,
                creds_dict.get("token"),
                creds_dict.get("refresh_token"),
                str(creds_dict.get("expiry")),
                creds_dict.get("token_uri"),
                creds_dict.get("client_id"),
                creds_dict.get("client_secret"),
                " ".join(creds_dict.get("scopes", [])),
            ),
        )


def get_gmail_credentials_row(telegram_id: int) -> Optional[Dict[str, Any]]:
    """Retrieve Gmail credentials for a specific Telegram user."""
    with _get_connection() as conn:
        cur = conn.execute(
            """
            SELECT gmail_address, access_token, refresh_token, token_expiry,
                   token_uri, client_id, client_secret, scopes
            FROM gmail_accounts
            WHERE telegram_id = ?
            """,
            (telegram_id,),
        )
        row = cur.fetchone()

    if not row:
        return None

    (
        gmail_address, access_token, refresh_token, token_expiry,
        token_uri, client_id, client_secret, scopes
    ) = row

    return {
        "gmail_address": gmail_address,
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_expiry": token_expiry,
        "token_uri": token_uri,
        "client_id": client_id,
        "client_secret": client_secret,
        "scopes": scopes.split() if scopes else [],
    }
