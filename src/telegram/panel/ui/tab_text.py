from __future__ import annotations

from typing import Optional

import streamlit as st

from ...telegram_utils import (  # type: ignore
    send_markdown,
    send_text,
)

from . import ResolveTargetFn

def render_tab_text(
    resolve_target: ResolveTargetFn,
    target: str,
    custom_chat_id: Optional[str],
) -> None:
    """
    Render the tab for sending a plain or Markdown-formatted text message.

    Args:
        resolve_target (ResolveTargetFn): Function to resolve the final chat ID.
        target (str): The selected target key.
        custom_chat_id (Optional[str]): Optional custom Chat ID if target is CUSTOM.
    """
    st.subheader("💬 Send Text Message")

    col1, col2 = st.columns([2, 1])

    with col1:
        text = st.text_area(
            "Message to send",
            height=150,
            placeholder="Type your message here...",
        )
    with col2:
        use_markdown = st.checkbox("Interpret text as Markdown", value=False)
        st.markdown(
            """
            **Notes:**
            - You can use **Markdown** for formatting  
            - Example: `*bold*`, `_italic_`, ``` `code` ```
            """
        )

    if st.button("🚀 Send Text Now", use_container_width=True, key="send_text_now"):
        chat_id = resolve_target(target, custom_chat_id)
        if not chat_id:
            st.error("⚠️ No valid chat_id available.")
        elif not text.strip():
            st.warning("⚠️ Please enter text before sending.")
        else:
            try:
                if use_markdown:
                    result = send_markdown(chat_id, text)
                else:
                    result = send_text(chat_id, text)

                if result:
                    msg_id = result["result"]["message_id"]
                    st.success(f"✅ Message sent successfully (message_id = {msg_id})")
                else:
                    st.error("❌ Failed to send message. Check terminal logs.")
            except Exception as e:
                st.error(f"❌ An error occurred while sending the message: {e}")