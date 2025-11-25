# apps/dashboard/tabs/tab_service.py
from __future__ import annotations

from typing import Dict

import streamlit as st

from apps.dashboard.helpers.systemd_api import run_systemctl, tail_journal


def render_tab(bot: Dict[str, str]) -> None:
    st.subheader("🖥 إدارة تشغيل البوت عبر systemd")

    service = bot.get("service_name") or ""

    if not service:
        st.warning(
            "لم يتم تعريف `SERVICE_NAME` في ملف `.env` لهذا البوت.\n"
            "أضف مثلاً: `SERVICE_NAME=tg_bot@hello_bot.service` داخل .env لتفعيل هذا القسم."
        )
        return

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
