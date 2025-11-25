# apps/dashboard/tabs/tab_chatid.py
from __future__ import annotations

from typing import Dict

import streamlit as st

from apps.dashboard.helpers.telegram_api import fetch_chats_from_updates


def render_tab(bot: Dict[str, str]) -> None:
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
