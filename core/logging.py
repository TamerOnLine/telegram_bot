from __future__ import annotations

import logging


def setup_logging(level: int = logging.INFO) -> None:
    """
    Configure basic logging for all bots.
    """
    logging.basicConfig(
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        level=level,
    )
