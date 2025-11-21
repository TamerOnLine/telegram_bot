from __future__ import annotations

import os

import streamlit as st

from ...db import get_all_users, get_messages_for_chat


def render_tab_users() -> None:
    """
    تبويب عرض المستخدمين:
    - يعرض فقط المستخدمين الذين لهم نفس bot_profile الخاص بهذه الواجهة
      (المأخوذ من BOT_PROFILE في ملف .env).
    - لا يظهر أي مستخدمين من بوتات أخرى.
    """

    st.header("👥 Users Who Contacted the Bot")

    # 1) قراءة البروفايل الحالي من .env
    current_profile = os.getenv("BOT_PROFILE")
    if not current_profile:
        st.error(
            "❌ BOT_PROFILE غير مضبوط في ملف .env لهذه الواجهة.\n"
            "ضع مثلاً: BOT_PROFILE=quran أو BOT_PROFILE=gmail ثم أعد تشغيل اللوحة."
        )
        return

    # 2) جلب كل المستخدمين من قاعدة البيانات
    users = get_all_users()
    if not users:
        st.info("لم يتم تسجيل أي مستخدم بعد في قاعدة البيانات.")
        return

    # 3) فلترة المستخدمين حسب البوت الحالي فقط
    filtered_users = [
        u for u in users if (u.get("bot_profile") or "") == current_profile
    ]

    st.caption(f"عرض المستخدمين لبروفايل البوت الحالي: `{current_profile}`")

    if not filtered_users:
        st.info(
            "لا يوجد مستخدمون مسجّلون لهذا البوت بعد.\n"
            "جرّب أن ترسل رسالة لهذا البوت من تيليجرام ثم أعد فتح الصفحة."
        )
        return

    # 4) عرض جدول المستخدمين
    st.subheader("قائمة المستخدمين")

    st.dataframe(
        [
            {
                "chat_id": u["chat_id"],
                "type": u["type"],
                "username": u["username"],
                "name": f"{u.get('first_name') or ''} {u.get('last_name') or ''}".strip(),
                "title": u["title"],
                "added_at": u["added_at"],
                "last_seen_at": u["last_seen_at"],
            }
            for u in filtered_users
        ],
        use_container_width=True,
    )

    # 5) عرض رسائل مستخدم معيّن (من نفس البوت فقط)
    st.markdown("---")
    st.subheader("📨 Messages for a specific user")

    chat_ids = [u["chat_id"] for u in filtered_users]
    selected_chat_id = st.selectbox("اختر chat_id:", chat_ids)

    if selected_chat_id:
        msgs = get_messages_for_chat(int(selected_chat_id), limit=50)
        if not msgs:
            st.info("لا توجد رسائل محفوظة لهذا المستخدم بعد.")
        else:
            # نضمن أننا نعرض رسائل هذا البوت فقط
            msgs = [
                m
                for m in msgs
                if (m.get("bot_profile") or "") == current_profile
            ]

            for m in reversed(msgs):
                direction = "⬅️ In" if m["direction"] == "in" else "➡️ Out"
                st.markdown(
                    f"**{direction}** — `{m['created_at']}`  \n"
                    f"{m['text'] or ''}"
                )
