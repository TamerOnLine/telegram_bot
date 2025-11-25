# apps/dashboard/streamlit_app.py
from __future__ import annotations

from typing import Dict, List

import streamlit as st

from apps.dashboard.helpers.bots import discover_bots
from apps.dashboard.helpers.paths import ensure_project_root_on_sys_path
from apps.dashboard.helpers.style import inject_global_css
from apps.dashboard.tabs import (
    tab_chatid,
    tab_database,
    tab_overview,
    tab_send,
    tab_service,
)

# تأكد من أن جذر المشروع موجود في sys.path
ensure_project_root_on_sys_path()


def _render_header(bot: Dict[str, str]) -> None:
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
        service = bot.get("service_name") or "غير معرف"

        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-label">المجلد</div>
                <div class="metric-value">apps/{bot['folder']}</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">ملف البيئة (.env)</div>
                <div class="metric-value">{bot['env_path']}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown(
            f"""
            <div class="metric-card" style="margin-top:0.35rem;">
                <div class="metric-label">Token</div>
                <div class="metric-value">{token_masked}</div>
                <div class="small-muted" style="margin-top:0.15rem;">
                    يتم إخفاء التوكن في الواجهة، لا تُظهره لأحد.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown(
            f"""
            <div class="metric-card" style="margin-top:0.35rem;">
                <div class="metric-label">خدمة systemd</div>
                <div class="metric-value">{service}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # سطر معلومات إضافية تحت الهيدر
    meta_col_left, meta_col_right = st.columns([2.0, 1.3])
    with meta_col_left:
        tags_html = f'<span class="tag">📂 apps/{bot["folder"]}</span>'
        if bot["bot_username"]:
            tags_html += f'<span class="tag">✉️ @{bot["bot_username"]}</span>'
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


def main() -> None:
    st.set_page_config(
        page_title="Telegram Bot Control Center",
        layout="wide",
        page_icon="🤖",
    )

    inject_global_css()

    # الشريط الجانبي
    st.sidebar.title("⚙️ إدارة البوتات")
    st.sidebar.caption("مشروع: telegram_bot — Multi-Bot Suite")

    bots: List[Dict[str, str]] = discover_bots()
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

    # رأس الصفحة
    _render_header(bot)

    # التبويبات
    tab_over, tab_send_tab, tab_srv, tab_chat, tab_db = st.tabs(
        [
            "📋 نظرة عامة",
            "✉️ إرسال رسالة",
            "🖥 تشغيل البوت (systemd)",
            "📌 Chat ID",
            "🗄️ قاعدة البيانات",
        ]
    )

    with tab_over:
        tab_overview.render_tab(bot)

    with tab_send_tab:
        tab_send.render_tab(bot)

    with tab_srv:
        tab_service.render_tab(bot)

    with tab_chat:
        tab_chatid.render_tab(bot)

    with tab_db:
        tab_database.render_tab(bot)


if __name__ == "__main__":
    main()
