from __future__ import annotations

import os
from pathlib import Path

# Base URL for your OAuth server
GMAIL_OAUTH_BASE_URL = os.getenv(
    "GMAIL_OAUTH_BASE_URL", "http://mystrotamer.com:8001"
).rstrip("/")

# Path to credentials.json file
GOOGLE_CLIENT_SECRET_PATH = Path(
    os.getenv(
        "GOOGLE_CLIENT_SECRET_PATH",
        "/home/tamer/telegram_bot/apps/gmail/credentials.json",
    )
)

# Directory to store token files
GOOGLE_TOKEN_DIR = Path(
    os.getenv(
        "GOOGLE_TOKEN_DIR",
        "/home/tamer/telegram_bot/apps/gmail/tokens",
    )
)

# Gmail scopes
SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "openid",
    "email",
    "profile",
]
