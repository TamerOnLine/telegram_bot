from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv


def load_env(env_path: Path) -> None:
    """
    Load environment variables from the given .env file.
    """
    if not env_path.exists():
        raise FileNotFoundError(f".env file not found: {env_path}")

    load_dotenv(dotenv_path=env_path, override=True)


def get_env(name: str, default: str | None = None) -> str:
    """
    Read an environment variable (after load_env has been called).
    """
    value = os.getenv(name, default)
    if value is None:
        raise RuntimeError(f"Environment variable {name} is required but not set")
    return value
