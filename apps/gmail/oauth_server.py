from __future__ import annotations

import sys
from pathlib import Path
from typing import Dict, Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse, PlainTextResponse
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials

# Project directory path
BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.telegram.user_store import init_db, save_gmail_credentials  # type: ignore

# Importing configuration and HTML content from the bot directory
import gmail_oauth_config as cfg
import gmail_oauth_html as html

# Mapping between OAuth state and Telegram ID
STATE_TO_TELEGRAM: Dict[str, int] = {}

app = FastAPI(title="Gmail OAuth Server")


@app.on_event("startup")
def on_startup() -> None:
    """
    Initialize the database on server startup.
    Ensures the token directory exists.
    """
    try:
        init_db()
    except TypeError:
        # Adjust here if init_db requires parameters
        pass

    cfg.GOOGLE_TOKEN_DIR.mkdir(parents=True, exist_ok=True)


@app.get("/", response_class=HTMLResponse)
async def index() -> str:
    """
    Basic check page.
    """
    return html.index_html()


@app.get("/start")
async def start_oauth(telegram_id: int) -> RedirectResponse:
    """
    Starts the OAuth process.
    Triggered by the bot via a URL like:
    {GMAIL_OAUTH_BASE_URL}/start?telegram_id=123456
    """
    if not cfg.GOOGLE_CLIENT_SECRET_PATH.exists():
        raise HTTPException(
            status_code=500,
            detail=f"Google OAuth credentials file not found: {cfg.GOOGLE_CLIENT_SECRET_PATH}",
        )

    redirect_uri = f"{cfg.GMAIL_OAUTH_BASE_URL}/callback"

    flow = Flow.from_client_secrets_file(
        str(cfg.GOOGLE_CLIENT_SECRET_PATH),
        scopes=cfg.SCOPES,
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
    """
    Callback endpoint after user authorizes the application with Google.
    """
    params = dict(request.query_params)
    state: Optional[str] = params.get("state")
    if not state:
        return HTMLResponse(html.error_html("Missing state parameter from Google."), status_code=400)

    telegram_id = STATE_TO_TELEGRAM.pop(state, None)
    if telegram_id is None:
        return HTMLResponse(
            html.error_html("Unable to match state with a Telegram user."),
            status_code=400,
        )

    redirect_uri = f"{cfg.GMAIL_OAUTH_BASE_URL}/callback"

    flow = Flow.from_client_secrets_file(
        str(cfg.GOOGLE_CLIENT_SECRET_PATH),
        scopes=cfg.SCOPES,
        redirect_uri=redirect_uri,
        state=state,
    )

    try:
        authorization_response = str(request.url)
        flow.fetch_token(authorization_response=authorization_response)
    except Exception as exc:
        return HTMLResponse(
            html.error_html(f"Failed to fetch token from Google: {exc}"),
            status_code=400,
        )

    creds: Credentials = flow.credentials

    gmail_address: Optional[str] = None
    if creds.id_token and isinstance(creds.id_token, dict):
        gmail_address = creds.id_token.get("email")

    try:
        save_gmail_credentials(telegram_id, creds, gmail_address)
    except Exception as exc:
        return HTMLResponse(
            html.error_html(f"Token received but failed to save to database: {exc}"),
            status_code=500,
        )

    return HTMLResponse(html.success_html())


@app.get("/health", response_class=PlainTextResponse)
async def health() -> str:
    """
    Simple health check endpoint.
    """
    return "ok"