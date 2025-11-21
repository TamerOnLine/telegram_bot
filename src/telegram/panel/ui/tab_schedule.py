from __future__ import annotations

from datetime import date, datetime, time as dtime
from typing import Optional

import streamlit as st

from ..scheduler import schedule_message
from . import ResolveTargetFn

def render_tab_schedule(
    resolve_target: ResolveTargetFn,
    target: str,
    custom_chat_id: Optional[str],
) -> None:
    """
    Render the tab for scheduling a message to be sent later via the Telegram bot.

    Args:
        resolve_target (ResolveTargetFn): Function to resolve the final chat ID.
        target (str): The selected target key.
        custom_chat_id (Optional[str]): Optional custom Chat ID if target is CUSTOM.
    """
    st.subheader("⏰ Schedule a Message (send later)")

    sched_text = st.text_area(
        "Text to be sent later",
        height=120,
        placeholder="Type the message you want to schedule for later...",
    )
    sched_markdown = st.checkbox(
        "Interpret text as Markdown",
        value=False,
        key="sched_md",
    )

    today = date.today()
    sched_date = st.date_input("📅 Send Date", value=today)
    sched_time = st.time_input("🕒 Send Time", value=dtime(hour=12, minute=0))

    if st.button("⏰ Schedule Message", use_container_width=True):
        chat_id = resolve_target(target, custom_chat_id)
        if not chat_id:
            st.error("⚠️ No valid chat_id available.")
        elif not sched_text.strip():
            st.warning("⚠️ Please enter a message before scheduling.")
        else:
            run_at = datetime.combine(sched_date, sched_time)
            delay = schedule_message(chat_id, sched_text, run_at, sched_markdown)
            mins = int(delay // 60)
            secs = int(delay % 60)
            st.success(
                f"✅ Message scheduled to be sent at {run_at} "
                f"(in approximately {mins} minutes and {secs} seconds).\n"
                "Note: The Streamlit server must remain running until the scheduled time."
            )