from __future__ import annotations

from typing import Dict, Optional

import streamlit as st

from . import ResolveTargetFn
from .sidebar import render_sidebar
from .tab_info import render_tab_info
from .tab_text import render_tab_text
from .tab_media import render_tab_media
from .tab_alert import render_tab_alert
from .tab_schedule import render_tab_schedule
from .tab_users import render_tab_users

def _setup_page() -> None:
    """
    Configure the Streamlit page settings and render the header.
    """
    st.set_page_config(
        page_title="Telegram Control Panel",
        page_icon="🤖",
        layout="wide",
    )

    st.markdown(
        """
        <h1 style="text-align:center;">🤖 Telegram Control Panel</h1>
        <p style="text-align:center; color: gray;">
            Interface for inspecting the bot, extracting Chat ID, sending text, media, alerts, and scheduled messages.
        </p>
        <hr>
        """,
        unsafe_allow_html=True,
    )

def render_panel(telegram_ids: Dict[str, str], resolve_target: ResolveTargetFn) -> None:
    """
    Render the full Streamlit interface for the Telegram bot control panel.

    Args:
        telegram_ids (Dict[str, str]): Dictionary of available Telegram IDs.
        resolve_target (ResolveTargetFn): Function to resolve the final target chat ID.
    """

    # 1) Set up the page
    _setup_page()

    # 2) Render the sidebar, returns target and custom_chat_id
    target, custom_chat_id = render_sidebar(telegram_ids)

    # 3) Define tabs
    tab_info, tab_text, tab_media, tab_alert, tab_schedule, tab_users = st.tabs(
        [
            "ℹ️ Bot Status & Chat ID",
            "💬 Text Message",
            "🖼 Media (Images/Audio/Files)",
            "🚨 Error Alert",
            "⏰ Scheduled Message",
            "👥 Users",
        ]
    )


    # 4) Render each tab content
    with tab_info:
        render_tab_info()

    with tab_text:
        render_tab_text(resolve_target, target, custom_chat_id)

    with tab_media:
        render_tab_media(resolve_target, target, custom_chat_id)

    with tab_alert:
        render_tab_alert()

    with tab_schedule:
        render_tab_schedule(resolve_target, target, custom_chat_id)

    with tab_users:
        render_tab_users()