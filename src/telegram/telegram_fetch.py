from __future__ import annotations

import os
from typing import Any, Dict, List, Optional, Tuple

import requests
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# =====================
#  HELPERS
# =====================

def _build_api_url() -> Tuple[bool, Optional[str], Optional[str]]:
    """
    Build the Telegram Bot API URL based on TELEGRAM_BOT_TOKEN.

    Returns:
        Tuple: (success flag, error message, API URL if successful)
    """
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        return False, "TELEGRAM_BOT_TOKEN is missing.", None
    return True, None, f"https://api.telegram.org/bot{token}"


def _extract_chat_from_update(update: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Extract the chat dictionary from a Telegram update object.

    Args:
        update (Dict[str, Any]): A single update from getUpdates.

    Returns:
        Optional[Dict[str, Any]]: The chat object if found, else None.
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
#  getMe
# =====================

def get_bot_info() -> Tuple[bool, Optional[str], Optional[Dict[str, Any]]]:
    """
    Perform a getMe request to the Telegram Bot API.

    Returns:
        Tuple: (success flag, error message, bot info dict if successful)
    """
    ok, err, api_url = _build_api_url()
    if not ok or not api_url:
        return False, err, None

    try:
        resp = requests.get(f"{api_url}/getMe", timeout=10)
        data = resp.json()
    except Exception as e:
        return False, f"Network error in getMe: {e}", None

    if not data.get("ok"):
        return False, f"Telegram Error in getMe: {data}", None

    return True, None, data.get("result")

# =====================
#  getUpdates → last chat
# =====================

def get_last_chat() -> Tuple[
    bool,
    Optional[str],
    Optional[Dict[str, Any]],
    Optional[Dict[str, Any]],
]:
    """
    Retrieve the last update from getUpdates and extract its chat.

    Returns:
        Tuple: (success flag, error message, chat dict if found, last update dict)
    """
    ok, err, api_url = _build_api_url()
    if not ok or not api_url:
        return False, err, None, None

    try:
        resp = requests.get(f"{api_url}/getUpdates", timeout=15)
        data = resp.json()
    except Exception as e:
        return False, f"Network error in getUpdates: {e}", None, None

    if not data.get("ok"):
        return False, f"Telegram Error in getUpdates: {data}", None, None

    updates = data.get("result", [])
    if not updates:
        return False, "No updates found. Send a message to the bot first.", None, None

    chat: Optional[Dict[str, Any]] = None
    last_update: Optional[Dict[str, Any]] = None

    for upd in reversed(updates):
        chat = _extract_chat_from_update(upd)
        if chat:
            last_update = upd
            break

    if not chat:
        return False, "Could not extract chat from the last update.", None, last_update

    return True, None, chat, last_update

# =====================
#  Unique Chats List
# =====================

def get_unique_chats() -> Tuple[bool, Optional[str], List[Dict[str, Any]]]:
    """
    Retrieve a list of all unique users/channels/groups that have contacted the bot at least once.

    Returns:
        Tuple: (success flag, error message, list of unique chat dictionaries)
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