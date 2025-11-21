from __future__ import annotations

import threading
from datetime import datetime

from ..telegram_utils import send_markdown, send_text  # type: ignore

def schedule_message(
    chat_id: str | int,
    text: str,
    run_at: datetime,
    use_markdown: bool,
) -> float:
    """
    Schedule a message to be sent at a specific datetime.

    Args:
        chat_id (str | int): The chat ID where the message will be sent.
        text (str): The message content.
        run_at (datetime): The scheduled datetime for sending the message.
        use_markdown (bool): Whether to format the message using Markdown.

    Returns:
        float: The delay in seconds until the message is sent.
    """
    delay = (run_at - datetime.now()).total_seconds()
    if delay < 0:
        delay = 0

    def _job() -> None:
        try:
            if use_markdown:
                send_markdown(chat_id, text)
            else:
                send_text(chat_id, text)
        except Exception as e:
            print(f"[SCHEDULE ERROR] {e}")

    t = threading.Timer(delay, _job)
    t.daemon = True
    t.start()
    return delay