from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Optional, Dict, Any

DB_PATH = Path("/home/tamer/telegram_bot/users.db")


def init_db() -> None:
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS gmail_tokens (
            telegram_id INTEGER PRIMARY KEY,
            email TEXT,
            access_token TEXT,
            refresh_token TEXT,
            token_uri TEXT,
            client_id TEXT,
            client_secret TEXT,
            scopes TEXT
        )
        """
    )
    conn.commit()
    conn.close()


def save_gmail_credentials(
    telegram_id: int,
    creds,
    email: Optional[str],
) -> None:
    scopes = " ".join(creds.scopes or [])

    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        """
        INSERT INTO gmail_tokens (
            telegram_id, email,
            access_token, refresh_token,
            token_uri, client_id, client_secret,
            scopes
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(telegram_id) DO UPDATE SET
            email = excluded.email,
            access_token = excluded.access_token,
            refresh_token = excluded.refresh_token,
            token_uri = excluded.token_uri,
            client_id = excluded.client_id,
            client_secret = excluded.client_secret,
            scopes = excluded.scopes
        """,
        (
            telegram_id,
            email,
            creds.token,
            creds.refresh_token,
            creds.token_uri,
            creds.client_id,
            creds.client_secret,
            scopes,
        ),
    )
    conn.commit()
    conn.close()


def get_gmail_credentials_row(telegram_id: int) -> Optional[Dict[str, Any]]:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.execute(
        "SELECT * FROM gmail_tokens WHERE telegram_id = ?",
        (telegram_id,),
    )
    row = cur.fetchone()
    conn.close()

    if not row:
        return None

    cols = [
        "telegram_id",
        "email",
        "access_token",
        "refresh_token",
        "token_uri",
        "client_id",
        "client_secret",
        "scopes",
    ]
    return dict(zip(cols, row))
