from __future__ import annotations

import os
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse, PlainTextResponse

from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials

from src.telegram.user_store import init_db, save_gmail_credentials

# =========================
# General Settings
# =========================

BASE_DIR = Path(__file__).resolve().parent

# Path to the Google OAuth credentials file (downloaded from Google Cloud Console)
CREDENTIALS_FILE = BASE_DIR / "credentials.json"

# Required Gmail scopes
SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]

# Callback URL registered in Google Cloud
REDIRECT_URI = os.getenv(
    "GMAIL_OAUTH_REDIRECT_URI",
    "http://localhost:8001/oauth/callback",
)

# Ensure the database is initialized
init_db()

app = FastAPI(title="Gmail OAuth Server")

# =========================
# Helpers
# =========================

def _build_flow() -> Flow:
    """
    Build a Flow object from the credentials file with the specified scopes.

    Returns:
        Flow: Google OAuth2 Flow instance configured for Gmail access.
    """
    flow = Flow.from_client_secrets_file(
        str(CREDENTIALS_FILE),
        scopes=SCOPES,
        redirect_uri=REDIRECT_URI,
    )
    return flow

def _success_html() -> str:
    """
    HTML content displayed after successful Gmail account linking.

    Returns:
        str: HTML response content.
    """
    return """
    <html dir=\"rtl\" lang=\"ar\">
      <head>
        <meta charset=\"utf-8\" />
        <title>تم ربط Gmail بنجاح</title>
        <style>
          body {
            font-family: system-ui, -apple-system, BlinkMacSystemFont, \"Segoe UI\", sans-serif;
            background-color: #0f172a;
            color: #e5e7eb;
            display: flex;
            align-items: center;
            justify-content: center;
            height: 100vh;
          }
          .card {
            background-color: #020617;
            padding: 2rem 2.5rem;
            border-radius: 1rem;
            box-shadow: 0 20px 40px rgba(0,0,0,0.35);
            text-align: center;
            max-width: 480px;
          }
          h1 {
            margin-top: 0;
            margin-bottom: 0.75rem;
            font-size: 1.5rem;
          }
          p {
            margin: 0.5rem 0;
            line-height: 1.6;
          }
          .emoji {
            font-size: 2.5rem;
            margin-bottom: 0.5rem;
          }
        </style>
      </head>
      <body>
        <div class=\"card\">
          <div class=\"emoji\">✅</div>
          <h1>Gmail account successfully linked</h1>
          <p>You can now return to Telegram and use the <code>/gmail</code> command to view your emails.</p>
          <p>This window can be safely closed.</p>
        </div>
      </body>
    </html>
    """

# =========================
# Endpoints
# =========================

@app.get("/", response_class=PlainTextResponse)
async def root() -> str:
    """
    Basic health check endpoint.

    Returns:
        str: Status message.
    """
    return "Gmail OAuth server is running."

@app.get("/oauth/start")
async def oauth_start(request: Request, telegram_id: int):
    """
    Starts the OAuth flow for a specific Telegram user.

    Args:
        request (Request): Incoming HTTP request.
        telegram_id (int): Telegram user's unique ID passed as state.

    Returns:
        RedirectResponse: Redirects the user to Google's OAuth consent page.
    """
    flow = _build_flow()

    auth_url, _ = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        state=str(telegram_id),
        prompt="consent",
    )

    return RedirectResponse(auth_url)

@app.get("/oauth/callback", response_class=HTMLResponse)
async def oauth_callback(request: Request):
    """
    Handles the callback from Google after user consent.

    Args:
        request (Request): Incoming callback request containing the authorization response.

    Returns:
        HTMLResponse: Confirmation page upon successful authorization.

    Raises:
        HTTPException: If the state is missing or token retrieval fails.
    """
    telegram_id_str = request.query_params.get("state")
    if not telegram_id_str:
        raise HTTPException(status_code=400, detail="Missing state parameter")

    try:
        telegram_id = int(telegram_id_str)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid state value")

    flow = _build_flow()

    try:
        flow.fetch_token(authorization_response=str(request.url))
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Failed to fetch token: {exc}") from exc

    creds: Credentials = flow.credentials

    gmail_address: str | None = None
    if creds.id_token and isinstance(creds.id_token, dict):
        gmail_address = creds.id_token.get("email")

    save_gmail_credentials(telegram_id, creds, gmail_address)

    return HTMLResponse(_success_html())
