from __future__ import annotations

import os
from pathlib import Path
from typing import List

# Base URL for OAuth (same variable as in .env)
GMAIL_OAUTH_BASE_URL = os.getenv(
    "GMAIL_OAUTH_BASE_URL",
    "http://localhost:8001"
).rstrip("/")

# Path to credentials.json file
GOOGLE_CLIENT_SECRET_PATH = Path(
    os.getenv("GOOGLE_CLIENT_SECRET_PATH", "credentials.json")
)

# Directory to store user tokens
GOOGLE_TOKEN_DIR = Path(
    os.getenv("GOOGLE_TOKEN_DIR", "tokens")
)

# Required Gmail scopes
SCOPES: List[str] = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/userinfo.email",
    "openid",
]

# Ensure the token directory exists
GOOGLE_TOKEN_DIR.mkdir(parents=True, exist_ok=True)
