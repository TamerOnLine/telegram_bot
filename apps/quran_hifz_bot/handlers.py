from __future__ import annotations

from datetime import date
from typing import Tuple

from telegram import (
    Update,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from telegram.ext import (
    CallbackContext,
    ConversationHandler,
    MessageHandler,
    CallbackQueryHandler,
    CommandHandler,
    filters,
)

from .config import BOT_NAME
from .models import HifzGoal, compute_today_portion
from .storage import save_goal, load_goal

# Conversation states
SET_SURAH, SET_START, SET_END, SET_DAYS, CONFIRM = range(5)


async def start(update: Update, context: CallbackContext) -> None:
    """
    Send a welcome message and display the main menu.
    """
    user = update.effective_user
    keyboard = [
        [
            InlineKeyboardButton("Set Goal", callback_data="set_goal"),
            InlineKeyboardButton("Today", callback_data="today"),
        ],
        [
            InlineKeyboardButton("My Goal", callback_data="my_goal"),
            InlineKeyboardButton("Help", callback_data="help"),
        ],
    ]
    text = (
        f"Hello *{user.first_name or 'User'}*!\n\n"
        f"I'm *{BOT_NAME}*, your Quran Hifz assistant.\n\n"
        "Choose an option or use commands:\n"
        "• /set_goal – Set a new goal\n"
        "• /my_goal – View your current goal\n"
        "• /today – Today's portion\n"
        "• /help – Help"
    )
    await update.effective_message.reply_markdown(
        text, reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def help_cmd(update: Update, context: CallbackContext) -> None:
    """
    Display help and usage instructions.
    """
    text = (
        "*How to use the bot:*\n\n"
        "1. Use /set_goal to define a new Hifz goal.\n"
        "   You'll be guided step-by-step:\n"
        "   • Surah name\n"
        "   • Starting and ending ayah\n"
        "   • Duration in days\n\n"
        "2. Use /today to see your current portion.\n"
        "3. Use /my_goal to see your current goal.\n\n"
        "You can reset your goal anytime by using /set_goal."
    )
    await update.effective_message.reply_markdown(text)


async def set_goal_entry(update: Update, context: CallbackContext) -> int:
    """
    Initiate the goal setting process.
    """
    if update.callback_query:
        await update.callback_query.answer()
        msg = update.callback_query.message
    else:
        msg = update.effective_message

    await msg.reply_text(
        "Let's set a new Hifz goal.\n\n"
        "First, send me the *Surah name* (e.g. Al-Baqarah):"
    )
    return SET_SURAH


async def set_goal_surah(update: Update, context: CallbackContext) -> int:
    surah = update.effective_message.text.strip()
    context.user_data["goal_surah"] = surah
    await update.effective_message.reply_text(
        f"Surah: *{surah}*\n\nNow send the *first ayah number* (e.g. 1):",
        parse_mode="Markdown",
    )
    return SET_START


async def set_goal_start(update: Update, context: CallbackContext) -> int:
    try:
        start_ayah = int(update.effective_message.text.strip())
        if start_ayah <= 0:
            raise ValueError
    except ValueError:
        await update.effective_message.reply_text(
            "Please send a *positive number* for the first ayah."
        )
        return SET_START

    context.user_data["goal_start"] = start_ayah
    await update.effective_message.reply_text(
        "Great! Now send the *last ayah number* in this goal:",
        parse_mode="Markdown",
    )
    return SET_END


async def set_goal_end(update: Update, context: CallbackContext) -> int:
    try:
        end_ayah = int(update.effective_message.text.strip())
        if end_ayah <= 0:
            raise ValueError
    except ValueError:
        await update.effective_message.reply_text(
            "Please send a *positive number* for the last ayah."
        )
        return SET_END

    start_ayah = context.user_data.get("goal_start", 1)
    if end_ayah < start_ayah:
        await update.effective_message.reply_text(
            "The last ayah must be *greater than or equal* to the first ayah."
        )
        return SET_END

    context.user_data["goal_end"] = end_ayah
    await update.effective_message.reply_text(
        "Almost done!\n\nHow many *days* do you want to finish this part in?",
        parse_mode="Markdown",
    )
    return SET_DAYS


async def set_goal_days(update: Update, context: CallbackContext) -> int:
    try:
        days = int(update.effective_message.text.strip())
        if days <= 0:
            raise ValueError
    except ValueError:
        await update.effective_message.reply_text(
            "Please send a *positive number* of days."
        )
        return SET_DAYS

    context.user_data["goal_days"] = days

    surah = context.user_data["goal_surah"]
    start_ayah = context.user_data["goal_start"]
    end_ayah = context.user_data["goal_end"]
    total = end_ayah - start_ayah + 1
    per_day = max(1, (total + days - 1) // days)

    text = (
        "Please confirm your goal:\n\n"
        f"• Surah: *{surah}*\n"
        f"• From ayah: *{start_ayah}*\n"
        f"• To ayah: *{end_ayah}*\n"
        f"• Total ayahs: *{total}*\n"
        f"• Duration: *{days}* days\n"
        f"• ≈ Ayahs per day: *{per_day}*\n"
    )
    keyboard = [
        [
            InlineKeyboardButton("Confirm", callback_data="confirm_goal"),
            InlineKeyboardButton("Cancel", callback_data="cancel_goal"),
        ]
    ]
    await update.effective_message.reply_markdown(
        text, reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return CONFIRM


async def set_goal_confirm(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    await query.answer()

    if query.data == "cancel_goal":
        await query.edit_message_text("Goal creation cancelled.")
        context.user_data.clear()
        return ConversationHandler.END

    surah = context.user_data["goal_surah"]
    start_ayah = context.user_data["goal_start"]
    end_ayah = context.user_data["goal_end"]
    days = context.user_data["goal_days"]
    goal = HifzGoal(
        surah=surah,
        start_ayah=start_ayah,
        end_ayah=end_ayah,
        days=days,
        start_date=date.today().isoformat(),
    )
    save_goal(update.effective_user.id, goal)
    context.user_data.clear()

    from_ayah, to_ayah, finished = compute_today_portion(goal)
    today_text = (
        f"New goal saved!\n\n"
        f"Surah *{goal.surah}* from ayah *{goal.start_ayah}* to *{goal.end_ayah}* "
        f"in *{goal.days}* days.\n\n"
        f"Today's portion (Day 1):\n"
        f"→ Ayahs *{from_ayah}* to *{to_ayah}*"
    )
    await query.edit_message_text(today_text, parse_mode="Markdown")
    return ConversationHandler.END


async def set_goal_cancel(update: Update, context: CallbackContext) -> int:
    await update.effective_message.reply_text("Goal creation cancelled.")
    context.user_data.clear()
    return ConversationHandler.END


def _format_goal(goal: HifzGoal) -> str:
    return (
        f"Your current goal:\n\n"
        f"• Surah: *{goal.surah}*\n"
        f"• From ayah: *{goal.start_ayah}*\n"
        f"• To ayah: *{goal.end_ayah}*\n"
        f"• Total ayahs: *{goal.total_ayahs}*\n"
        f"• Duration: *{goal.days}* days\n"
        f"• Start date: *{goal.start_date}*"
    )


async def my_goal(update: Update, context: CallbackContext) -> None:
    goal = load_goal(update.effective_user.id)
    if not goal:
        await update.effective_message.reply_text(
            "You don't have a goal yet.\nUse /set_goal to create one."
        )
        return

    await update.effective_message.reply_markdown(_format_goal(goal))


async def today(update: Update, context: CallbackContext) -> None:
    goal = load_goal(update.effective_user.id)
    if not goal:
        await update.effective_message.reply_text(
            "You don't have a goal yet.\nUse /set_goal first."
        )
        return

    today_date = date.today()
    from_ayah, to_ayah, finished = compute_today_portion(goal, today_date)

    if finished:
        await update.effective_message.reply_markdown(
            "*MashaAllah!*\n\n"
            "You have finished your current goal.\n"
            "You can set a new one with /set_goal."
        )
        return

    start = date.fromisoformat(goal.start_date)
    day_index = (today_date - start).days + 1

    text = (
        f"Today's portion – Day {day_index}\n\n"
        f"Surah *{goal.surah}*\n"
        f"Ayahs *{from_ayah}* to *{to_ayah}*\n\n"
        "May Allah make it easy for you."
    )
    await update.effective_message.reply_markdown(text)


async def menu_buttons(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()

    if query.data == "set_goal":
        fake_update = Update(
            update.update_id,
            message=query.message,
        )
        return await set_goal_entry(fake_update, context)

    if query.data == "today":
        await today(update, context)
    elif query.data == "my_goal":
        await my_goal(update, context)
    elif query.data == "help":
        await help_cmd(update, context)
