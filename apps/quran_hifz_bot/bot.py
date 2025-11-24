from __future__ import annotations

from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ConversationHandler,
    MessageHandler,
    filters,
)

from .config import BOT_TOKEN, BOT_NAME, logger
from .handlers import (
    start,
    help_cmd,
    my_goal,
    today,
    menu_buttons,
    set_goal_entry,
    set_goal_surah,
    set_goal_start,
    set_goal_end,
    set_goal_days,
    set_goal_confirm,
    set_goal_cancel,
    SET_SURAH,
    SET_START,
    SET_END,
    SET_DAYS,
    CONFIRM,
)


def main() -> None:
    logger.info("Starting Quran Hifz bot...")

    app = (
        ApplicationBuilder()
        .token(BOT_TOKEN)
        .application_name(BOT_NAME)
        .build()
    )

    # أوامر بسيطة
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("my_goal", my_goal))
    app.add_handler(CommandHandler("today", today))

    # أزرار القائمة
    app.add_handler(
        CallbackQueryHandler(
            menu_buttons, pattern="^(set_goal|today|my_goal|help)$"
        )
    )

    # محادثة /set_goal
    conv = ConversationHandler(
        entry_points=[CommandHandler("set_goal", set_goal_entry)],
        states={
            SET_SURAH: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, set_goal_surah)
            ],
            SET_START: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, set_goal_start)
            ],
            SET_END: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, set_goal_end)
            ],
            SET_DAYS: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, set_goal_days)
            ],
            CONFIRM: [
                CallbackQueryHandler(
                    set_goal_confirm, pattern="^(confirm_goal|cancel_goal)$"
                )
            ],
        },
        fallbacks=[CommandHandler("cancel", set_goal_cancel)],
    )
    app.add_handler(conv)

    app.run_polling()


if __name__ == "__main__":
    main()
