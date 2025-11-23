from __future__ import annotations

import os

import streamlit as st

from ...db import get_all_users, get_messages_for_chat

def render_tab_users() -> None:
    """
    Renders the Users tab:
    - Displays only users associated with the current bot profile
      as specified by BOT_PROFILE in the .env file.
    - Filters out users from other bot profiles.
    """

    st.header("Users Who Contacted the Bot")

    # Read current bot profile from .env
    current_profile = os.getenv("BOT_PROFILE")
    if not current_profile:
        st.error(
            "BOT_PROFILE is not set in the .env file.\n"
            "Set it to a value like BOT_PROFILE=quran or BOT_PROFILE=gmail and restart the panel."
        )
        return

    # Fetch all users from the database
    users = get_all_users()
    if not users:
        st.info("No users have been recorded in the database yet.")
        return

    # Filter users by current bot profile
    filtered_users = [
        u for u in users if (u.get("bot_profile") or "") == current_profile
    ]

    st.caption(f"Displaying users for current bot profile: `{current_profile}`")

    if not filtered_users:
        st.info(
            "No users are registered for this bot yet.\n"
            "Try messaging the bot on Telegram, then refresh this page."
        )
        return

    # Display users in a table
    st.subheader("User List")
    st.dataframe(
        [
            {
                "chat_id": u["chat_id"],
                "type": u["type"],
                "username": u["username"],
                "name": f"{u.get('first_name') or ''} {u.get('last_name') or ''}".strip(),
                "title": u["title"],
                "added_at": u["added_at"],
                "last_seen_at": u["last_seen_at"],
            }
            for u in filtered_users
        ],
        use_container_width=True,
    )

    # Show messages for a selected user
    st.markdown("---")
    st.subheader("Messages for a Specific User")

    chat_ids = [u["chat_id"] for u in filtered_users]
    selected_chat_id = st.selectbox("Select a chat_id:", chat_ids)

    if selected_chat_id:
        msgs = get_messages_for_chat(int(selected_chat_id), limit=50)
        if not msgs:
            st.info("No messages recorded for this user.")
        else:
            msgs = [
                m for m in msgs if (m.get("bot_profile") or "") == current_profile
            ]

            for m in reversed(msgs):
                direction = "⬅️ In" if m["direction"] == "in" else "➡️ Out"
                st.markdown(
                    f"**{direction}** — `{m['created_at']}`  \n"
                    f"{m['text'] or ''}"
                )