from __future__ import annotations

import os
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse, PlainTextResponse

from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials

from src.telegram.user_store import init_db, save_gmail_credentials


# =========================
# إعدادات عامة
# =========================

BASE_DIR = Path(__file__).resolve().parent

# ملف بيانات تطبيق Google OAuth (حمّلته من Google Cloud Console)
CREDENTIALS_FILE = BASE_DIR / "credentials.json"

# الصلاحيات المطلوبة من Gmail
SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]

# عنوان الـ callback المسجل في Google Cloud
# يمكنك تغييره من متغير البيئة إذا أردت استخدام 192.168.1.100 مثلًا
REDIRECT_URI = os.getenv(
    "GMAIL_OAUTH_REDIRECT_URI",
    "http://localhost:8001/oauth/callback",
)

# تأكد أن قاعدة البيانات موجودة
init_db()

app = FastAPI(title="Gmail OAuth Server")


# =========================
# Helpers
# =========================


def _build_flow() -> Flow:
    """
    يبني كائن Flow من ملف credentials.json مع الصلاحيات المطلوبة.
    لا نستخدم flow.params هنا (غير مدعوم في النسخ الجديدة).
    """
    flow = Flow.from_client_secrets_file(
        str(CREDENTIALS_FILE),
        scopes=SCOPES,
        redirect_uri=REDIRECT_URI,
    )
    return flow


def _success_html() -> str:
    return """
    <html dir="rtl" lang="ar">
      <head>
        <meta charset="utf-8" />
        <title>تم ربط Gmail بنجاح</title>
        <style>
          body {
            font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
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
        <div class="card">
          <div class="emoji">✅</div>
          <h1>تم ربط حساب Gmail بنجاح</h1>
          <p>يمكنك الآن العودة إلى تيلجرام وكتابة الأمر <code>/gmail</code> لقراءة رسائلك.</p>
          <p>يمكن إغلاق هذه النافذة بأمان.</p>
        </div>
      </body>
    </html>
    """


# =========================
# Endpoints
# =========================


@app.get("/", response_class=PlainTextResponse)
async def root() -> str:
    return "Gmail OAuth server is running."


@app.get("/oauth/start")
async def oauth_start(request: Request, telegram_id: int):
    """
    يبدأ تدفق OAuth لمستخدم تيلجرام معيّن.
    - نرسل المستخدم إلى صفحة Google مع state = telegram_id.
    """
    # نبني الـ Flow
    flow = _build_flow()

    # نمرّر telegram_id داخل state
    auth_url, _ = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        state=str(telegram_id),  # 👈 هنا تم تمرير state بشكل صحيح
        prompt="consent",
    )

    # إعادة توجيه المستخدم مباشرة إلى Google
    return RedirectResponse(auth_url)


@app.get("/oauth/callback", response_class=HTMLResponse)
async def oauth_callback(request: Request):
    """
    يستقبل الرد من Google بعد الموافقة.
    - نقرأ state (الذي يحتوي telegram_id)
    - نجلب التوكن
    - نخزّنه في قاعدة البيانات
    """
    # state يجب أن يحتوي telegram_id الذي أرسلناه في /oauth/start
    telegram_id_str = request.query_params.get("state")
    if not telegram_id_str:
        raise HTTPException(status_code=400, detail="Missing state parameter")

    try:
        telegram_id = int(telegram_id_str)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid state value")

    # نبني Flow جديد بنفس الإعدادات
    flow = _build_flow()

    # نجلب التوكن من Google بالاعتماد على رابط الاستدعاء الكامل
    try:
        flow.fetch_token(authorization_response=str(request.url))
    except Exception as exc:  # pragma: no cover - للتشخيص فقط
        raise HTTPException(status_code=400, detail=f"Failed to fetch token: {exc}") from exc

    creds: Credentials = flow.credentials

    # email غالبًا موجود في id_token، وإن لم يوجد يمكن تجاهله
    gmail_address: str | None = None
    if creds.id_token and isinstance(creds.id_token, dict):
        gmail_address = creds.id_token.get("email")

    # نحفظ بيانات الاعتماد في قاعدة البيانات (تابع التوقيع الموجود عندك في user_store)
    # هنا نفترض أن save_gmail_credentials يقبل:
    #   (telegram_id: int, creds: Credentials, email: Optional[str])
    save_gmail_credentials(telegram_id, creds, gmail_address)

    # صفحة نجاح بسيطة للمستخدم
    return HTMLResponse(_success_html())
