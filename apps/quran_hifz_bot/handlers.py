from __future__ import annotations

from datetime import date
from math import ceil
from typing import Final

from telegram import (
    Update,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
)

from .config import logger
from .models import HifzGoal, compute_today_portion
from .storage import save_goal, load_goal


# =========================
#  حالات المحادثة
# =========================

SET_SURAH, SET_START, SET_END, SET_DAYS, CONFIRM = range(5)


# =========================
#  مساعد لبناء القائمة الرئيسية
# =========================

def _build_main_menu() -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton("🎯 Set goal", callback_data="set_goal")],
        [InlineKeyboardButton("📅 Today", callback_data="today")],
        [InlineKeyboardButton("📘 My goal", callback_data="my_goal")],
        [InlineKeyboardButton("❓ Help", callback_data="help")],
    ]
    return InlineKeyboardMarkup(keyboard)


# =========================
#  رسائل مساعدة
# =========================

def _format_goal_summary(goal: HifzGoal) -> str:
    total = goal.total_ayahs
    per_day = max(1, ceil(total / goal.days))

    return (
        "📋 *Your memorization goal:*\n\n"
        f"• Surah: *{goal.surah}*\n"
        f"• From ayah: *{goal.start_ayah}*\n"
        f"• To ayah: *{goal.end_ayah}*\n"
        f"• Total ayahs: *{total}*\n"
        f"• Days: *{goal.days}*\n"
        f"• ≈ Ayahs per day: *{per_day}*\n"
        f"• Start date: *{goal.start_date}*\n"
    )


# =========================
#  أوامر بسيطة
# =========================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    /start — رسالة ترحيب + قائمة رئيسية.
    """
    user = update.effective_user
    logger.info("User %s started the bot.", user.id if user else "unknown")

    text = (
        "🕌 *Quran Hifz Coach*\n\n"
        "Welcome! This bot helps you plan and track your Quran memorization.\n\n"
        "You can:\n"
        "• Set a memorization goal with /set_goal\n"
        "• See today's portion with /today\n"
        "• View your current goal with /my_goal\n"
        "• Get help with /help\n\n"
        "Use the buttons below or send commands directly."
    )

    await update.effective_message.reply_markdown(
        text,
        reply_markup=_build_main_menu(),
    )


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    /help — شرح طريقة الاستخدام.
    """
    text = (
        "❓ *How to use the bot:*\n\n"
        "1️⃣ Use /set_goal to define a memorization plan:\n"
        "   • Choose a Surah\n"
        "   • Starting ayah\n"
        "   • Ending ayah\n"
        "   • Number of days\n\n"
        "2️⃣ Use /today to see what you should memorize today.\n"
        "3️⃣ Use /my_goal to see your full current goal.\n\n"
        "You can also use the main menu buttons."
    )

    await update.effective_message.reply_markdown(
        text,
        reply_markup=_build_main_menu(),
    )


