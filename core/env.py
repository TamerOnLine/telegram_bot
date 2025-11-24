from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv


def load_env(env_path: Path) -> None:
    """
    Load environment variables from the specified .env file.

    Args:
        env_path (Path): The path to the .env file.

    Raises:
        FileNotFoundError: If the .env file does not exist.
    """
    if not env_path.exists():
        raise FileNotFoundError(f".env file not found: {env_path}")

    load_dotenv(dotenv_path=env_path, override=True)


def get_env(name: str, default: str | None = None) -> str:
    """
    Retrieve the value of an environment variable.

    This function should be called after `load_env()` has loaded the environment variables.

    Args:
        name (str): The name of the environment variable.
        default (str | None, optional): The default value to return if the environment variable is not set.

    Returns:
        str: The value of the environment variable.

    Raises:
        RuntimeError: If the environment variable is not set and no default is provided.
    """
    value = os.getenv(name, default)
    if value is None:
        raise RuntimeError(f"Environment variable {name} is required but not set")
    return value
