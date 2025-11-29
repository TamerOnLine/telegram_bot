from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import os

# قراءة التوكن من ملف .env الموجود في نفس المجلد
TOKEN = os.getenv("BOT_TOKEN")

# رابط اللعبة (عدّله حسب مكان رفع اللعبة)
# مثال: رابط محلي عندما تشغّل السيرفر على الكمبيوتر
GAME_URL = "http://192.168.1.24:8000/index.html"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton("🎮 العب لعبة Pi", url=GAME_URL)]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "مرحبًا! اضغط على الزر لبدأ لعب لعبة Pi HTML5 🎮",
        reply_markup=reply_markup
    )

async def game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton("🎮 افتح اللعبة", url=GAME_URL)]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "اضغط لفتح اللعبة 👇",
        reply_markup=reply_markup
    )

def main():
    app = ApplicationBuilder().token(TOKEN).build()

    # الأوامر
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("game", game))

    app.run_polling()

if __name__ == "__main__":
    main()
