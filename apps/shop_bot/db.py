from __future__ import annotations
import psycopg2
from psycopg2.extras import RealDictCursor
from pathlib import Path
import os
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
ENV_PATH = BASE_DIR / ".env"

load_dotenv(ENV_PATH)   # تحميل بيئة البوت الخاصة به فقط

PG_DSN = os.getenv("PG_DSN")
if not PG_DSN:
    raise SystemExit("PG_DSN is missing in .env for shop_bot")

def get_conn():
    return psycopg2.connect(PG_DSN)

def init_db():
    """إنشاء الجداول الخاصة بالـ shop_bot إن لم تكن موجودة."""
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute("""
        CREATE TABLE IF NOT EXISTS shop_orders (
            id SERIAL PRIMARY KEY,
            user_id BIGINT NOT NULL,
            username TEXT,
            full_name TEXT,
            details TEXT NOT NULL,
            total NUMERIC(10,2) NOT NULL,
            created_at TIMESTAMP DEFAULT NOW()
        );
        """)
        conn.commit()

def save_order(user_id: int, username: str, full_name: str, details: str, total: float):
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute("""
            INSERT INTO shop_orders (user_id, username, full_name, details, total)
            VALUES (%s, %s, %s, %s, %s)
        """, (user_id, username, full_name, details, total))
        conn.commit()

def list_orders():
    with get_conn() as conn, conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("SELECT * FROM shop_orders ORDER BY created_at DESC")
        return cur.fetchall()
