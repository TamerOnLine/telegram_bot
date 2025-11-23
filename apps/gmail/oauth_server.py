from __future__ import annotations

import sys
from pathlib import Path
from typing import Dict, Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse, PlainTextResponse
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials

# Set project root so we can import src.telegram.*
BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.telegram.user_store import init_db, save_gmail_credentials  # type: ignore

from .gmail_config import (
    GMAIL_OAUTH_BASE_URL,
    GOOGLE_CLIENT_SECRET_PATH,
    GOOGLE_TOKEN_DIR,
    SCOPES,
)

# Temporary mapping between OAuth state ↔ Telegram ID
STATE_TO_TELEGRAM: Dict[str, int] = {}

app = FastAPI(title="Gmail OAuth Server")


@app.on_event("startup")
def on_startup() -> None:
    """Initialize DB and ensure token directory exists."""
    init_db()
    GOOGLE_TOKEN_DIR.mkdir(parents=True, exist_ok=True)


@app.get("/", response_class=HTMLResponse)
async def index() -> str:
    return "<h2>Gmail OAuth Server Running</h2>"


@app.get("/start")
async def start_oauth(telegram_id: int) -> RedirectResponse:
    """User clicks link from bot → go to Google OAuth."""
    if not GOOGLE_CLIENT_SECRET_PATH.exists():
        raise HTTPException(
            status_code=500,
            detail=f"credentials.json not found at: {GOOGLE_CLIENT_SECRET_PATH}",
        )

    redirect_uri = f"{GMAIL_OAUTH_BASE_URL}/callback"

    flow = Flow.from_client_secrets_file(
        str(GOOGLE_CLIENT_SECRET_PATH),
        scopes=SCOPES,
        redirect_uri=redirect_uri,
    )

    auth_url, state = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent",
    )

    STATE_TO_TELEGRAM[state] = telegram_id
    return RedirectResponse(auth_url)


@app.get("/callback", response_class=HTMLResponse)
async def oauth_callback(request: Request) -> HTMLResponse:
    """Google redirects here after user login."""
    params = dict(request.query_params)
    state: Optional[str] = params.get("state")

    if not state:
        return HTMLResponse("Missing state", status_code=400)

    telegram_id = STATE_TO_TELEGRAM.pop(state, None)
    if telegram_id is None:
        return HTMLResponse("Invalid OAuth state", status_code=400)

    redirect_uri = f"{GMAIL_OAUTH_BASE_URL}/callback"

    flow = Flow.from_client_secrets_file(
        str(GOOGLE_CLIENT_SECRET_PATH),
        scopes=SCOPES,
        redirect_uri=redirect_uri,
        state=state,
    )

    try:
        flow.fetch_token(authorization_response=str(request.url))
    except Exception as exc:
        return HTMLResponse(f"Failed to fetch token: {exc}", status_code=400)

    creds: Credentials = flow.credentials

    email = None
    if creds.id_token and isinstance(creds.id_token, dict):
        email = creds.id_token.get("email")

    save_gmail_credentials(telegram_id, creds, email)

    return HTMLResponse(
        "<h2>تم ربط Gmail بنجاح — يمكنك العودة للبوت وكتابة /gmail</h2>"
    )


@app.get("/health", response_class=PlainTextResponse)
async def health() -> str:
    return "ok"
