from __future__ import annotations

import logging
from typing import Dict

from telegram import (
    Update,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from telegram.ext import ContextTypes

from .config import CURRENCY, ADMIN_CHAT_ID
from .products import PRODUCTS


def _build_products_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        [
            InlineKeyboardButton(
                f"{p['name']} — {p['price']}", callback_data=f"prod:{pid}"
            )
        ]
        for pid, p in PRODUCTS.items()
    ]
    return InlineKeyboardMarkup(buttons)


def _get_cart(context: ContextTypes.DEFAULT_TYPE) -> Dict[str, int]:
    cart = context.user_data.get("cart")
    if not isinstance(cart, dict):
        cart = {}
        context.user_data["cart"] = cart
    return cart


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    name = user.first_name if user else "Friend"

    text = (
        f"Hello *{name}*!\n\n"
        "Welcome to *The Mini Shop*!\n\n"
        "Available commands:\n"
        "• /products — Show products\n"
        "• /cart — View cart\n"
        "• /checkout — Submit your order\n"
        "• /clear — Empty the cart"
    )
    await update.effective_message.reply_markdown(text)


async def cmd_products(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = "*Product list:*\n\nClick a product for more details."
    await update.effective_message.reply_markdown(text, reply_markup=_build_products_keyboard())


async def cmd_cart(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    cart = _get_cart(context)
    if not cart:
        await update.effective_message.reply_text("Your cart is currently empty.")
        return

    lines = ["*Current Cart:*\n"]
    total = 0.0

    for pid, qty in cart.items():
        product = PRODUCTS.get(pid)
        if not product:
            continue

        price = float(product["price"])
        line_total = price * qty
        total += line_total

        lines.append(f"• {product['name']} × {qty} = {line_total:.2f} {CURRENCY}")

    lines.append(f"\n*Total:* {total:.2f} {CURRENCY}")
    await update.effective_message.reply_markdown("\n".join(lines))


async def cmd_clear(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    context.user_data["cart"] = {}
    await update.effective_message.reply_text("Cart has been cleared.")


async def cmd_checkout(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    cart = _get_cart(context)
    if not cart:
        await update.effective_message.reply_text("Your cart is empty.")
        return

    user = update.effective_user
    lines = ["*New Order*"]
    if user:
        lines.append(f"👤: {user.first_name} (id={user.id})")

    total = 0.0
    for pid, qty in cart.items():
        product = PRODUCTS.get(pid)
        if not product:
            continue

        price = float(product["price"])
        line_total = price * qty
        total += line_total

        lines.append(f"• {product['name']} × {qty} = {line_total:.2f} {CURRENCY}")

    lines.append(f"\n*Total:* {total:.2f} {CURRENCY}")

    if ADMIN_CHAT_ID:
        try:
            await context.bot.send_message(
                chat_id=int(ADMIN_CHAT_ID),
                text="\n".join(lines),
                parse_mode="Markdown"
            )
        except Exception as e:
            logging.getLogger(__name__).error(f"Failed to send admin message: {e}")

    await update.effective_message.reply_text("Your order has been submitted. Thank you!")
    context.user_data["cart"] = {}


async def product_details(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    q = update.callback_query
    await q.answer()

    _, pid = q.data.split(":")
    product = PRODUCTS.get(pid)
    if not product:
        await q.edit_message_text("Product not found.")
        return

    text = (
        f"{product['name']}\n\n"
        f"{product['description']}\n\n"
        f"Price: {product['price']} {CURRENCY}"
    )

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("Add to cart", callback_data=f"add:{pid}")],
        [InlineKeyboardButton("Back", callback_data="back:products")],
    ])

    await q.edit_message_text(text=text, reply_markup=keyboard)


async def add_to_cart(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    q = update.callback_query
    _, pid = q.data.split(":")

    cart = _get_cart(context)
    cart[pid] = cart.get(pid, 0) + 1

    await q.answer("Product added to cart!", show_alert=False)


async def back_to_products(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    q = update.callback_query
    await q.answer()
    await q.edit_message_text(
        text="*Product list:*",
        parse_mode="Markdown",
        reply_markup=_build_products_keyboard(),
    )