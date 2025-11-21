from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Optional

import streamlit as st

from ...telegram_utils import (  # type: ignore
    send_document,
    send_photo,
    send_voice,
)

from . import ResolveTargetFn

def render_tab_media(
    resolve_target: ResolveTargetFn,
    target: str,
    custom_chat_id: Optional[str],
) -> None:
    """
    Render the tab for sending media (photo, voice, or document) through the Telegram bot.

    Args:
        resolve_target (ResolveTargetFn): Function to resolve the final chat ID.
        target (str): The selected target key.
        custom_chat_id (Optional[str]): Optional custom Chat ID if target is CUSTOM.
    """
    st.subheader("🖼 Send Media (Photo / Voice / Document)")

    media_type = st.radio(
        "Select media type:",
        ["Photo", "Voice", "Document"],
        horizontal=True,
    )

    caption = st.text_input("Caption (optional)", value="")

    uploaded_file = st.file_uploader(
        "Choose a file from your device",
        type=["jpg", "jpeg", "png", "gif", "ogg", "mp3", "wav", "pdf", "zip", "txt"],
    )

    if st.button("📤 Send Media", use_container_width=True):
        chat_id = resolve_target(target, custom_chat_id)

        if not chat_id:
            st.error("⚠️ No valid chat_id available.")
        elif not uploaded_file:
            st.warning("⚠️ Please select a file before sending.")
        else:
            try:
                suffix = Path(uploaded_file.name).suffix
                with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                    tmp.write(uploaded_file.read())
                    tmp_path = tmp.name

                if media_type == "Photo":
                    result = send_photo(chat_id, tmp_path, caption=caption)
                elif media_type == "Voice":
                    result = send_voice(chat_id, tmp_path, caption=caption)
                else:
                    result = send_document(chat_id, tmp_path, caption=caption)

                if result:
                    st.success("✅ Media sent successfully")
                else:
                    st.error("❌ Failed to send media. Check the terminal logs.")
            except Exception as e:
                st.error(f"❌ An error occurred while sending media: {e}")