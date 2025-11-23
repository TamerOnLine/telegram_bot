from __future__ import annotations

import os
from typing import Any, Dict, List, Optional

import requests
from dotenv import load_dotenv

# Attempt to load any existing .env file (e.g., at the root level)
# Applications with specific .env paths should call load_dotenv(dotenv_path=...) beforehand.
load_dotenv()


# ========= Internal Utilities =========

def _get_token() -> Optional[str]:
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        print("TELEGRAM_BOT_TOKEN is missing in environment.")
        return None
    return token


def _post(
    method: str,
    payload: Optional[Dict[str, Any]] = None,
    files: Optional[Dict[str, Any]] = None,
    timeout: int = 30,
) -> Optional[Dict[str, Any]]:
    """
    Call any Telegram Bot API method via POST.
    The token is fetched dynamically from the environment each time.
    """
    token = _get_token()
    if not token:
        return None

    api_url = f"https://api.telegram.org/bot{token}"
    url = f"{api_url}/{method}"

    try:
        resp = requests.post(url, data=payload, files=files, timeout=timeout)
    except Exception as e:
        print(f"Telegram network error in {method}: {e}")
        return None

    try:
        data = resp.json()
    except Exception:
        print(f"RAW RESPONSE from {method}:", resp.text)
        return None

    if not data.get("ok"):
        print(f"Telegram error in {method}:", data)
        return None

    return data


def _get_me_id() -> Optional[str]:
    me_id = os.getenv("TELEGRAM_ME_ID")
    if not me_id:
        print("TELEGRAM_ME_ID is missing in environment.")
        return None
    return me_id


def _get_channel_id() -> Optional[str]:
    cid = os.getenv("TELEGRAM_CHANNEL_ID")
    if not cid:
        print("TELEGRAM_CHANNEL_ID is missing in environment.")
        return None
    return cid


def _get_group_id() -> Optional[str]:
    gid = os.getenv("TELEGRAM_GROUP_ID")
    if not gid:
        print("TELEGRAM_GROUP_ID is missing in environment.")
        return None
    return gid


# =========================
#  TEXT MESSAGES
# =========================

def send_text(
    chat_id: int | str,
    text: str,
    parse_mode: Optional[str] = None,
    reply_to_message_id: Optional[int] = None,
    disable_web_page_preview: Optional[bool] = None,
) -> Optional[Dict[str, Any]]:
    payload: Dict[str, Any] = {
        "chat_id": chat_id,
        "text": text,
    }
    if parse_mode:
        payload["parse_mode"] = parse_mode
    if reply_to_message_id:
        payload["reply_to_message_id"] = reply_to_message_id
    if disable_web_page_preview is not None:
        payload["disable_web_page_preview"] = disable_web_page_preview

    return _post("sendMessage", payload)


def send_markdown(
    chat_id: int | str,
    text: str,
    reply_to_message_id: Optional[int] = None,
) -> Optional[Dict[str, Any]]:
    return send_text(chat_id, text, parse_mode="Markdown", reply_to_message_id=reply_to_message_id)


def send_html(
    chat_id: int | str,
    text: str,
    reply_to_message_id: Optional[int] = None,
) -> Optional[Dict[str, Any]]:
    return send_text(chat_id, text, parse_mode="HTML", reply_to_message_id=reply_to_message_id)


# =========================
#  SHORTCUTS (ME / CHANNEL / GROUP)
# =========================

def send_to_me(text: str) -> Optional[Dict[str, Any]]:
    me_id = _get_me_id()
    if not me_id:
        return None
    return send_text(me_id, text)


def send_to_channel(text: str) -> Optional[Dict[str, Any]]:
    cid = _get_channel_id()
    if not cid:
        return None
    return send_text(cid, text)


def send_to_group(text: str) -> Optional[Dict[str, Any]]:
    gid = _get_group_id()
    if not gid:
        return None
    return send_text(gid, text)


def broadcast(chat_ids: List[int | str], text: str) -> List[Optional[Dict[str, Any]]]:
    results: List[Optional[Dict[str, Any]]] = []
    for cid in chat_ids:
        results.append(send_text(cid, text))
    return results


