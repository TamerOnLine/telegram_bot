from __future__ import annotations

from pathlib import Path
import tempfile

import PyPDF2
from telegram import Update
from telegram.ext import CommandHandler, MessageHandler, ContextTypes, filters

from src.telegram.panel.environment import load_environment

# 🔹 ملف .env الخاص بوحدة PDF
ENV_PATH = Path(__file__).resolve().parent / ".env"


async def cmd_pdf(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    msg = update.effective_message

    # تحميل بيئة pdf_chat لو كان فيها إعدادات خاصة
    load_environment(ENV_PATH)

    await msg.reply_text(
        "📄 وضع PDF:\n\n"
        "1️⃣ أرسل لي ملف PDF كمستند (Document).\n"
        "2️⃣ سأقوم بقراءة الملف وأعطيك:\n"
        "   • اسم الملف\n"
        "   • عدد الصفحات\n"
        "   • مقتطف من أول صفحة.\n\n"
        "لاحقًا يمكن إضافة أوامر مثل /ask للسؤال عن محتوى الملف."
    )


async def handle_pdf(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    msg = update.effective_message
    document = msg.document

    # تحميل بيئة pdf_chat هنا أيضاً (للأوامر المعتمدة على إعدادات env)
    load_environment(ENV_PATH)

    if not document:
        await msg.reply_text("⚠️ أرسل ملف PDF كمستند (Document).")
        return

    if document.mime_type not in ("application/pdf", None):
        await msg.reply_text("⚠️ الملف المرسل ليس PDF. أعد الإرسال كـ PDF.")
        return

    tg_file = await document.get_file()

    with tempfile.TemporaryDirectory() as tmpdir:
        pdf_path = Path(tmpdir) / (document.file_name or "file.pdf")
        await tg_file.download_to_drive(str(pdf_path))

        try:
            reader = PyPDF2.PdfReader(str(pdf_path))
        except Exception as e:
            await msg.reply_text(f"❌ تعذر قراءة ملف الـ PDF:\n{e}")
            return

        num_pages = len(reader.pages)

        preview_text = ""
        if num_pages > 0:
            try:
                first_page = reader.pages[0]
                preview_text = (first_page.extract_text() or "").strip()
            except Exception:
                preview_text = ""

        if not preview_text:
            preview_text = "لم أستطع استخراج نص من الصفحة الأولى (ربما يكون الملف ممسوح ضوئيًا أو محميًا)."

        max_chars = 700
        if len(preview_text) > max_chars:
            preview_text = preview_text[:max_chars] + "...\n\n(تم قص النص للعرض)"

    reply = (
        "✅ تم استلام ومعالجة ملف PDF.\n\n"
        f"📄 اسم الملف: {document.file_name}\n"
        f"📑 عدد الصفحات: {num_pages}\n\n"
        f"📝 مقتطف من الصفحة الأولى:\n\n"
        f"{preview_text}"
    )

    await msg.reply_text(reply)


def register_handlers(app) -> None:
    app.add_handler(CommandHandler("pdf", cmd_pdf))
    app.add_handler(MessageHandler(filters.Document.PDF, handle_pdf))
