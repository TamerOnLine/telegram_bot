# apps/dashboard/tabs/tab_send.py
from __future__ import annotations

from typing import Dict, List

import streamlit as st

from apps.dashboard.helpers.telegram_api import send_message


def render_tab(bot: Dict[str, str]) -> None:
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

    if not send_btn:
        return

    if not text.strip():
        st.error("الرجاء إدخال نص الرسالة.")
        return

    if not chat_id_input.strip():
        st.error("الرجاء إدخال قيمة واحدة على الأقل لـ Chat ID.")
        return

    if mode == "single":
        chat_ids: List[str] = [chat_id_input.strip()]
    else:
        chat_ids = [
            line.strip()
            for line in chat_id_input.splitlines()
            if line.strip()
        ]

    results = []
    with st.spinner("جاري الإرسال عبر Telegram API..."):
        for cid in chat_ids:
            ok, msg = send_message(bot["token"], cid, text)
            results.append(
                {
                    "chat_id": cid,
                    "status": "✅ OK" if ok else "❌ ERROR",
                    "details": msg,
                }
            )

    st.success(f"تمت محاولة الإرسال إلى {len(chat_ids)} Chat.")
    st.dataframe(results, use_container_width=True)