async def my_goal(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    /my_goal — عرض الهدف الحالي للمستخدم.
    """
    user = update.effective_user
    if not user:
        return

    goal = load_goal(user.id)
    if not goal:
        await update.effective_message.reply_text(
            "You don't have a saved goal yet.\n"
            "Use /set_goal to create a new memorization goal.",
            reply_markup=_build_main_menu(),
        )
        return

    text = _format_goal_summary(goal)
    await update.effective_message.reply_markdown(
        text,
        reply_markup=_build_main_menu(),
    )


async def today(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    /today — حساب الجزء المطلوب لهذا اليوم.
    """
    user = update.effective_user
    if not user:
        return

    goal = load_goal(user.id)
    if not goal:
        await update.effective_message.reply_text(
            "You don't have a saved goal yet.\n"
            "Use /set_goal to create a memorization plan first.",
            reply_markup=_build_main_menu(),
        )
        return

    from_ayah, to_ayah, finished = compute_today_portion(goal)

    if finished and from_ayah > goal.end_ayah:
        # الهدف منتهي
        text = (
            "✅ Your memorization goal is already *completed*.\n\n"
            + _format_goal_summary(goal)
        )
    else:
        text = (
            "📅 *Today's portion:*\n\n"
            f"• Surah: *{goal.surah}*\n"
            f"• From ayah: *{from_ayah}*\n"
            f"• To ayah: *{to_ayah}*\n\n"
            "May Allah make it easy for you 🤲"
        )

    await update.effective_message.reply_markdown(
        text,
        reply_markup=_build_main_menu(),
    )


# =========================
#  محادثة /set_goal
# =========================

async def set_goal_entry(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    نقطة دخول /set_goal — نسأل عن اسم السورة.
    """
    context.user_data.clear()
    await update.effective_message.reply_text(
        "🔹 Let's set a new memorization goal.\n\n"
        "Please type the *Surah name* you want to memorize."
    )
    return SET_SURAH


async def set_goal_surah(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    حفظ اسم السورة والانتقال لرقم الآية الأولى.
    """
    surah = (update.effective_message.text or "").strip()
    if not surah:
        await update.effective_message.reply_text(
            "Please write a valid Surah name."
        )
        return SET_SURAH

    context.user_data["goal_surah"] = surah
    await update.effective_message.reply_text(
        f"✅ Surah set to: {surah}\n\n"
        "Now, please type the *starting ayah number*."
    )
    return SET_START


async def set_goal_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    حفظ الآية الأولى والانتقال لرقم الآية الأخيرة.
    """
    text = (update.effective_message.text or "").strip()
    try:
        start_ayah = int(text)
        if start_ayah <= 0:
            raise ValueError
    except ValueError:
        await update.effective_message.reply_text(
            "Please enter a valid *positive number* for the starting ayah."
        )
        return SET_START

    context.user_data["goal_start"] = start_ayah
    await update.effective_message.reply_text(
        f"✅ Starting ayah set to: {start_ayah}\n\n"
        "Now, please type the *ending ayah number*."
    )
    return SET_END


async def set_goal_end(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    حفظ الآية الأخيرة والانتقال لعدد الأيام.
    """
    text = (update.effective_message.text or "").strip()
    try:
        end_ayah = int(text)
        if end_ayah <= 0:
            raise ValueError
    except ValueError:
        await update.effective_message.reply_text(
            "Please enter a valid *positive number* for the ending ayah."
        )
        return SET_END

    start_ayah = context.user_data.get("goal_start")
    if start_ayah is None:
        await update.effective_message.reply_text(
            "Something went wrong. Let's start again with /set_goal."
        )
        return ConversationHandler.END

    if end_ayah < start_ayah:
        await update.effective_message.reply_text(
            "Ending ayah must be *greater than or equal* to the starting ayah.\n"
            "Please enter the ending ayah again."
        )
        return SET_END

    context.user_data["goal_end"] = end_ayah
    await update.effective_message.reply_text(
        f"✅ Ending ayah set to: {end_ayah}\n\n"
        "Finally, how many *days* do you want to use to complete this goal?"
    )
    return SET_DAYS


async def set_goal_days(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    حفظ عدد الأيام، حساب الملخص، وعرض رسالة تأكيد.
    """
    text = (update.effective_message.text or "").strip()
    try:
        days = int(text)
        if days <= 0:
            raise ValueError
    except ValueError:
        await update.effective_message.reply_text(
            "Please enter a valid *positive number* for the days."
        )
        return SET_DAYS

    surah = context.user_data.get("goal_surah")
    start_ayah = context.user_data.get("goal_start")
    end_ayah = context.user_data.get("goal_end")

    if surah is None or start_ayah is None or end_ayah is None:
        await update.effective_message.reply_text(
            "Something went wrong. Let's start again with /set_goal."
        )
        return ConversationHandler.END

    start_date = date.today().isoformat()
    goal = HifzGoal(
        surah=surah,
        start_ayah=start_ayah,
        end_ayah=end_ayah,
        days=days,
        start_date=start_date,
    )

    context.user_data["pending_goal"] = goal

    summary = _format_goal_summary(goal)
    text_summary = (
        summary
        + "\nDo you want to *save* this goal?\n\n"
        "✅ Confirm to save\n"
        "❌ Cancel to discard"
    )

    keyboard = [
        [
            InlineKeyboardButton("✅ Confirm", callback_data="confirm_goal"),
            InlineKeyboardButton("❌ Cancel", callback_data="cancel_goal"),
        ]
    ]

    await update.effective_message.reply_markdown(
        text_summary,
        reply_markup=InlineKeyboardMarkup(keyboard),
    )
    return CONFIRM


async def set_goal_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    تأكيد أو إلغاء الهدف عبر أزرار inline.
    """
    query = update.callback_query
    await query.answer()

    data = query.data or ""
    user = update.effective_user

    goal: HifzGoal | None = context.user_data.get("pending_goal")

    if data == "confirm_goal":
        if not user or not goal:
            await query.edit_message_text(
                "Something went wrong and the goal could not be saved.\n"
                "Please try again with /set_goal."
            )
            return ConversationHandler.END

        save_goal(user.id, goal)
        context.user_data.pop("pending_goal", None)
        logger.info("Saved goal for user %s: %s", user.id, goal)

        await query.edit_message_text(
            "✅ Your memorization goal has been *saved*.\n\n"
            "Use /today to see your daily portion.",
        )
        return ConversationHandler.END

    # cancel_goal or unknown
    context.user_data.pop("pending_goal", None)
    await query.edit_message_text(
        "❌ Goal creation *cancelled*.\n"
        "You can start again anytime with /set_goal."
    )
    return ConversationHandler.END


async def set_goal_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    /cancel داخل المحادثة — إلغاء إعداد الهدف.
    """
    context.user_data.pop("pending_goal", None)
    await update.effective_message.reply_text(
        "❌ Goal creation cancelled.\n"
        "You can start again anytime with /set_goal.",
        reply_markup=_build_main_menu(),
    )
    return ConversationHandler.END


# =========================
#  أزرار القائمة الرئيسية
# =========================

async def menu_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    التعامل مع أزرار القائمة الرئيسية (CallbackQuery).
    الأنماط المتوقعة: set_goal / today / my_goal / help
    """
    query = update.callback_query
    await query.answer()

    data: Final[str] = query.data or ""

    if data == "set_goal":
        # نطلب من المستخدم أن يرسل /set_goal لبدء المحادثة
        await query.message.reply_text(
            "To set a new memorization goal, please send the command: /set_goal"
        )
        return

    if data == "today":
        await today(update, context)
        return

    if data == "my_goal":
        await my_goal(update, context)
        return

    if data == "help":
        await help_cmd(update, context)
        return
