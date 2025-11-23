from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, List

from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

from src.telegram.panel.environment import load_environment
from src.telegram.db import upsert_user_from_chat, add_message

# =====================
# General Configuration
# =====================

BOT_PROFILE: str = "quran"  # Will be updated from .env inside run_bot

UserState = Dict[str, Any]
user_states: Dict[int, UserState] = {}


def get_user_state(user_id: int) -> UserState:
    """
    Return or initialize the state of a specific user.

    Args:
        user_id (int): Telegram user ID.

    Returns:
        UserState: A dictionary holding the user's current state.
    """
    if user_id not in user_states:
        user_states[user_id] = {
            "surah": "Al-Fatiha",
            "verse_index": 1,
            "chunk": 1,
        }
    return user_states[user_id]


SURAH_BUTTONS: List[List[str]] = [
    ["Al-Fatiha", "Al-Baqarah"],
    ["Aal-E-Imran", "An-Nisa"],
]

# =====================
# Logging to Database
# =====================

def _log_incoming(update: Update) -> None:
    msg = update.effective_message
    chat = msg.chat

    try:
        chat_id = int(chat.id)
    except Exception:
        return

    text = msg.text or msg.caption or ""
    upsert_user_from_chat(chat, bot_profile=BOT_PROFILE)
    add_message(chat_id, "in", text, bot_profile=BOT_PROFILE)


def _log_outgoing(chat_id: int | str, text: str) -> None:
    try:
        db_chat_id = int(str(chat_id))
    except Exception:
        return
    add_message(db_chat_id, "out", text, bot_profile=BOT_PROFILE)

# =====================
# Bot Command Handlers
# =====================

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    _log_incoming(update)
    msg = update.effective_message
    chat_id = msg.chat_id

    keyboard = ReplyKeyboardMarkup(SURAH_BUTTONS, resize_keyboard=True)

    text = (
        "Welcome to the Quran Memorization Bot\n\n"
        "Available commands:\n"
        "/setsurah — Choose a Surah\n"
        "/setchunk — Set number of verses per batch\n"
        "/next — Show next verses\n"
        "/repeat — Repeat last batch\n"
        "/progress — Show progress\n\n"
        "Please choose a Surah from the buttons below to begin."
    )

    await msg.reply_text(text, reply_markup=keyboard, parse_mode="Markdown")
    _log_outgoing(chat_id, text)


async def cmd_setsurah(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    _log_incoming(update)
    msg = update.effective_message
    chat_id = msg.chat_id
    user_id = msg.from_user.id

    args = context.args
    surah = " ".join(args) if args else None

    if not surah:
        text = (
            "Usage: `/setsurah Al-Fatiha`\n"
            "Or select a Surah from the keyboard below."
        )
        await msg.reply_text(text, parse_mode="Markdown")
        _log_outgoing(chat_id, text)
        return

    state = get_user_state(user_id)
    state["surah"] = surah
    state["verse_index"] = 1

    text = f"Surah *{surah}* selected. Use `/next` to begin."
    await msg.reply_text(text, parse_mode="Markdown")
    _log_outgoing(chat_id, text)


async def cmd_setchunk(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    _log_incoming(update)
    msg = update.effective_message
    chat_id = msg.chat_id
    user_id = msg.from_user.id

    if not context.args or not context.args[0].isdigit():
        text = "Usage: `/setchunk 3` (e.g., 3 verses per batch)."
        await msg.reply_text(text, parse_mode="Markdown")
        _log_outgoing(chat_id, text)
        return

    chunk = max(1, int(context.args[0]))
    state = get_user_state(user_id)
    state["chunk"] = chunk

    text = f"Chunk size set to: *{chunk}* verses per batch."
    await msg.reply_text(text, parse_mode="Markdown")
    _log_outgoing(chat_id, text)


async def cmd_next(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    _log_incoming(update)
    msg = update.effective_message
    chat_id = msg.chat_id
    user_id = msg.from_user.id

    state = get_user_state(user_id)
    surah = state["surah"]
    verse_index = state["verse_index"]
    chunk = state["chunk"]

    start = verse_index
    end = verse_index + chunk - 1
    state["verse_index"] = end + 1

    text = (
        f"*Surah {surah}* (Sample Data)\n"
        f"Verses {start} to {end}\n\n"
        "This will later be linked to actual Quran text."
    )

    await msg.reply_text(text, parse_mode="Markdown")
    _log_outgoing(chat_id, text)


async def cmd_repeat(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    _log_incoming(update)
    msg = update.effective_message
    chat_id = msg.chat_id
    user_id = msg.from_user.id

    state = get_user_state(user_id)
    surah = state["surah"]
    chunk = state["chunk"]
    current = state["verse_index"]

    start = max(1, current - chunk)
    end = current - 1 if current > 1 else 1

    text = f"*Repeat* Surah {surah}\nVerses {start} to {end}"
    await msg.reply_text(text, parse_mode="Markdown")
    _log_outgoing(chat_id, text)


async def cmd_progress(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    _log_incoming(update)
    msg = update.effective_message
    chat_id = msg.chat_id
    user_id = msg.from_user.id

    state = get_user_state(user_id)
    surah = state["surah"]
    verse_index = state["verse_index"]
    chunk = state["chunk"]

    text = (
        "*Your Current Progress:*\n"
        f"- Surah: {surah}\n"
        f"- Approximate Verse: {verse_index}\n"
        f"- Chunk Size: {chunk}"
    )

    await msg.reply_text(text, parse_mode="Markdown")
    _log_outgoing(chat_id, text)


async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    _log_incoming(update)
    msg = update.effective_message
    chat_id = msg.chat_id
    user_id = msg.from_user.id
    text = (msg.text or "").strip()

    flat_buttons = [name for row in SURAH_BUTTONS for name in row]
    if text in flat_buttons:
        state = get_user_state(user_id)
        state["surah"] = text
        state["verse_index"] = 1

        reply = f"Surah *{text}* selected. Use `/next` to begin."
        await msg.reply_text(reply, parse_mode="Markdown")
        _log_outgoing(chat_id, reply)
        return

    reply = (
        "Use the buttons to select a Surah or commands: /setsurah /setchunk /next /repeat /progress"
    )
    await msg.reply_text(reply)
    _log_outgoing(chat_id, reply)


# =====================
# Application Launcher
# =====================

def build_application(token: str) -> Application:
    app = Application.builder().token(token).build()

    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("setsurah", cmd_setsurah))
    app.add_handler(CommandHandler("setchunk", cmd_setchunk))
    app.add_handler(CommandHandler("next", cmd_next))
    app.add_handler(CommandHandler("repeat", cmd_repeat))
    app.add_handler(CommandHandler("progress", cmd_progress))

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))

    return app


def run_bot(env_path: Path) -> None:
    """
    Entry point for running the bot.

    - Loads .env file.
    - Reads BOT_PROFILE and TELEGRAM_BOT_TOKEN.
    - Starts the bot with polling.

    Args:
        env_path (Path): Path to the .env configuration file.
    """
    load_environment(env_path)

    global BOT_PROFILE
    BOT_PROFILE = os.getenv("BOT_PROFILE", BOT_PROFILE)

    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        print(f"Missing TELEGRAM_BOT_TOKEN in .env: {env_path}")
        return

    print(f"Quran Bot starting... env={env_path}, profile={BOT_PROFILE}")
    app = build_application(token)
    app.run_polling()