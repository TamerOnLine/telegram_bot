from __future__ import annotations

from pathlib import Path
from typing import List, Dict

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# صلاحيات القراءة فقط للبريد
SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]

# جذر المشروع: telegram/
PROJECT_ROOT = Path(__file__).resolve().parents[2]

# مجلد تطبيق الجيميل: telegram/apps/gmail/
GMAIL_APP_DIR = PROJECT_ROOT / "apps" / "gmail"

CREDENTIALS_FILE = GMAIL_APP_DIR / "credentials.json"
TOKEN_FILE = GMAIL_APP_DIR / "token.json"


def _get_service():
    """إنشاء كائن خدمة Gmail API مع التعامل مع token.json تلقائيًا."""
    creds: Credentials | None = None

    if TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)

    # لو لا يوجد توكن أو انتهت صلاحيته → نعمل تسجيل دخول جديد
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
    """إرجاع آخر رسائل البريد (مختصرة) لاستخدامها في البوت أو Streamlit."""
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
