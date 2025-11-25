from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Dict, List, Tuple

import requests
import streamlit as st
from dotenv import dotenv_values

import pandas as pd
from core.db import load_chats_for_bot, delete_chats_for_bot, delete_chat


# =========================
# مسارات المشروع
# =========================

# هذا الملف في: apps/dashboard/streamlit_app.py
PROJECT_ROOT = Path(__file__).resolve().parents[2]
APPS_DIR = PROJECT_ROOT / "apps"


# =========================
# دوال مساعدة عامة
# =========================


def discover_bots() -> List[Dict[str, str]]:
    """
    يبحث عن كل البوتات داخل apps/* التي تحتوي على:
      - bot.py
      - .env فيه TELEGRAM_BOT_TOKEN
    ويقرأ معلومات إضافية اختيارية من .env:
      BOT_NAME, BOT_USERNAME, BOT_DESCRIPTION, SERVICE_NAME
    """
    bots: List[Dict[str, str]] = []

    if not APPS_DIR.exists():
        return bots

    for bot_dir in sorted(APPS_DIR.iterdir()):
        if not bot_dir.is_dir():
            continue

        bot_file = bot_dir / "bot.py"
        env_file = bot_dir / ".env"

        if not bot_file.exists() or not env_file.exists():
            continue

        env_data = dotenv_values(env_file)

        token = env_data.get("TELEGRAM_BOT_TOKEN", "")
        if not token:
            # بدون توكن لا نعتبره بوت جاهز
            continue

        bots.append(
            {
                "folder": bot_dir.name,
                "env_path": str(env_file),
                "bot_name": env_data.get("BOT_NAME", bot_dir.name),
                "bot_username": env_data.get("BOT_USERNAME", ""),
                "bot_description": env_data.get("BOT_DESCRIPTION", ""),
                "token": token,
                "service_name": env_data.get("SERVICE_NAME", ""),  # اختياري
            }
        )

    return bots


def call_telegram_send_message(
    token: str,
    chat_id: str,
    text: str,
) -> Tuple[bool, str]:
    """
    يرسل رسالة عبر Telegram HTTP API.
    يرجع (success, message).
    """
    if not token:
        return False, "❌ لا يوجد TELEGRAM_BOT_TOKEN في ملف .env لهذا البوت."

    url = f"https://api.telegram.org/bot{token}/sendMessage"

    try:
        resp = requests.post(
            url,
            data={
                "chat_id": chat_id.strip(),
                "text": text,
            },
            timeout=15,
        )
    except Exception as exc:  # noqa: BLE001
        return False, f"❌ خطأ في الاتصال بواجهة Telegram API: {exc}"

    try:
        data = resp.json()
    except json.JSONDecodeError:
        return (
            False,
            f"❌ استجابة غير مفهومة من Telegram (status={resp.status_code}).",
        )

    if not data.get("ok"):
        return False, f"❌ Telegram error: {data.get('description', 'Unknown error')}"

    return True, "✅ تم إرسال الرسالة."


def fetch_chats_from_updates(
    token: str,
) -> Tuple[bool, str | List[Dict[str, str]]]:
    """
    يجلب آخر التحديثات من Telegram ويستخرج قائمة بالشاتات.
    تحذير: يستخدم getUpdates (قد يتعارض مع run_polling لو البوت شغال بنفس التوكن).
    """
    if not token:
        return False, "❌ لا يوجد TELEGRAM_BOT_TOKEN في ملف .env لهذا البوت."

    url = f"https://api.telegram.org/bot{token}/getUpdates"

    try:
        resp = requests.get(url, timeout=15)
    except Exception as exc:  # noqa: BLE001
        return False, f"❌ خطأ في الاتصال بواجهة Telegram API: {exc}"

    try:
        data = resp.json()
    except json.JSONDecodeError:
        return (
            False,
            f"❌ استجابة غير مفهومة من Telegram (status={resp.status_code}).",
        )

    if not data.get("ok"):
        return False, f"❌ Telegram error: {data.get('description', 'Unknown error')}"

    results = data.get("result", [])
    chats: Dict[int, Dict[str, str]] = {}

    for update in results:
        msg = (
            update.get("message")
            or update.get("edited_message")
            or update.get("channel_post")
            or update.get("edited_channel_post")
        )
        if not msg:
            continue

        chat = msg.get("chat", {})
        chat_id = chat.get("id")
        if chat_id is None:
            continue

        chat_type = chat.get("type", "unknown")
        title = (
            chat.get("title")
            or chat.get("username")
            or f"{chat.get('first_name', '')} {chat.get('last_name', '')}".strip()
            or "—"
        )

        chats[chat_id] = {
            "chat_id": str(chat_id),
            "type": chat_type,
            "title_or_username": title,
        }

    if not chats:
        return False, (
            "لم أجد أي محادثات في getUpdates.\n"
            "تأكد أنك أرسلت /start أو رسالة للبوت، ثم أعد المحاولة."
        )

    return True, list(chats.values())


