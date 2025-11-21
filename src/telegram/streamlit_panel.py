from __future__ import annotations

from pathlib import Path
from typing import Dict, Optional

from .panel.environment import load_environment, load_telegram_ids
from .panel.ui_layout import render_panel
from .db import init_db   # ✅ استيراد init_db


def run_panel(env_path: Path) -> None:
    """
    Run the Streamlit interface for a single Telegram bot using the specified .env file.
    """

    # 1) تحميل ملف .env
    load_environment(env_path)

    # 2) تهيئة قاعدة البيانات (إنشاء الجداول إذا لم تكن موجودة) ✅
    init_db()

    # 3) قراءة TELEGRAM_*_ID
    telegram_ids: Dict[str, str] = load_telegram_ids()

    # 4) دالة تحديد الهدف النهائي
    def resolve_target(target_key: str, custom_id: Optional[str]) -> Optional[str]:
        if target_key == "CUSTOM":
            return custom_id or None
        return telegram_ids.get(target_key)

    # 5) رسم الواجهة
    render_panel(telegram_ids, resolve_target)
