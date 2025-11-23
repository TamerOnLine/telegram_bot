from __future__ import annotations

import os
from typing import Optional, List

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
    KeyboardButton,
)
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
)

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

from src.telegram.user_store import get_gmail_credentials_row

# ======================
# General Configuration
# ======================

# Base URL for the OAuth server (should match the one in oauth_server.py)
GMAIL_OAUTH_BASE_URL = os.getenv("GMAIL_OAUTH_BASE_URL", "http://localhost:8001")

# ======================
# Bot Command Handlers
# ======================

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Sends a welcome message with a command keyboard.
    """
    msg = update.effective_message

    text = (
        "Gmail Bot on Telegram\n\n"
        "This bot connects to your Gmail account using OAuth.\n\n"
        "Available commands:\n"
        "\u2022 /link_gmail  to link your Gmail account.\n"
        "\u2022 /gmail       to view your latest inbox messages.\n\n"
        "Note: Ensure the OAuth server is running on your machine."
    )

    keyboard = ReplyKeyboardMarkup(
        [[KeyboardButton("/link_gmail"), KeyboardButton("/gmail")]],
        resize_keyboard=True,
        one_time_keyboard=False,
    )

    await msg.reply_text(text, reply_markup=keyboard)


async def cmd_link_gmail(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Initiates the Gmail linking process for a Telegram user.
    Sends a button with the OAuth URL containing the telegram_id.
    """
    user = update.effective_user
    msg = update.effective_message

    if not user:
        await msg.reply_text("Unable to identify the user.")
        return

    telegram_id = user.id

    base = GMAIL_OAUTH_BASE_URL.rstrip("/")
    auth_url = f"{base}/oauth/start?telegram_id={telegram_id}"

    text = (
        "Link your Gmail account (Local Setup)\n\n"
        "1. Ensure the OAuth server is running.\n"
        "2. Click the button below or open the URL in a browser on the same machine:\n\n"
        f"{auth_url}\n\n"
        "3. Once linked successfully, return here and type /gmail to read your emails."
    )

    keyboard = InlineKeyboardMarkup(
        [[InlineKeyboardButton("Open Gmail Link Page", url=auth_url)]]
    )

    await msg.reply_text(text, reply_markup=keyboard)


# ======================
# Gmail Credential Handling
# ======================

def _build_user_credentials(telegram_id: int) -> Optional[Credentials]:
    """
    Rebuilds Gmail Credentials from the stored database values.

    Args:
        telegram_id (int): Telegram user ID.

    Returns:
        Optional[Credentials]: OAuth2 credentials or None if invalid/missing.
    """
    row = get_gmail_credentials_row(telegram_id)
    if not row:
        return None

    if not row["access_token"] or not row["refresh_token"]:
        return None

    scopes_raw = row.get("scopes") or ""
    if isinstance(scopes_raw, str):
        scopes: List[str] = [
            s for s in scopes_raw.replace(",", " ").split() if s.strip()
        ]
    else:
        scopes = ["https://www.googleapis.com/auth/gmail.readonly"]

    creds = Credentials(
        token=row["access_token"],
        refresh_token=row["refresh_token"],
        token_uri=row["token_uri"],
        client_id=row["client_id"],
        client_secret=row["client_secret"],
        scopes=scopes,
    )
    return creds


async def cmd_gmail(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Displays the latest 5 Gmail messages for a user with linked credentials.
    """
    user = update.effective_user
    msg = update.effective_message

    if not user:
        await msg.reply_text("Unable to identify the user.")
        return

    telegram_id = user.id
    creds = _build_user_credentials(telegram_id)

    if not creds:
        await msg.reply_text(
            "No Gmail account is linked to this user.\n"
            "Use the /link_gmail command to link your account."
        )
        return

    try:
        service = build("gmail", "v1", credentials=creds)

        result = (
            service.users()
            .messages()
            .list(userId="me", maxResults=5, labelIds=["INBOX"])
            .execute()
        )
        messages = result.get("messages", [])
    except Exception as exc:
        await msg.reply_text(f"An error occurred while connecting to Gmail:\n{exc}")
        return

    if not messages:
        await msg.reply_text("No recent messages in your inbox.")
        return

    lines: list[str] = ["Latest 5 messages in your inbox:\n"]

    for m in messages:
        full = (
            service.users()
            .messages()
            .get(
                userId="me",
                id=m["id"],
                format="metadata",
                metadataHeaders=["Subject", "From"],
            )
            .execute()
        )
        headers = {
            h["name"]: h["value"]
            for h in full.get("payload", {}).get("headers", [])
        }
        subject = headers.get("Subject", "(No Subject)")
        sender = headers.get("From", "(Unknown Sender)")
        lines.append(f"\u2022 {subject}\n  From: {sender}\n")

    await msg.reply_text("\n".join(lines))


# ======================
# Registering Handlers
# ======================

def register_handlers(app: Application) -> None:
    """
    Register Gmail command handlers with the bot application.

    Args:
        app (Application): Telegram bot application instance.
    """
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("link_gmail", cmd_link_gmail))
    app.add_handler(CommandHandler("gmail", cmd_gmail))