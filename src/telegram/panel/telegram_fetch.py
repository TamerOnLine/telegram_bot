from __future__ import annotations

import os
from typing import Any, Dict, List, Optional, Tuple

import requests
from dotenv import load_dotenv

# Load environment variables (as used across the project)
load_dotenv()


# =====================
#  HELPERS
# =====================

def _build_api_url() -> Tuple[bool, Optional[str], Optional[str]]:
    """
    Builds the Telegram Bot API URL based on TELEGRAM_BOT_TOKEN.

    Returns:
        Tuple of (status, error message, API URL)
    """
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        return False, "TELEGRAM_BOT_TOKEN is missing.", None
    return True, None, f"https://api.telegram.org/bot{token}"


def _extract_chat_from_update(update: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Extracts the chat dictionary from a Telegram update.

    Args:
        update (Dict[str, Any]): Telegram update object.

    Returns:
        Optional[Dict[str, Any]]: Extracted chat dictionary if found, else None.
    """
    if "message" in update and "chat" in update["message"]:
        return update["message"]["chat"]

    if "edited_message" in update and "chat" in update["edited_message"]:
        return update["edited_message"]["chat"]

    if "channel_post" in update and "chat" in update["channel_post"]:
        return update["channel_post"]["chat"]

    if "edited_channel_post" in update and "chat" in update["edited_channel_post"]:
        return update["edited_channel_post"]["chat"]

    if "my_chat_member" in update and "chat" in update["my_chat_member"]:
        return update["my_chat_member"]["chat"]

    return None


# =====================
#  UNIQUE CHATS
# =====================

def get_unique_chats() -> Tuple[bool, Optional[str], List[Dict[str, Any]]]:
    """
    Retrieves a list of all unique users/channels/groups that have
    communicated with the bot at least once via getUpdates.

    Returns:
        Tuple of (status, error message, list of unique chat dictionaries)
    """
    ok, err, api_url = _build_api_url()
    if not ok or not api_url:
        return False, err, []

    try:
        resp = requests.get(f"{api_url}/getUpdates", timeout=15)
        data = resp.json()
    except Exception as e:
        return False, f"Network error in getUpdates: {e}", []

    if not data.get("ok"):
        return False, f"Telegram Error in getUpdates: {data}", []

    updates = data.get("result", [])
    if not updates:
        return True, None, []

    seen_ids: set[int] = set()
    chats: List[Dict[str, Any]] = []

    for upd in updates:
        chat = _extract_chat_from_update(upd)
        if not chat:
            continue

        cid = chat.get("id")
        if cid in seen_ids:
            continue

        seen_ids.add(cid)

        chats.append(
            {
                "id": cid,
                "type": chat.get("type"),
                "title": chat.get("title"),
                "username": chat.get("username"),
                "first_name": chat.get("first_name"),
                "last_name": chat.get("last_name"),
            }
        )

    return True, None, chats
