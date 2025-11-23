from __future__ import annotations

from pathlib import Path
from typing import List, Dict

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# Read-only permissions for Gmail
SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]

# Project root directory: telegram/
PROJECT_ROOT = Path(__file__).resolve().parents[2]

# Gmail application directory: telegram/apps/gmail/
GMAIL_APP_DIR = PROJECT_ROOT / "apps" / "gmail"

CREDENTIALS_FILE = GMAIL_APP_DIR / "credentials.json"
TOKEN_FILE = GMAIL_APP_DIR / "token.json"

def _get_service():
    """
    Create and return a Gmail API service object.

    Handles automatic loading, validation, and refreshing of the token file.
    Initiates a new OAuth2 flow if no valid token exists.

    Returns:
        Resource: Authorized Gmail API service instance.
    """
    creds: Credentials | None = None

    if TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                str(CREDENTIALS_FILE),
                SCOPES,
            )
            creds = flow.run_local_server(port=0)
        TOKEN_FILE.write_text(creds.to_json(), encoding="utf-8")

    return build("gmail", "v1", credentials=creds)

def get_last_emails(limit: int = 5) -> List[Dict[str, str]]:
    """
    Retrieve the latest emails with basic metadata.

    Args:
        limit (int): Maximum number of emails to retrieve.

    Returns:
        List[Dict[str, str]]: A list of email metadata including sender, subject, date,
        snippet, and a direct Gmail web link.
    """
    service = _get_service()

    res = service.users().messages().list(
        userId="me", maxResults=limit, q="",
    ).execute()

    messages = res.get("messages", [])
    emails: List[Dict[str, str]] = []

    for m in messages:
        msg = service.users().messages().get(
            userId="me",
            id=m["id"],
            format="metadata",
            metadataHeaders=["From", "Subject", "Date"],
        ).execute()

        headers = {
            h["name"]: h["value"] for h in msg["payload"].get("headers", [])
        }

        emails.append(
            {
                "from": headers.get("From", ""),
                "subject": headers.get("Subject", ""),
                "date": headers.get("Date", ""),
                "snippet": msg.get("snippet", ""),
                "link": f"https://mail.google.com/mail/u/0/#inbox/{m['id']}",
            }
        )

    return emails