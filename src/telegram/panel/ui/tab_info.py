from __future__ import annotations

import streamlit as st

# Import the actual get_bot_info function from src/telegram/telegram_fetch.py
from ...telegram_fetch import get_bot_info

def render_tab_info() -> None:
    """
    Renders the Bot Info tab in the Streamlit app.

    Features:
    - Performs a getMe API call to check bot status.
    - Displays basic bot information.

    Note: This tab does not include options for retrieving last chat ID or getUpdates.
    """
    st.header("Bot Status (getMe)")

    # Bot status section
    st.subheader("Bot Status Check")

    if st.checkbox("Check Bot Status (getMe)", value=True):
        ok, err, info = get_bot_info()
        if not ok:
            st.error(err)
        else:
            st.success("Bot is working correctly")
            st.json(info, expanded=True)