from __future__ import annotations

import os
from pathlib import Path

from telegram.ext import Application, ApplicationBuilder

from apps.gmail.telegram_commands import register_handlers

def run_bot(env_path: Path) -> None:
    """
    Launch the Gmail Bot.

    - Reads TELEGRAM_BOT_TOKEN from the environment.
    - Registers Gmail command handlers.
    - Starts polling for updates.

    Args:
        env_path (Path): Path to the .env file containing bot configurations.

    Raises:
        RuntimeError: If TELEGRAM_BOT_TOKEN is not set.
    """
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        raise RuntimeError(
            "Missing TELEGRAM_BOT_TOKEN in the .env file for Gmail Bot."
        )

    print("Gmail Bot listening... (env:", env_path, ")")

    app: Application = ApplicationBuilder().token(token).build()

    # Register Gmail commands
    register_handlers(app)

    # Start polling for updates
    app.run_polling(close_loop=False)