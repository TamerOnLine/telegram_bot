from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Dict, List, Tuple

import requests
import streamlit as st
from dotenv import dotenv_values


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
        return False, f"❌ استجابة غير مفهومة من Telegram (status={resp.status_code})."

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
        return False, f"❌ استجابة غير مفهومة من Telegram (status={resp.status_code})."

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
            ["systemctl", action, service],
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

def main() -> None:
    st.set_page_config(
        page_title="Telegram Bot Control Center",
        layout="wide",
        page_icon="🤖",
    )

    st.sidebar.title("⚙️ إدارة البوتات")
    st.sidebar.caption("مشروع: telegram_bot")

    bots = discover_bots()
    if not bots:
        st.error("لم يتم العثور على أي بوتات في مجلد `apps/` تحتوي على `bot.py` و `.env` مع TELEGRAM_BOT_TOKEN.")
        st.stop()

    # ----------------- اختيار البوت -----------------
    bot_labels = [
        f"{b['bot_name']} ({b['folder']})"
        for b in bots
    ]
    selected_idx = st.sidebar.selectbox(
        "اختر البوت داخل المشروع",
        options=list(range(len(bots))),
        format_func=lambda i: bot_labels[i],
    )
    bot = bots[selected_idx]

    # ----------------- رأس الصفحة -----------------
    col_left, col_right = st.columns([2, 1])
    with col_left:
        st.title("🤖 Telegram Bot Manager")
        st.subheader(f"البوت الحالي: {bot['bot_name']}")
        if bot["bot_description"]:
            st.write(bot["bot_description"])
        if bot["bot_username"]:
            st.markdown(
                f"📨 **Telegram:** [@{bot['bot_username']}](https://t.me/{bot['bot_username']})"
            )

    with col_right:
        st.markdown("#### معلومات سريعة")
        st.markdown(f"- **Folder:** `apps/{bot['folder']}`")
        st.markdown(f"- **.env:** `{bot['env_path']}`")
        token_masked = bot["token"][:8] + "..." + bot["token"][-4:]
        st.markdown(f"- **TOKEN:** `{token_masked}`")
        if bot["service_name"]:
            st.markdown(f"- **Service:** `{bot['service_name']}`")
        else:
            st.markdown("- **Service:** _(غير معرف)_")

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
            st.metric("مجلد البوت", bot["folder"])
        with col2:
            st.metric("ملف الإعدادات", ".env")
        with col3:
            st.metric("Token متوفر", "نعم ✅" if bot["token"] else "لا ❌")

        st.info(
            "هذه الواجهة مركز تحكم موحد لكل البوتات:\n"
            "- اختيار البوت من الشريط الجانبي\n"
            "- إرسال رسائل تجريبية لأي Chat ID\n"
            "- إدارة تشغيل الخدمة على السيرفر (إن عرّفت SERVICE_NAME)\n"
            "- المساعدة في معرفة Chat ID"
        )

    # ========== تبويب: إرسال رسالة ==========
    with tab_send:
        st.subheader("✉️ إرسال رسالة من هذا البوت")

        with st.form("send_message_form"):
            mode = st.radio(
                "نوع الإرسال:",
                options=["single", "multi"],
                format_func=lambda m: "إلى Chat واحد" if m == "single" else "إلى عدة Chats (كل سطر Chat ID)",
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

            send_btn = st.form_submit_button("🚀 إرسال")

        if send_btn:
            if not text.strip():
                st.error("الرجاء إدخال نص الرسالة.")
            elif not chat_id_input.strip():
                st.error("الرجاء إدخال قيمة واحدة على الأقل لـ Chat ID.")
            else:
                # تجهيز قائمة الـ IDs
                if mode == "single":
                    chat_ids = [chat_id_input.strip()]
                else:
                    chat_ids = [
                        line.strip()
                        for line in chat_id_input.splitlines()
                        if line.strip()
                    ]

                results = []
                with st.spinner("جاري الإرسال..."):
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

            st.markdown("#### آخر اللوجات (journalctl)")
            lines = st.slider("عدد الأسطر:", 20, 200, 80, step=10)
            if st.button("📜 تحديث اللوجات"):
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
### الطريقة الموصى بها (أمر /id داخل البوت)
1. أضف في كود البوت أمر `/id` يرجع لك `chat.id` (مرة واحدة فقط في الكود).
2. من أي محادثة (شخصية / جروب / قناة) اكتب `/id`.
3. سيرد عليك البوت برسالة فيها رقم الـ Chat ID.

> هذه الطريقة **لا تستخدم getUpdates** ولا تتعارض مع تشغيل البوت بـ run_polling أو webhook.
"""
        )

        st.divider()

        st.markdown("### طريقة مساعدة إضافية (getUpdates من هنا)")
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
