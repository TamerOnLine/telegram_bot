import argparse
import sys
from pathlib import Path

# 🔹 BASE_DIR = مجلد المشروع الرئيسي (telegram/)
BASE_DIR = Path(__file__).resolve().parent
if (BASE_DIR / "src").exists():
    PROJECT_ROOT = BASE_DIR
else:
    # لو حطيته في مجلد آخر داخل المشروع
    PROJECT_ROOT = Path(__file__).resolve().parents[1]

SRC_DIR = PROJECT_ROOT / "src"
sys.path.insert(0, str(SRC_DIR))

from telegram.telegram_utils import (  # type: ignore
    ME_ID,
    CHANNEL_ID,
    GROUP_ID,
    send_text,
    send_markdown,
    send_photo,
    send_voice,
)


def resolve_target(to: str, chat_id_arg: str | None) -> int | str:
    """
    اختيار الـ chat_id ديناميكياً حسب --to أو --chat-id
    """
    if to == "me":
        if not ME_ID:
            raise RuntimeError("TELEGRAM_ME_ID غير موجود في .env")
        return ME_ID

    if to == "channel":
        if not CHANNEL_ID:
            raise RuntimeError("TELEGRAM_CHANNEL_ID غير موجود في .env")
        return CHANNEL_ID

    if to == "group":
        if not GROUP_ID:
            raise RuntimeError("TELEGRAM_GROUP_ID غير موجود في .env")
        return GROUP_ID

    if to == "custom":
        if not chat_id_arg:
            raise RuntimeError("--chat-id مطلوب عندما يكون --to=custom")
        return chat_id_arg

    raise RuntimeError(f"Target غير معروف: {to}")


def main():
    parser = argparse.ArgumentParser(
        description="🚀 إرسال رسائل/صور/صوت ديناميكياً عبر Telegram Bot"
    )
    parser.add_argument(
        "--to",
        choices=["me", "channel", "group", "custom"],
        required=True,
        help="الهدف: me / channel / group / custom",
    )
    parser.add_argument(
        "--chat-id",
        help="يستخدم فقط إذا كان --to=custom (ID مباشر لأي شات)",
    )
    parser.add_argument(
        "--text",
        help="نص الرسالة (اختياري)",
    )
    parser.add_argument(
        "--markdown",
        action="store_true",
        help="تفسير النص كـ Markdown",
    )
    parser.add_argument(
        "--photo",
        help="مسار صورة لإرسالها",
    )
    parser.add_argument(
        "--voice",
        help="مسار ملف صوتي (voice) لإرساله",
    )

    args = parser.parse_args()

    # 1️⃣ حدد الـ chat_id ديناميكياً
    chat_id = resolve_target(args.to, args.chat_id)
    print(f"🎯 Sending to: {chat_id} (target={args.to})")

    # 2️⃣ إرسال نص (إن وجد)
    if args.text:
        if args.markdown:
            print("💬 Sending markdown text...")
            send_markdown(chat_id, args.text)
        else:
            print("💬 Sending plain text...")
            send_text(chat_id, args.text)

    # 3️⃣ إرسال صورة (إن وجد)
    if args.photo:
        photo_path = Path(args.photo).expanduser().resolve()
        if not photo_path.exists():
            print(f"⚠️ الصورة غير موجودة: {photo_path}")
        else:
            print(f"🖼 Sending photo: {photo_path}")
            send_photo(chat_id, str(photo_path), caption=args.text or "")

    # 4️⃣ إرسال صوت (إن وجد)
    if args.voice:
        voice_path = Path(args.voice).expanduser().resolve()
        if not voice_path.exists():
            print(f"⚠️ الصوت غير موجود: {voice_path}")
        else:
            print(f"🎧 Sending voice: {voice_path}")
            send_voice(chat_id, str(voice_path), caption=args.text or "")

    if not args.text and not args.photo and not args.voice:
        print("⚠️ لا يوجد text / photo / voice لإرساله 😅")


if __name__ == "__main__":
    main()