def run_systemctl(
    service: str,
    action: str,
) -> Tuple[bool, str]:
    """
    يشغّل أو يوقف أو يعيد تشغيل خدمة systemd.
    action ∈ {status, start, stop, restart}
    يعمل فقط على لينكس ويحتاج صلاحيات مناسبة.
    """
    if not service:
        return False, "❌ لم يتم تعريف SERVICE_NAME في ملف .env لهذا البوت."

    try:
        result = subprocess.run(
            ["sudo", "/usr/bin/systemctl", action, service],  # ✅ هنا التعديل
            check=False,
            capture_output=True,
            text=True,
        )
    except FileNotFoundError:
        return False, "❌ systemctl غير متوفر (غالباً تعمل على ويندوز أو نظام بدون systemd)."

    out = (result.stdout or "") + (result.stderr or "")
    ok = result.returncode == 0
    return ok, out.strip() or "(لا يوجد مخرجات)"



def tail_journal(service: str, lines: int = 50) -> Tuple[bool, str]:
    """
    يجلب آخر N سطر من journalctl لهذه الخدمة.
    """
    if not service:
        return False, "❌ لم يتم تعريف SERVICE_NAME في ملف .env لهذا البوت."

    try:
        result = subprocess.run(
            ["journalctl", "-u", service, "--no-pager", f"-n{lines}"],
            check=False,
            capture_output=True,
            text=True,
        )
    except FileNotFoundError:
        return False, "❌ journalctl غير متوفر على هذا النظام."

    out = (result.stdout or "") + (result.stderr or "")
    ok = result.returncode == 0
    return ok, out.strip() or "(لا يوجد لوجات)"


# =========================
# واجهة Streamlit
# =========================


