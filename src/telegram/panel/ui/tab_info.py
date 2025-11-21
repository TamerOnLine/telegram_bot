from __future__ import annotations

import streamlit as st

# نستخدم الدالة الموجودة فعليًا في src/telegram/telegram_fetch.py
from ...telegram_fetch import get_bot_info


def render_tab_info() -> None:
    """
    تبويب معلومات البوت:
    • فحص getMe
    • عرض معلومات البوت

    (✔️ لا يوجد أي قسم لـ Retrieve Last Chat ID أو getUpdates)
    """

    st.header("ℹ️ Bot Status (getMe)")

    # --- فحص حالة البوت (getMe)
    st.subheader("🟢 Bot Status (getMe)")

    if st.checkbox("✔️ Check Bot Status (getMe)", value=True):
        ok, err, info = get_bot_info()
        if not ok:
            st.error(err)
        else:
            st.success("✅ Bot is working correctly")
            st.json(info, expanded=True)
