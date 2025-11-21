from __future__ import annotations

from typing import Dict, Optional, Tuple

import streamlit as st

def render_sidebar(telegram_ids: Dict[str, str]) -> Tuple[str, Optional[str]]:
    """
    Render the sidebar and return:
    
    - target (str): The selected key (e.g., TELEGRAM_ME_ID or CUSTOM).
    - custom_chat_id (Optional[str]): The custom Chat ID value if CUSTOM is selected.

    Args:
        telegram_ids (Dict[str, str]): Dictionary of Telegram IDs from the .env file.

    Returns:
        Tuple[str, Optional[str]]: Selected target key and optional custom Chat ID.
    """
    st.sidebar.header("🎯 Target")

    if telegram_ids:
        target_options = list(telegram_ids.keys()) + ["CUSTOM"]
    else:
        target_options = ["CUSTOM"]

    target = st.sidebar.selectbox("Select target:", target_options)

    custom_chat_id: Optional[str] = None
    if target == "CUSTOM":
        custom_chat_id = st.sidebar.text_input("Custom Chat ID", value="")

    st.sidebar.markdown("---")
    st.sidebar.subheader("🔐 TELEGRAM_*_ID from .env:")

    if not telegram_ids:
        st.sidebar.write("❌ No TELEGRAM_*_ID found in .env")
    else:
        for name, value in telegram_ids.items():
            st.sidebar.markdown(f"**{name}:** `{value}`")

    return target, custom_chat_id