from __future__ import annotations
from telegram import Update
from telegram.ext import ContextTypes
from .storage import get_user_record, update_user_record
from .helpers import make_main_keyboard


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    msg = update.effective_message
    if not user:
        return

    rec = get_user_record(user.id)
    role = rec.get("role", "student")

    text = (
        f"👋 *مرحباً {user.first_name or 'أخي'}!*\n\n"
        "هذا بوت *تحفيظ القرآن*.\n\n"
        "يمكنك استخدامه كطالب أو معلّم.\n\n"
        "الأوامر:\n"
        "/help\n/set_role_student\n/set_role_teacher\n/set_goal\n/today\n/my_goal\n"
    )

    await msg.reply_text(
        text, parse_mode="Markdown", reply_markup=make_main_keyboard(role)
    )


async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.effective_message.reply_text(
        "📚 *مساعدة بوت التحفيظ*\n\n"
        "/set_role_student\n/set_role_teacher\n/set_goal\n/today\n/my_goal\n",
        parse_mode="Markdown",
    )


async def cmd_set_role_student(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    update_user_record(user.id, {"role": "student"})
    await update.effective_message.reply_text(
        "✅ تم اختيار وضع الطالب.",
        parse_mode="Markdown",
        reply_markup=make_main_keyboard("student"),
    )


async def cmd_set_role_teacher(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    update_user_record(user.id, {"role": "teacher"})
    await update.effective_message.reply_text(
        "✅ تم اختيار وضع المعلّم.",
        parse_mode="Markdown",
        reply_markup=make_main_keyboard("teacher"),
    )


async def cmd_set_goal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    msg = update.effective_message

    if context.args:
        goal_text = " ".join(context.args)
        update_user_record(user.id, {"goal": goal_text})
        await msg.reply_text(f"🎯 تم حفظ هدفك:\n\n{goal_text}")
        return

    context.user_data["awaiting_goal"] = True
    await msg.reply_text(
        "اكتب هدف الحفظ الآن (مثال: حفظ سورة الملك خلال أسبوعين).",
        parse_mode="Markdown",
    )


async def cmd_my_goal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    rec = get_user_record(user.id)
    goal = rec.get("goal")
    if not goal:
        await update.effective_message.reply_text("لا يوجد هدف محدد.")
    else:
        await update.effective_message.reply_text(f"🎯 هدفك الحالي:\n\n{goal}")


async def cmd_today(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["awaiting_today"] = True
    await update.effective_message.reply_text(
        "اكتب ماذا حفظت اليوم.",
        parse_mode="Markdown",
    )
