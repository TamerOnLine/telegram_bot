# apps/dashboard/tabs/tab_overview.py
from __future__ import annotations

from typing import Dict

import streamlit as st


def render_tab(bot: Dict[str, str]) -> None:
    st.subheader("📋 نظرة عامة على البوت")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-label">اسم المجلد</div>
                <div class="metric-value">{bot['folder']}</div>
            </div>
            """,
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
            f"""
            <div class="metric-card">
                <div class="metric-label">Token متوفر</div>
                <div class="metric-value">{token_status}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.info(
        "هذه الواجهة هي مركز تحكم موحّد لكل البوتات داخل مشروعك:\n"
        "- 🔁 اختيار البوت من الشريط الجانبي.\n"
        "- ✉️ إرسال رسائل تجريبية لأي Chat ID.\n"
        "- 🖥 إدارة تشغيل الخدمة على السيرفر (لو تم تعريف SERVICE_NAME).\n"
        "- 📌 المساعدة في معرفة Chat ID للمستخدمين / الجروبات / القنوات.\n"
        "- 🗄️ معاينة قاعدة البيانات لكل بوت على حدة."
    )
