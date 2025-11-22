from __future__ import annotations

import os
from typing import Optional, List

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
    KeyboardButton,
)
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
)

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

from src.telegram.user_store import get_gmail_credentials_row


# ======================
# إعدادات عامة
# ======================

# عنوان سيرفر OAuth (نفسه الموجود في oauth_server.py)
# يمكنك تغييره في .env إلى دومين خارجي إذا استخدمت ngrok / Cloudflare
GMAIL_OAUTH_BASE_URL = os.getenv("GMAIL_OAUTH_BASE_URL", "http://localhost:8001")


# ======================
# أوامر البوت
# ======================

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    رسالة ترحيب + كيبورد أوامر أسفل الشاشة.
    """
    msg = update.effective_message

    text = (
        "📬 Gmail Bot في تليجرام\n\n"
        "هذا البوت متصل بحساب Gmail عبر OAuth.\n\n"
        "الأوامر المتاحة:\n"
        "• /link_gmail  لربط حساب Gmail الخاص بك.\n"
        "• /gmail       لعرض آخر الرسائل في بريدك الوارد.\n\n"
        "تذكّر: يجب أن يكون سيرفر OAuth شغّال على جهازك."
    )

    keyboard = ReplyKeyboardMarkup(
        [[KeyboardButton("/link_gmail"), KeyboardButton("/gmail")]],
        resize_keyboard=True,
        one_time_keyboard=False,
    )

    await msg.reply_text(text, reply_markup=keyboard)


async def cmd_link_gmail(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    يبدأ عملية ربط Gmail لمستخدم تيلجرام معيّن.
    يرسل له زر + رابط OAuth يحتوي على telegram_id.
    """
    user = update.effective_user
    msg = update.effective_message

    if not user:
        await msg.reply_text("❌ لم أستطع تحديد المستخدم.")
        return

    telegram_id = user.id

    # نبني رابط /oauth/start مع تمرير telegram_id
    base = GMAIL_OAUTH_BASE_URL.rstrip("/")
    auth_url = f"{base}/oauth/start?telegram_id={telegram_id}"

    text = (
        "🔗 ربط حساب Gmail (تجربة محلية)\n\n"
        "1️⃣ تأكد أن سيرفر OAuth يعمل على جهازك.\n"
        "2️⃣ اضغط الزر في الأسفل لفتح صفحة ربط Gmail،\n"
        "   أو افتح هذا الرابط في المتصفح على نفس الجهاز:\n\n"
        f"{auth_url}\n\n"
        "3️⃣ بعد إكمال الربط بنجاح، عد إلى هنا واكتب الأمر /gmail لقراءة الرسائل."
    )

    # زر تفاعلي لفتح الرابط
    keyboard = InlineKeyboardMarkup(
        [[InlineKeyboardButton("🔐 فتح صفحة ربط Gmail", url=auth_url)]]
    )

    await msg.reply_text(text, reply_markup=keyboard)


# ======================
# التعامل مع بيانات Gmail
# ======================

def _build_user_credentials(telegram_id: int) -> Optional[Credentials]:
    """
    إعادة بناء Credentials من البيانات المخزنة في قاعدة البيانات.
    نعتمد على الدالة get_gmail_credentials_row من user_store.py
    """
    row = get_gmail_credentials_row(telegram_id)
    if not row:
        return None

    if not row["access_token"] or not row["refresh_token"]:
        return None

    scopes_raw = row.get("scopes") or ""
    if isinstance(scopes_raw, str):
        scopes: List[str] = [
            s for s in scopes_raw.replace(",", " ").split() if s.strip()
        ]
    else:
        scopes = ["https://www.googleapis.com/auth/gmail.readonly"]

    creds = Credentials(
        token=row["access_token"],
        refresh_token=row["refresh_token"],
        token_uri=row["token_uri"],
        client_id=row["client_id"],
        client_secret=row["client_secret"],
        scopes=scopes,
    )
    return creds


async def cmd_gmail(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    يعرض آخر 5 رسائل من Gmail للمستخدم الذي ربط حسابه.
    """
    user = update.effective_user
    msg = update.effective_message

    if not user:
        await msg.reply_text("❌ لم أستطع تحديد المستخدم.")
        return

    telegram_id = user.id
    creds = _build_user_credentials(telegram_id)

    if not creds:
        await msg.reply_text(
            "❌ لا يوجد حساب Gmail مربوط بهذا المستخدم.\n"
            "استخدم الأمر /link_gmail أولًا لربط حسابك."
        )
        return

    try:
        service = build("gmail", "v1", credentials=creds)

        result = (
            service.users()
            .messages()
            .list(userId="me", maxResults=5, labelIds=["INBOX"])
            .execute()
        )
        messages = result.get("messages", [])
    except Exception as exc:  # شبكة / OAuth
        await msg.reply_text(f"⚠️ حدث خطأ أثناء الاتصال بـ Gmail:\n{exc}")
        return

    if not messages:
        await msg.reply_text("📭 لا توجد رسائل حديثة في البريد الوارد.")
        return

    lines: list[str] = ["📧 آخر 5 رسائل في بريدك الوارد:\n"]

    for m in messages:
        full = (
            service.users()
            .messages()
            .get(
                userId="me",
                id=m["id"],
                format="metadata",
                metadataHeaders=["Subject", "From"],
            )
            .execute()
        )
        headers = {
            h["name"]: h["value"]
            for h in full.get("payload", {}).get("headers", [])
        }
        subject = headers.get("Subject", "(بدون عنوان)")
        sender = headers.get("From", "(غير معروف)")
        lines.append(f"• {subject}\n  من: {sender}\n")

    await msg.reply_text("\n".join(lines))


# ======================
# تسجيل الهاندلرز في الـ Application
# ======================

def register_handlers(app: Application) -> None:
    """
    استدعِ هذه الدالة من app.py لتسجيل أوامر Gmail في البوت.
    """
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("link_gmail", cmd_link_gmail))
    app.add_handler(CommandHandler("gmail", cmd_gmail))
