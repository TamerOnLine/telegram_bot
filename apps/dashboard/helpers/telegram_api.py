# apps/dashboard/helpers/telegram_api.py
from __future__ import annotations

import json
from typing import Dict, List, Tuple

import requests


def send_message(
    token: str,
    chat_id: str,
    text: str,
) -> Tuple[bool, str]:
    """
    يرسل رسالة عبر Telegram HTTP API.
    يرجع (success, message).
    """
    if not token:
        return False, "❌ لا يوجد TELEGRAM_BOT_TOKEN في ملف .env لهذا البوت."

    url = f"https://api.telegram.org/bot{token}/sendMessage"

    try:
        resp = requests.post(
            url,
            data={
                "chat_id": chat_id.strip(),
                "text": text,
            },
            timeout=15,
        )
    except Exception as exc:  # noqa: BLE001
        return False, f"❌ خطأ في الاتصال بواجهة Telegram API: {exc}"

    try:
        data = resp.json()
    except json.JSONDecodeError:
        return (
            False,
            f"❌ استجابة غير مفهومة من Telegram (status={resp.status_code}).",
        )

    if not data.get("ok"):
        return False, f"❌ Telegram error: {data.get('description', 'Unknown error')}"

    return True, "✅ تم إرسال الرسالة."


def fetch_chats_from_updates(
    token: str,
) -> Tuple[bool, str | List[Dict[str, str]]]:
    """
    يجلب آخر التحديثات من Telegram ويستخرج قائمة بالشاتات.
    تحذير: يستخدم getUpdates (قد يتعارض مع run_polling لو البوت شغال بنفس التوكن).
    """
    if not token:
        return False, "❌ لا يوجد TELEGRAM_BOT_TOKEN في ملف .env لهذا البوت."

    url = f"https://api.telegram.org/bot{token}/getUpdates"

    try:
        resp = requests.get(url, timeout=15)
    except Exception as exc:  # noqa: BLE001
        return False, f"❌ خطأ في الاتصال بواجهة Telegram API: {exc}"

    try:
        data = resp.json()
    except json.JSONDecodeError:
        return (
            False,
            f"❌ استجابة غير مفهومة من Telegram (status={resp.status_code}).",
        )

    if not data.get("ok"):
        return False, f"❌ Telegram error: {data.get('description', 'Unknown error')}"

    results = data.get("result", [])
    chats: Dict[int, Dict[str, str]] = {}

    for update in results:
        msg = (
            update.get("message")
            or update.get("edited_message")
            or update.get("channel_post")
            or update.get("edited_channel_post")
        )
        if not msg:
            continue

        chat = msg.get("chat", {})
        chat_id = chat.get("id")
        if chat_id is None:
            continue

        chat_type = chat.get("type", "unknown")
        title = (
            chat.get("title")
            or chat.get("username")
            or f"{chat.get('first_name', '')} {chat.get('last_name', '')}".strip()
            or "—"
        )

        chats[chat_id] = {
            "chat_id": str(chat_id),
            "type": chat_type,
            "title_or_username": title,
        }

    if not chats:
        return False, (
            "لم أجد أي محادثات في getUpdates.\n"
            "تأكد أنك أرسلت /start أو رسالة للبوت، ثم أعد المحاولة."
        )

    return True, list(chats.values())