# =========================
#  IMAGES & FILES
# =========================

def send_photo(
    chat_id: int | str,
    photo_path: str,
    caption: str = "",
    parse_mode: Optional[str] = None,
    reply_to_message_id: Optional[int] = None,
) -> Optional[Dict[str, Any]]:
    with open(photo_path, "rb") as f:
        files = {"photo": f}
        payload: Dict[str, Any] = {"chat_id": chat_id, "caption": caption}
        if parse_mode:
            payload["parse_mode"] = parse_mode
        if reply_to_message_id:
            payload["reply_to_message_id"] = reply_to_message_id
        return _post("sendPhoto", payload, files=files)


def send_document(
    chat_id: int | str,
    document_path: str,
    caption: str = "",
    parse_mode: Optional[str] = None,
    reply_to_message_id: Optional[int] = None,
) -> Optional[Dict[str, Any]]:
    with open(document_path, "rb") as f:
        files = {"document": f}
        payload: Dict[str, Any] = {"chat_id": chat_id, "caption": caption}
        if parse_mode:
            payload["parse_mode"] = parse_mode
        if reply_to_message_id:
            payload["reply_to_message_id"] = reply_to_message_id
        return _post("sendDocument", payload, files=files)


def send_voice(
    chat_id: int | str,
    voice_path: str,
    caption: str = "",
    reply_to_message_id: Optional[int] = None,
) -> Optional[Dict[str, Any]]:
    with open(voice_path, "rb") as f:
        files = {"voice": f}
        payload: Dict[str, Any] = {"chat_id": chat_id, "caption": caption}
        if reply_to_message_id:
            payload["reply_to_message_id"] = reply_to_message_id
        return _post("sendVoice", payload, files=files)


def send_video(
    chat_id: int | str,
    video_path: str,
    caption: str = "",
    supports_streaming: bool = True,
    reply_to_message_id: Optional[int] = None,
) -> Optional[Dict[str, Any]]:
    with open(video_path, "rb") as f:
        files = {"video": f}
        payload: Dict[str, Any] = {
            "chat_id": chat_id,
            "caption": caption,
            "supports_streaming": supports_streaming,
        }
        if reply_to_message_id:
            payload["reply_to_message_id"] = reply_to_message_id
        return _post("sendVideo", payload, files=files)


# =========================
#  EDIT / DELETE / PIN
# =========================

def edit_message_text(
    chat_id: int | str,
    message_id: int,
    new_text: str,
    parse_mode: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    payload: Dict[str, Any] = {
        "chat_id": chat_id,
        "message_id": message_id,
        "text": new_text,
    }
    if parse_mode:
        payload["parse_mode"] = parse_mode
    return _post("editMessageText", payload)


def delete_message(chat_id: int | str, message_id: int) -> Optional[Dict[str, Any]]:
    payload = {"chat_id": chat_id, "message_id": message_id}
    return _post("deleteMessage", payload)


def pin_message(
    chat_id: int | str,
    message_id: int,
    disable_notification: bool = False,
) -> Optional[Dict[str, Any]]:
    payload = {
        "chat_id": chat_id,
        "message_id": message_id,
        "disable_notification": disable_notification,
    }
    return _post("pinChatMessage", payload)


def unpin_message(
    chat_id: int | str,
    message_id: Optional[int] = None,
) -> Optional[Dict[str, Any]]:
    payload: Dict[str, Any] = {"chat_id": chat_id}
    if message_id is not None:
        payload["message_id"] = message_id
    return _post("unpinChatMessage", payload)


# =========================
#  ERROR ALERTS
# =========================

def send_error_alert(message: str) -> Optional[Dict[str, Any]]:
    """
    Send an error alert to TELEGRAM_ME_ID (your personal Telegram ID).
    """
    me_id = _get_me_id()
    if not me_id:
        return None
    text = f"ERROR ALERT:\n{message}"
    return send_text(me_id, text)


# ============================================================
# Legacy / test IDs (needed by tests.test_pro_features)
# ============================================================