def _inject_custom_css() -> None:
    """حقن تنسيق بسيط لواجهة احترافية (داكنة + كروت)."""
    css = """
    <style>
    .stApp {
        background: radial-gradient(circle at top left, #0f172a 0, #020617 45%, #020617 100%);
        color: #e5e7eb;
    }
    .main-header {
        padding: 1.1rem 1.4rem;
        border-radius: 1rem;
        background: linear-gradient(135deg, #0ea5e9, #6366f1);
        color: white;
        margin-bottom: 1.3rem;
        box-shadow: 0 18px 40px rgba(15, 23, 42, 0.55);
    }
    .main-header h1 {
        font-size: 1.8rem;
        margin-bottom: 0.15rem;
    }
    .main-header p {
        margin: 0;
        opacity: 0.94;
        font-size: 0.95rem;
    }
    .bot-pill {
        display: inline-flex;
        align-items: center;
        gap: 0.35rem;
        padding: 0.1rem 0.75rem;
        border-radius: 999px;
        background: rgba(15,23,42,0.18);
        border: 1px solid rgba(226,232,240,0.35);
        font-size: 0.78rem;
    }
    .metric-card {
        padding: 0.85rem 1rem;
        border-radius: 0.9rem;
        background: rgba(15,23,42,0.9);
        border: 1px solid rgba(148,163,184,0.35);
        margin-bottom: 0.25rem;
    }
    .metric-label {
        font-size: 0.72rem;
        text-transform: uppercase;
        letter-spacing: .08em;
        color: #9ca3af;
    }
    .metric-value {
        font-size: 1.05rem;
        font-weight: 600;
        margin-top: 0.2rem;
        color: #e5e7eb;
    }
    .tag {
        display: inline-flex;
        align-items: center;
        gap: 0.35rem;
        padding: 0.15rem 0.55rem;
        border-radius: 999px;
        background: rgba(15,23,42,0.85);
        border: 1px solid rgba(55,65,81,0.85);
        font-size: 0.7rem;
        color: #cbd5f5;
        margin-right: 0.3rem;
        margin-bottom: 0.3rem;
    }
    .small-muted {
        font-size: 0.8rem;
        color: #9ca3af;
    }
    .stTabs [role="tablist"] {
        gap: .35rem;
    }
    .stTabs [role="tab"] {
        padding-top: 0.3rem;
        padding-bottom: 0.3rem;
    }
    footer, #MainMenu {
        visibility: hidden;
        height: 0;
    }
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)


def main() -> None:
    st.set_page_config(
        page_title="Telegram Bot Control Center",
        layout="wide",
        page_icon="🤖",
    )

    _inject_custom_css()

    # ----------------- الشريط الجانبي -----------------
    st.sidebar.title("⚙️ إدارة البوتات")
    st.sidebar.caption("مشروع: telegram_bot — Multi-Bot Suite")

    bots = discover_bots()
    if not bots:
        st.error(
            "لم يتم العثور على أي بوتات في مجلد `apps/` تحتوي على `bot.py` و `.env` مع TELEGRAM_BOT_TOKEN."
        )
        st.stop()

    bot_labels = [f"{b['bot_name']} ({b['folder']})" for b in bots]
    selected_idx = st.sidebar.selectbox(
        "اختر البوت داخل المشروع",
        options=list(range(len(bots))),
        format_func=lambda i: bot_labels[i],
    )
    bot = bots[selected_idx]

    with st.sidebar.expander("ℹ️ معلومات عن المشروع", expanded=False):
        st.markdown(
            "- يدعم عدد غير محدود من البوتات داخل مشروع واحد.\n"
            "- كل بوت في مجلد مستقل تحت `apps/`.\n"
            "- هذه اللوحة فقط للتحكم والإدارة."
        )
        st.markdown(
            "[📦 فتح المشروع في GitHub](https://github.com/TamerOnLine/telegram_bot)",
            unsafe_allow_html=True,
        )

    # ----------------- رأس الصفحة الاحترافي -----------------
    col_header, col_quick = st.columns([2.4, 1.6])

    with col_header:
        st.markdown(
            f"""
            <div class="main-header">
                <div style="display:flex;justify-content:space-between;align-items:flex-start;gap:1rem;">
                    <div>
                        <h1>🤖 Telegram Bot Control Center</h1>
                        <p>
                            مركز تحكّم موحّد لكل البوتات داخل مشروعك.<br/>
                            <span class="small-muted">يمكنك إرسال رسائل، إدارة systemd، وقراءة Chat IDs من مكان واحد.</span>
                        </p>
                        <div style="margin-top:0.45rem;">
                            <span class="bot-pill">
                                <span style="font-size:0.8rem;">البوت الحالي:</span>
                                <strong>{bot['bot_name']}</strong>
                            </span>
                        </div>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col_quick:
        token_masked = bot["token"][:8] + "..." + bot["token"][-4:]
        service = bot["service_name"] or "غير معرف"

        st.markdown(
            """
            <div class="metric-card">
                <div class="metric-label">المجلد</div>
                <div class="metric-value">apps/{folder}</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">ملف البيئة (.env)</div>
                <div class="metric-value">{env_path}</div>
            </div>
            """.format(
                folder=bot["folder"],
                env_path=bot["env_path"],
            ),
            unsafe_allow_html=True,
        )

        st.markdown(
            """
            <div class="metric-card" style="margin-top:0.35rem;">
                <div class="metric-label">Token</div>
                <div class="metric-value">{token}</div>
                <div class="small-muted" style="margin-top:0.15rem;">
                    يتم إخفاء التوكن في الواجهة، لا تُظهره لأحد.
                </div>
            </div>
            """.format(
                token=token_masked,
            ),
            unsafe_allow_html=True,
        )

        st.markdown(
            """
            <div class="metric-card" style="margin-top:0.35rem;">
                <div class="metric-label">خدمة systemd</div>
                <div class="metric-value">{service}</div>
            </div>
            """.format(
                service=service,
            ),
            unsafe_allow_html=True,
        )

    # معلومات إضافية بسيطة تحت الهيدر
    meta_col_left, meta_col_right = st.columns([2.0, 1.3])
    with meta_col_left:
        tags_html = '<span class="tag">📂 apps/{folder}</span>'.format(
            folder=bot["folder"]
        )
        if bot["bot_username"]:
            tags_html += (
                '<span class="tag">✉️ @{username}</span>'.format(
                    username=bot["bot_username"]
                )
            )
        tags_html += '<span class="tag">🧪 جاهز للاختبار</span>'
        st.markdown(tags_html, unsafe_allow_html=True)

        if bot["bot_description"]:
            st.markdown(
                f"<div class='small-muted' style='margin-top:0.2rem;'>{bot['bot_description']}</div>",
                unsafe_allow_html=True,
            )
    with meta_col_right:
        if bot["bot_username"]:
            st.markdown(
                f"**رابط البوت:** [@{bot['bot_username']}](https://t.me/{bot['bot_username']})"
            )

    st.markdown("---")

    # ----------------- التبويبات الرئيسية -----------------
    tab_overview, tab_send, tab_service, tab_chatid = st.tabs(
        ["📋 نظرة عامة", "✉️ إرسال رسالة", "🖥 تشغيل البوت (systemd)", "📌 Chat ID"]
    )

    # ========== تبويب: نظرة عامة ==========
    with tab_overview:
        st.subheader("📋 نظرة عامة على البوت")

        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown(
                """
                <div class="metric-card">
                    <div class="metric-label">اسم المجلد</div>
                    <div class="metric-value">{folder}</div>
                </div>
                """.format(
                    folder=bot["folder"],
                ),
                unsafe_allow_html=True,
            )
        with col2:
            st.markdown(
                """
                <div class="metric-card">
                    <div class="metric-label">ملف البيئة</div>
                    <div class="metric-value">.env</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with col3:
            token_status = "نعم ✅" if bot["token"] else "لا ❌"
            st.markdown(
                """
                <div class="metric-card">
                    <div class="metric-label">Token متوفر</div>
                    <div class="metric-value">{status}</div>
                </div>
                """.format(
                    status=token_status,
                ),
                unsafe_allow_html=True,
            )

        st.info(
            "هذه الواجهة هي مركز تحكم موحّد لكل البوتات داخل مشروعك:\n"
            "- 🔁 اختيار البوت من الشريط الجانبي.\n"
            "- ✉️ إرسال رسائل تجريبية لأي Chat ID.\n"
            "- 🖥 إدارة تشغيل الخدمة على السيرفر (لو تم تعريف SERVICE_NAME).\n"
            "- 📌 المساعدة في معرفة Chat ID للمستخدمين / الجروبات / القنوات."
        )

    # ========== تبويب: إرسال رسالة ==========
    with tab_send:
        st.subheader("✉️ إرسال رسالة من هذا البوت")

        st.caption("أرسل رسالة اختبار إلى Chat ID واحد أو إلى قائمة من الـ IDs.")

        with st.form("send_message_form"):
            mode = st.radio(
                "نوع الإرسال:",
                options=["single", "multi"],
                format_func=lambda m: "إلى Chat واحد"
                if m == "single"
                else "إلى عدة Chats (كل سطر Chat ID)",
                horizontal=True,
            )

            if mode == "single":
                chat_id_input = st.text_input(
                    "Chat ID",
                    help="مثال: 123456789 أو -100123456789 (للقنوات والجروبات).",
                )
            else:
                chat_id_input = st.text_area(
                    "قائمة Chat IDs",
                    help="اكتب كل Chat ID في سطر مستقل.",
                    height=100,
                )

            text = st.text_area(
                "نص الرسالة",
                value="👋 رسالة اختبار من لوحة إدارة البوتات.",
                height=150,
            )

            st.caption(
                "تلميح: استخدم هذا القسم لاختبار البوت على عدة جروبات وقنوات في نفس الوقت."
            )

            send_btn = st.form_submit_button("🚀 إرسال الرسالة الآن")

        if send_btn:
            if not text.strip():
                st.error("الرجاء إدخال نص الرسالة.")
            elif not chat_id_input.strip():
                st.error("الرجاء إدخال قيمة واحدة على الأقل لـ Chat ID.")
            else:
                if mode == "single":
                    chat_ids = [chat_id_input.strip()]
                else:
                    chat_ids = [
                        line.strip()
                        for line in chat_id_input.splitlines()
                        if line.strip()
                    ]

                results = []
                with st.spinner("جاري الإرسال عبر Telegram API..."):
                    for cid in chat_ids:
                        ok, msg = call_telegram_send_message(
                            bot["token"],
                            cid,
                            text,
                        )
                        results.append(
                            {
                                "chat_id": cid,
                                "status": "✅ OK" if ok else "❌ ERROR",
                                "details": msg,
                            }
                        )

                st.success(f"تمت محاولة الإرسال إلى {len(chat_ids)} Chat.")
                st.dataframe(results, use_container_width=True)

    # ========== تبويب: إدارة التشغيل (systemd) ==========
    with tab_service:
        st.subheader("🖥 إدارة تشغيل البوت عبر systemd")

        service = bot["service_name"]

        if not service:
            st.warning(
                "لم يتم تعريف `SERVICE_NAME` في ملف `.env` لهذا البوت.\n"
                "أضف مثلاً: `SERVICE_NAME=shop_bot.service` داخل .env لتفعيل هذا القسم."
            )
        else:
            st.info(
                f"التحكم في الخدمة: `{service}`\n\n"
                "⚠️ يتطلب هذا أن تعمل اللوحة على نفس السيرفر الذي يحتوي على خدمة systemd "
                "وأن يكون للمستخدم صلاحيات تشغيل systemctl."
            )

            col_a, col_b, col_c, col_d = st.columns(4)
            with col_a:
                if st.button("📊 Status", use_container_width=True):
                    ok, out = run_systemctl(service, "status")
                    st.code(out, language="bash")
            with col_b:
                if st.button("▶️ Start", use_container_width=True):
                    ok, out = run_systemctl(service, "start")
                    st.code(out, language="bash")
            with col_c:
                if st.button("⏸ Stop", use_container_width=True):
                    ok, out = run_systemctl(service, "stop")
                    st.code(out, language="bash")
            with col_d:
                if st.button("🔄 Restart", use_container_width=True):
                    ok, out = run_systemctl(service, "restart")
                    st.code(out, language="bash")

            st.markdown("#### 📜 آخر اللوجات (journalctl)")
            lines = st.slider("عدد الأسطر:", 20, 200, 80, step=10)
            if st.button("📥 تحديث اللوجات"):
                ok, out = tail_journal(service, lines=lines)
                if ok:
                    st.code(out, language="bash")
                else:
                    st.error(out)

    # ========== تبويب: Chat ID ==========
    with tab_chatid:
        st.subheader("📌 الحصول على Chat ID")

        st.markdown(
            """
### ✅ الطريقة الموصى بها (أمر /id داخل البوت)
1. أضف في كود البوت أمر `/id` يرجع لك `chat.id` (مرة واحدة فقط في الكود).
2. من أي محادثة (شخصية / جروب / قناة) اكتب `/id`.
3. سيرد عليك البوت برسالة فيها رقم الـ Chat ID.

> هذه الطريقة **لا تستخدم getUpdates** ولا تتعارض مع تشغيل البوت بـ `run_polling` أو `webhook`.
"""
        )

        st.divider()

        st.markdown("### 🧪 طريقة مساعدة إضافية (getUpdates من هنا)")
        st.warning(
            "هذه الطريقة تستخدم `getUpdates` وقد تعطي خطأ (Conflict) إذا كان البوت شغال بـ `run_polling` "
            "بنفس التوكن. استخدمها فقط إذا أوقفت البوت مؤقتًا أو في بيئة تطويرية."
        )

        if st.button("🔄 جلب آخر التحديثات من Telegram (getUpdates)"):
            with st.spinner("جاري جلب التحديثات وتحليل المحادثات..."):
                ok, result = fetch_chats_from_updates(bot["token"])

            if ok:
                chats_list = result  # type: ignore[assignment]
                st.success(
                    "✅ تم العثور على المحادثات التالية. انسخ الـ `chat_id` المناسب واستخدمه في تبويب (إرسال رسالة)."
                )
                st.dataframe(chats_list, use_container_width=True)
            else:
                st.error(result)  # type: ignore[arg-type]


if __name__ == "__main__":
    main()
