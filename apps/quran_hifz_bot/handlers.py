from __future__ import annotations
from telegram import Update
from telegram.ext import ContextTypes
from .storage import get_user_record, update_user_record


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    user = update.effective_user
    if not user or not msg.text:
        return

    text = msg.text.strip()

    # هدف جديد
    if context.user_data.get("awaiting_goal"):
        context.user_data["awaiting_goal"] = False
        update_user_record(user.id, {"goal": text})
        await msg.reply_text(f"🎯 تم حفظ هدفك:\n\n{text}")
        return

    # تسجيل ما حفظ اليوم
    if context.user_data.get("awaiting_today"):
        context.user_data["awaiting_today"] = False

        rec = get_user_record(user.id)
        today_list = rec.get("today_memorized") or []
        today_list.append(text)

        update_user_record(user.id, {"today_memorized": today_list})
        await msg.reply_text("📌 تم تسجيل ما حفظته اليوم.")
        return

    await msg.reply_text(
        "استعمل الأوامر:\n/help\n/set_goal\n/today\n/my_goal\n"
    )
