# apps/dashboard/helpers/database_api.py
from __future__ import annotations

from typing import Any, Dict, List

from apps.dashboard.helpers.paths import ensure_project_root_on_sys_path

# نضمن وجود جذر المشروع على sys.path
ensure_project_root_on_sys_path()

from core.db import (  # type: ignore  # مسار داخل مشروعك
    load_chats_for_bot as _load_chats_for_bot,
    delete_chat as _delete_chat,
    delete_chats_for_bot as _delete_chats_for_bot,
)


def get_chats_for_bot(bot_name: str) -> List[Dict[str, Any]]:
    """جلب المحادثات من جدول bot_chats لبوت معيّن."""
    return _load_chats_for_bot(bot_name)


def delete_single_chat(bot_name: str, chat_id: int) -> None:
    """حذف محادثة واحدة."""
    _delete_chat(bot_name, chat_id)


def delete_all_chats(bot_name: str) -> None:
    """حذف كل سجلات المحادثات لهذا البوت."""
    _delete_chats_for_bot(bot_name)
