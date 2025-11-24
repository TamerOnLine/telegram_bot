from __future__ import annotations

from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
)

from .config import BOT_TOKEN, BOT_NAME, logger
from .handlers import (
    cmd_start,
    cmd_products,
    cmd_cart,
    cmd_clear,
    cmd_checkout,
    product_details,
    add_to_cart,
    back_to_products,
)


def main() -> None:
    logger.info("Starting bot: %s", BOT_NAME)

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # أوامر
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("products", cmd_products))
    app.add_handler(CommandHandler("cart", cmd_cart))
    app.add_handler(CommandHandler("clear", cmd_clear))
    app.add_handler(CommandHandler("checkout", cmd_checkout))

    # أزرار
    app.add_handler(CallbackQueryHandler(product_details, pattern=r"^prod:"))
    app.add_handler(CallbackQueryHandler(add_to_cart, pattern=r"^add:"))
    app.add_handler(CallbackQueryHandler(back_to_products, pattern=r"^back:products$"))

    logger.info("Shop bot is running...")
    app.run_polling()


if __name__ == "__main__":
    main()
