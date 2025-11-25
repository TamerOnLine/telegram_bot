# apps/dashboard/tabs/tab_database.py
from __future__ import annotations

from typing import Dict

import pandas as pd
import streamlit as st

from apps.dashboard.helpers.database_api import (
    delete_all_chats,
    delete_single_chat,
    get_chats_for_bot,
)


def render_tab(bot: Dict[str, str]) -> None:
    st.subheader("🗄️ إدارة قاعدة البيانات (bot_chats)")

    bot_name = bot["bot_name"]

    # قراءة البيانات من PostgreSQL
    chats = get_chats_for_bot(bot_name)

    if not chats:
        st.info("لا توجد سجلات للمحادثات في قاعدة البيانات لهذا البوت بعد.")
        return

    df = pd.DataFrame(chats)

    st.markdown("### 📊 إحصائيات سريعة")
    col1, col2, col3 = st.columns(3)
    col1.metric("عدد المحادثات", len(df))
    col2.metric("إجمالي الرسائل", int(df["message_count"].sum()))
    col3.metric("آخر نشاط", str(df["last_seen_at"].max())[:19])

    st.markdown("### 📜 السجلات")
    search_q = st.text_input(
        "🔍 بحث بالاسم / Chat ID / @username", key="db_search"
    )
    if search_q:
        q = search_q.strip().lower()
        mask = (
            df["chat_id"].astype(str).str.contains(q)
            | df["chat_type"].str.lower().str.contains(q)
            | df["title"].fillna("").str.lower().str.contains(q)
            | df["username"].fillna("").str.lower().str.contains(q)
        )
        df = df[mask]

    st.dataframe(df, use_container_width=True)

    st.markdown("---")
    st.markdown("### 🧹 تنظيف السجلات")

    # حذف محادثة واحدة
    with st.form("delete_single_chat"):
        st.write("حذف محادثة معيّنة (حسب Chat ID):")
        chat_id_str = st.text_input("Chat ID", placeholder="مثال: 123456789")
        submitted = st.form_submit_button("❌ حذف هذه المحادثة")
        if submitted and chat_id_str.strip():
            try:
                delete_single_chat(bot_name, int(chat_id_str.strip()))
                st.success("تم حذف المحادثة (إن كانت موجودة).")
            except ValueError:
                st.error("Chat ID غير صالح، يجب أن يكون رقمًا صحيحًا.")

    st.markdown("----")

    # حذف كل سجلات البوت
    if st.button("⚠️ حذف جميع سجلات هذا البوت من bot_chats"):
        delete_all_chats(bot_name)
        st.success("✅ تم حذف جميع السجلات لهذا البوت.")
