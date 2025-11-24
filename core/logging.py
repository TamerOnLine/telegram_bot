from __future__ import annotations

import logging
import os


def setup_logging(level: int | None = None) -> None:
    """
    Configure basic logging for bots with adjustable verbosity.

    The logging level defaults to INFO. If the environment variable ENV_DEBUG is set to "1",
    the level is set to DEBUG. This function also suppresses verbose logs from `httpx` and
    `urllib3` within python-telegram-bot to reduce noise.

    Args:
        level (int | None): Optional custom logging level. If None, the value of ENV_DEBUG is used.

    Environment Variables:
        ENV_DEBUG: If set to "1", logging level is DEBUG; otherwise, it is INFO.
    """
    if level is None:
        env_debug = os.getenv("ENV_DEBUG", "0")
        level = logging.DEBUG if env_debug == "1" else logging.INFO

    logging.basicConfig(
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        level=level,
    )

    # Suppress detailed logs from httpx to avoid leaking bot-related URLs
    logging.getLogger("httpx").setLevel(logging.WARNING)

    # Suppress verbose logs from urllib3 used internally by python-telegram-bot
    logging.getLogger("telegram.vendor.ptb_urllib3.urllib3").setLevel(logging.WARNING)