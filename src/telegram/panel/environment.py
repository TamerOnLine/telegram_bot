from __future__ import annotations

import os
from pathlib import Path
from typing import Dict

from dotenv import load_dotenv

def load_environment(env_path: Path) -> None:
    """
    Load the specified .env file for the bot's environment configuration.

    Args:
        env_path (Path): Path to the .env file.
    """
    load_dotenv(dotenv_path=env_path)

def load_telegram_ids() -> Dict[str, str]:
    """
    Read all TELEGRAM_*_ID entries from the environment variables and return them as a dictionary.

    Returns:
        Dict[str, str]: Dictionary containing TELEGRAM_*_ID keys and their values.
    """
    ids: Dict[str, str] = {}
    for key, value in os.environ.items():
        if key.startswith("TELEGRAM_") and key.endswith("_ID") and value:
            ids[key] = value
    return ids