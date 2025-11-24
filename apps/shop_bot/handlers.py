from __future__ import annotations

import logging
from typing import Dict
from telegram import (
    Update,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from telegram.ext import (
    ContextTypes,
)

from .config import CURRENCY, ADMIN_CHAT_ID
from .products import PRODUCTS


# =========================
# أدوات داخلية
# =========================

def _build_products_keyboard() -> InlineKeyboardMarkup:
    buttons = []
    for pid, p in PRODUCTS.items():
        buttons.append([
            InlineKeyboardButton(
                f"{p['name']} — {p['price']}",
                callback_data=f"prod:{pid}",
            )
        ])
    return InlineKeyboardMarkup(buttons)


def _get_cart(context: ContextTypes.DEFAULT_TYPE) -> Dict[str, int]:
    cart = context.user_data.get("cart")
    if not isinstance(cart, dict):
        cart = {}
        context.user_data["cart"] = cart
    return cart


# =========================
# الأوامر
# =========================

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    name = user.first_name if user else "صديقي"

    text = (
        f"👋 أهلاً *{name}*!\n\n"
        "مرحباً بك في *المتجر الصغير* 🛍️\n\n"
        "الأوامر المتاحة:\n"
        "• /products — عرض المنتجات\n"
        "• /cart — عرض سلة المشتريات\n"
        "• /checkout — إرسال طلب الشراء\n"
        "• /clear — إفراغ السلة\n"
    )
    await update.effective_message.reply_markdown(text)


async def cmd_products(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = "🛍️ *قائمة المنتجات:*\n\nاضغط على أي منتج لمزيد من التفاصيل."
    await update.effective_message.reply_markdown(text, reply_markup=_build_products_keyboard())


async def cmd_cart(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    cart = _get_cart(context)
    if not cart:
        await update.effective_message.reply_text("🧺 سلة المشتريات فارغة حالياً.")
        return

    lines = ["🧺 *سلة المشتريات الحالية:*\n"]
    total = 0.0

    for pid, qty in cart.items():
        product = PRODUCTS.get(pid)
        if not product:
            continue

        price = float(product["price"])
        line_total = price * qty
        total += line_total

        lines.append(f"• {product['name']} × {qty} = {line_total:.2f} {CURRENCY}")

    lines.append(f"\n💵 *المجموع:* {total:.2f} {CURRENCY}")
    await update.effective_message.reply_markdown("\n".join(lines))


async def cmd_clear(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    context.user_data["cart"] = {}
    await update.effective_message.reply_text("🧹 تم إفراغ السلة بنجاح.")


async def cmd_checkout(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    cart = _get_cart(context)
    if not cart:
        await update.effective_message.reply_text("🧺 السلة فارغة.")
        return

    user = update.effective_user

    lines = ["🆕 *طلب جديد*"]
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

    lines.append(f"\n💵 *المجموع:* {total:.2f} {CURRENCY}")

    # إرسال الطلب للإدمن
    if ADMIN_CHAT_ID:
        try:
            await context.bot.send_message(
                chat_id=int(ADMIN_CHAT_ID),
                text="\n".join(lines),
                parse_mode="Markdown"
            )
        except Exception as e:
            logging.getLogger(__name__).error(f"Failed to send admin message: {e}")

    await update.effective_message.reply_text("✅ تم إرسال طلبك. شكراً لك!")
    context.user_data["cart"] = {}  # إفراغ بعد الطلب


# =========================
# الأزرار (Callbacks)
# =========================

async def product_details(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    q = update.callback_query
    await q.answer()

    _, pid = q.data.split(":")
    product = PRODUCTS.get(pid)
    if not product:
        await q.edit_message_text("❌ المنتج غير متوفر.")
        return

    text = (
        f"{product['name']}\n\n"
        f"{product['description']}\n\n"
        f"💰 السعر: {product['price']} {CURRENCY}"
    )

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("➕ أضف للسلة", callback_data=f"add:{pid}")],
        [InlineKeyboardButton("⬅️ رجوع", callback_data="back:products")],
    ])

    await q.edit_message_text(text=text, reply_markup=keyboard)


async def add_to_cart(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    q = update.callback_query

    # استخراج ID المنتج من callback_data
    _, pid = q.data.split(":")

    # تحديث السلة في user_data
    cart = _get_cart(context)
    cart[pid] = cart.get(pid, 0) + 1

    # تنبيه صغير للمستخدم فقط (بدون تعديل الرسالة)
    await q.answer("✅ تمت إضافة المنتج!", show_alert=False)
    # ❌ لا نستدعي product_details هنا



async def back_to_products(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    q = update.callback_query
    await q.answer()
    await q.edit_message_text(
        text="🛍️ *قائمة المنتجات:*",
        parse_mode="Markdown",
        reply_markup=_build_products_keyboard(),
    )
