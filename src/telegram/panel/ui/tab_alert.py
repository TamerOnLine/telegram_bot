from __future__ import annotations

import streamlit as st

from ...telegram_utils import send_error_alert  # type: ignore

def render_tab_alert() -> None:
    """
    Render the tab for sending an error alert to the personal Telegram account.
    """
    st.subheader("🚨 Send Error Alert to Your Personal Account")

    err_text = st.text_input(
        "Error description (will be sent via send_error_alert)",
        value="",
    )

    if st.button("🚨 Send Error Alert Now", use_container_width=True):
        if not err_text.strip():
            st.warning("⚠️ Please enter an error message first.")
        else:
            try:
                send_error_alert(err_text)
                st.success("✅ Error alert successfully sent to your personal account (ME_ID).")
            except Exception as e:
                st.error(f"❌ An error occurred while sending the alert: {e}")