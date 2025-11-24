from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Final

import requests
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from core.env import load_env, get_env
from core.logging import setup_logging

BASE_DIR = Path(__file__).resolve().parent
ENV_PATH = BASE_DIR / ".env"

logger = logging.getLogger(__name__)

ARABIC_RE = re.compile(r"[\u0600-\u06FF]")

TOPIC_NAME: Final[str] = "Pi Network"
TOPIC_DESCRIPTION: Final[str] = (
    "A bot specialized in retrieving summaries about Pi Network from Wikipedia."
)
BOT_LANG: Final[str] = "ar"
WIKI_DEFAULT_LANG: Final[str] = "ar"
FORCE_TOPIC_IN_QUERY: Final[bool] = True


def get_start_message() -> str:
    if BOT_LANG == "ar":
        return (
            f"Welcome to the *{TOPIC_NAME}* search bot.\n\n"
            "Send your question or use:\n"
            "• `/search your question here`\n\n"
            "I will try to fetch a summary from Wikipedia related to this topic."
        )
    return (
        f"Welcome to the *{TOPIC_NAME}* search bot.\n\n"
        "Send your question or use:\n"
        "• `/search your question here`\n\n"
        "I will try to fetch a summary from Wikipedia related to this topic."
    )


def get_help_message() -> str:
    if BOT_LANG == "ar":
        return (
            "*How to use the bot:*\n\n"
            f"- This bot is specialized in: *{TOPIC_NAME}*\n"
            "- Send your question directly, or use:\n"
            "  `/search your question here`\n\n"
            "I will search Wikipedia and return a summary + link to the full article."
        )
    return (
        "*How to use the bot:*\n\n"
        f"- This bot is specialized in: *{TOPIC_NAME}*\n"
        "- Send your question directly, or use:\n"
        "  `/search your question here`\n\n"
        "I will search Wikipedia and return a summary + link to the full article."
    )


def detect_lang(query: str) -> str:
    if ARABIC_RE.search(query):
        return "ar"
    return "en"


def build_search_term(user_query: str) -> str:
    user_query = user_query.strip()
    if FORCE_TOPIC_IN_QUERY and TOPIC_NAME.lower() not in user_query.lower():
        return f"{TOPIC_NAME} {user_query}"
    return user_query


def wiki_search(query: str, max_chars: int = 800) -> str:
    if not query:
        return "Please provide a search query."

    lang = detect_lang(query) or WIKI_DEFAULT_LANG
    search_term = build_search_term(query)

    search_url = f"https://{lang}.wikipedia.org/w/api.php"
    search_params = {
        "action": "query",
        "list": "search",
        "srsearch": search_term,
        "format": "json",
        "srlimit": 1,
    }

    try:
        resp = requests.get(search_url, params=search_params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
    except Exception as exc:
        logger.exception("Wikipedia search failed: %s", exc)
        return "Error while contacting Wikipedia. Please try again later."

    results = data.get("query", {}).get("search", [])
    if not results:
        return "No clear result found on Wikipedia. Try a different wording."

    page_title = results[0]["title"]
    summary_url = f"https://{lang}.wikipedia.org/api/rest_v1/page/summary/" + page_title.replace(" ", "_")

    try:
        s_resp = requests.get(summary_url, timeout=10)
        s_resp.raise_for_status()
        s_data = s_resp.json()
    except Exception as exc:
        logger.exception("Wikipedia summary failed: %s", exc)
        return "Error while fetching page summary from Wikipedia."

    title = s_data.get("title", page_title)
    extract = s_data.get("extract") or ""
    page_url = (
        s_data.get("content_urls", {}).get("desktop", {}).get("page")
        or f"https://{lang}.wikipedia.org/wiki/{page_title.replace(' ', '_')}"
    )

    if not extract:
        return "Not enough information found on Wikipedia."

    if len(extract) > max_chars:
        extract = extract[: max_chars - 3] + "..."

    header = f"Search about {TOPIC_NAME}\n\n"
    result_lines = [
        header,
        f"*{title}*",
        "",
        extract,
        "",
        f"Link: {page_url}",
    ]

    return "\n".join(result_lines)


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.effective_message.reply_markdown(get_start_message())


async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.effective_message.reply_markdown(get_help_message())


async def cmd_search(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if context.args:
        query = " ".join(context.args).strip()
    else:
        full_text = update.effective_message.text or ""
        parts = full_text.split(maxsplit=1)
        query = parts[1].strip() if len(parts) > 1 else ""

    if not query:
        await update.effective_message.reply_text("Please write something to search after /search.")
        return

    await update.effective_message.reply_text("Searching Wikipedia...", quote=True)
    result = wiki_search(query)
    await update.effective_message.reply_markdown(result)


async def handle_plain_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = (update.effective_message.text or "").strip()
    if len(text) < 3:
        return

    await update.effective_message.reply_markdown(
        f"Searching Wikipedia for:\n`{text}`\n\nPlease wait..."
    )
    result = wiki_search(text)
    await update.effective_message.reply_markdown(result)


def main() -> None:
    setup_logging()
    load_env(ENV_PATH)

    token = get_env("TELEGRAM_BOT_TOKEN")
    bot_name = get_env("BOT_NAME", f"{TOPIC_NAME}_search_bot")

    logger.info("Starting topic search bot for: %s", TOPIC_NAME)

    app = ApplicationBuilder().token(token).build()

    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("help", cmd_help))
    app.add_handler(CommandHandler("search", cmd_search))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_plain_text))

    logger.info("Bot %s is polling...", bot_name)
    app.run_polling()


if __name__ == "__main__":
    main()