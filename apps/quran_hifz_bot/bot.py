from __future__ import annotations
from telegram.ext import Application, CommandHandler, MessageHandler, filters

from .config import BOT_TOKEN, BOT_NAME, logger
from .commands import (
    cmd_start, cmd_help, cmd_set_role_student, cmd_set_role_teacher,
    cmd_set_goal, cmd_my_goal, cmd_today
)
from .handlers import handle_text


def main():
    logger.info("Starting bot: %s", BOT_NAME)

    app = Application.builder().token(BOT_TOKEN).build()

    # Commands
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("help", cmd_help))
    app.add_handler(CommandHandler("set_role_student", cmd_set_role_student))
    app.add_handler(CommandHandler("set_role_teacher", cmd_set_role_teacher))
    app.add_handler(CommandHandler("set_goal", cmd_set_goal))
    app.add_handler(CommandHandler("my_goal", cmd_my_goal))
    app.add_handler(CommandHandler("today", cmd_today))

    # Text messages
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    app.run_polling()


if __name__ == "__main__":
    main()
