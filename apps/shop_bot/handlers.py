from __future__ import annotations

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from products import PRODUCTS
from config import ADMIN_CHAT_ID
from db import save_order

from core.db import upsert_chat


# =============================================
# Helpers
# =============================================

def _get_cart(context: ContextTypes.DEFAULT_TYPE) -> dict:
    return context.user_data.setdefault("cart", {})


def _add_item(cart: dict, pid: str, qty: int = 1) -> None:
    cart[pid] = cart.get(pid, 0) + qty


def _track_chat(update: Update) -> None:
    """
    تسجيل الشات في جدول bot_chats (مشترك لكل البوتات).
    نستخدم فقط قيم بسيطة، وليس كائن Chat نفسه.
    """
    chat = update.effective_chat
    if chat is None:
        return

    upsert_chat(
        bot_name="shop_bot",                 # 👈 اسم البوت
        chat_id=chat.id,
        chat_type=chat.type,
        title=getattr(chat, "title", None),
        username=getattr(chat, "username", None),
    )


# =============================================
# Handlers
# =============================================

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    _track_chat(update)

    await update.effective_message.reply_text(
        "Welcome to the Store Bot!\n\n"
        "Use /products to browse our items."
    )


async def cmd_products(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    _track_chat(update)

    keyboard: list[list[InlineKeyboardButton]] = []
    for pid, item in PRODUCTS.items():
        keyboard.append(
            [
                InlineKeyboardButton(
                    f"{item['name']} – {item['price']}€",
                    callback_data=f"product_{pid}",
                )
            ]
        )

    await update.effective_message.reply_text(
        "Our products:",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


async def product_details(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    _track_chat(update)

    query = update.callback_query
    await query.answer()

    pid = (query.data or "").replace("product_", "")
    product = PRODUCTS.get(pid)
    if not product:
        await query.edit_message_text("Product not found.")
        return

    keyboard = [
        [InlineKeyboardButton("Add to Cart", callback_data=f"add_{pid}")],
        [InlineKeyboardButton("Back", callback_data="back")],
    ]

    await query.edit_message_text(
        f"{product['name']}\n\nPrice: {product['price']}€",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


async def add_to_cart(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    _track_chat(update)

    query = update.callback_query
    await query.answer()

    pid = (query.data or "").replace("add_", "")
    cart = _get_cart(context)
    _add_item(cart, pid)

    await query.edit_message_text("Added to cart! Use /cart to view your items.")


async def back_to_products(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    _track_chat(update)
    await cmd_products(update, context)


async def cmd_cart(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    _track_chat(update)

    cart = _get_cart(context)
    if not cart:
        await update.effective_message.reply_text("Your cart is empty.")
        return

    lines: list[str] = ["Your cart:\n"]
    total = 0.0

    for pid, qty in cart.items():
        product = PRODUCTS.get(pid)
        if not product:
            continue
        price = float(product["price"])
        line_total = qty * price
        total += line_total
        lines.append(f"{product['name']} × {qty} = {line_total:.2f}€")

    lines.append(f"\nTotal: {total:.2f}€")
    lines.append("\nUse /checkout to submit your order.")

    await update.effective_message.reply_text("\n".join(lines))


async def cmd_clear(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    _track_chat(update)

    context.user_data["cart"] = {}
    await update.effective_message.reply_text("Cart cleared.")


async def cmd_checkout(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    _track_chat(update)

    cart = _get_cart(context)
    if not cart:
        await update.effective_message.reply_text("Your cart is empty.")
        return

    user = update.effective_user
    if user is None:
        await update.effective_message.reply_text("User not found.")
        return

    lines: list[str] = ["New Order:\n"]
    total = 0.0

    for pid, qty in cart.items():
        product = PRODUCTS.get(pid)
        if not product:
            continue
        price = float(product["price"])
        line_total = qty * price
        total += line_total
        lines.append(f"{product['name']} × {qty} = {line_total:.2f}€")

    order_text = "\n".join(lines)

    save_order(
        user_id=user.id,
        username=user.username or "",
        full_name=user.full_name or "",
        details=order_text,
        total=total,
    )

    if ADMIN_CHAT_ID:
        await context.bot.send_message(ADMIN_CHAT_ID, order_text)

    await update.effective_message.reply_text(
        "Your order has been submitted. Thank you!"
    )

    context.user_data["cart"] = {}
