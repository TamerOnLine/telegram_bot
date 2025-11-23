from __future__ import annotations

from pathlib import Path
from typing import Dict, Optional

from .panel.environment import load_environment, load_telegram_ids
from .panel.ui_layout import render_panel
from .db import init_db

def run_panel(env_path: Path) -> None:
    """
    Run the Streamlit interface for a single Telegram bot using the specified .env file.

    Steps:
    1. Load environment variables from the provided .env file.
    2. Initialize the database (create tables if they do not exist).
    3. Load Telegram user IDs.
    4. Define a resolver function for target user selection.
    5. Render the panel interface.

    Args:
        env_path (Path): Path to the .env configuration file.
    """

    # Load .env file
    load_environment(env_path)

    # Initialize the database (create tables if needed)
    init_db()

    # Load TELEGRAM_*_ID values
    telegram_ids: Dict[str, str] = load_telegram_ids()

    # Define the target resolution function
    def resolve_target(target_key: str, custom_id: Optional[str]) -> Optional[str]:
        if target_key == "CUSTOM":
            return custom_id or None
        return telegram_ids.get(target_key)

    # Render the panel
    render_panel(telegram_ids, resolve_target)