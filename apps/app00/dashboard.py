import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Dict, Any

import requests
import streamlit as st
from dotenv import load_dotenv

# تحميل متغيرات البيئة من .env (لأجل token_env وغيرها)
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent
CONFIG_PATH = BASE_DIR / "bots_config.json"


@dataclass
class BotConfig:
    name: str
    token_env: str
    me_id: Optional[int] = None
    channel_id: Optional[int] = None
    group_id: Optional[int] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BotConfig":
        return cls(
            name=data["name"],
            token_env=data["token_env"],
            me_id=data.get("me_id"),
            channel_id=data.get("channel_id"),
            group_id=data.get("group_id"),
        )


class TelegramBotClient:
    def __init__(self, config: BotConfig):
        self.config = config
        token = os.getenv(config.token_env)
        if not token:
            raise RuntimeError(
                f"Environment variable {config.token_env} is not set or empty."
            )
        self.token = token
        self.base_url = f"https://api.telegram.org/bot{self.token}"

    def send_message(
        self,
        chat_id: int | str,
        text: str,
        parse_mode: Optional[str] = None,
        disable_web_page_preview: bool = False,
    ) -> Dict[str, Any]:
        payload: Dict[str, Any] = {
            "chat_id": chat_id,
            "text": text,
            "disable_web_page_preview": disable_web_page_preview,
        }
        if parse_mode:
            payload["parse_mode"] = parse_mode

        r = requests.post(
            f"{self.base_url}/sendMessage",
            data=payload,
            timeout=15,
        )
        try:
            return r.json()
        except Exception:
            return {"ok": False, "error": "Invalid JSON response", "status": r.status_code}

    def get_me(self) -> Dict[str, Any]:
        r = requests.get(f"{self.base_url}/getMe", timeout=10)
        try:
            return r.json()
        except Exception:
            return {"ok": False, "error": "Invalid JSON response", "status": r.status_code}


@st.cache_data
def load_bots_config() -> list[BotConfig]:
    if not CONFIG_PATH.exists():
        raise FileNotFoundError(
            f"bots_config.json not found at: {CONFIG_PATH}\n"
            "Create it based on the example in the README."
        )
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        raw = json.load(f)

    bots_raw = raw.get("bots", [])
    configs: list[BotConfig] = [BotConfig.from_dict(b) for b in bots_raw]
    return configs


def main() -> None:
    st.set_page_config(
        page_title="Telegram Bot Dashboard",
        page_icon="🤖",
        layout="wide",
    )

    st.title("🤖 لوحة تحكم البوتات - Telegram Bot Dashboard")

    # تحميل الإعدادات
    try:
        bot_configs = load_bots_config()
    except Exception as e:
        st.error(f"تعذّر تحميل bots_config.json:\n\n{e}")
        st.stop()

    if not bot_configs:
        st.warning("ملف bots_config.json لا يحتوي على أي بوتات (قائمة bots فارغة).")
        st.stop()

    # الشريط الجانبي: اختيار بوت أو أكثر
    st.sidebar.header("الإعدادات")

    bot_names = [cfg.name for cfg in bot_configs]
    selected_bot_names = st.sidebar.multiselect(
        "اختر البوت/البوتات للإرسال:",
        options=bot_names,
        default=[bot_names[0]],
    )

    if not selected_bot_names:
        st.info("اختر على الأقل بوتًا واحدًا من القائمة الجانبية.")
        st.stop()

    # خريطة من الاسم إلى config
    name_to_config: Dict[str, BotConfig] = {cfg.name: cfg for cfg in bot_configs}
    selected_configs = [name_to_config[n] for n in selected_bot_names]

    # وضع عام للإرسال
    st.sidebar.subheader("خيار الإرسال")
    target_mode = st.sidebar.radio(
        "الجهة المستهدفة:",
        options=["me", "channel", "group", "custom_chat_id"],
        format_func=lambda x: {
            "me": "حسابي الشخصي (me_id)",
            "channel": "القناة (channel_id)",
            "group": "المجموعة (group_id)",
            "custom_chat_id": "معرّف مخصص (chat_id)",
        }[x],
    )

    parse_mode = st.sidebar.selectbox(
        "نوع التنسيق (parse_mode):",
        options=["None", "Markdown", "HTML"],
        index=0,
    )
    if parse_mode == "None":
        parse_mode_value: Optional[str] = None
    else:
        parse_mode_value = parse_mode

    disable_preview = st.sidebar.checkbox("إلغاء معاينة الروابط (disable_web_page_preview)", value=False)

    st.sidebar.markdown("---")
    st.sidebar.write("📄 ملف الإعدادات:", f"`{CONFIG_PATH.name}`")

    # الواجهة الرئيسية
    col_msg, col_status = st.columns([2, 1])

    with col_msg:
        st.subheader("✉️ إنشاء رسالة")

        message_text = st.text_area(
            "نص الرسالة",
            value="السلام عليكم ورحمة الله وبركاته 🌿",
            height=160,
        )

        custom_chat_id: Optional[str] = None
        if target_mode == "custom_chat_id":
            custom_chat_id = st.text_input(
                "أدخل chat_id (يمكن أن يكون رقمًا مثل -100123456 أو ID مستخدم):",
                value="",
            )

        send_button = st.button("🚀 إرسال الرسالة", type="primary")

    with col_status:
        st.subheader("ℹ️ حالة البوتات المحددة")

        for cfg in selected_configs:
            token_ok = bool(os.getenv(cfg.token_env))
            st.markdown(f"**🤖 {cfg.name}**")
            st.write(f"- متغير البيئة للـ token: `{cfg.token_env}`")
            st.write(f"- token موجود في البيئة؟ {'✅' if token_ok else '❌'}")
            st.write(f"- me_id: `{cfg.me_id}`")
            st.write(f"- channel_id: `{cfg.channel_id}`")
            st.write(f"- group_id: `{cfg.group_id}`")
            st.markdown("---")

    st.markdown("---")
    st.subheader("📜 سجل الإرسال (Logs)")

    if "logs" not in st.session_state:
        st.session_state["logs"] = []

    if send_button:
        if not message_text.strip():
            st.warning("الرجاء إدخال نص الرسالة قبل الإرسال.")
        elif target_mode == "custom_chat_id" and not (custom_chat_id and custom_chat_id.strip()):
            st.warning("لقد اخترت chat_id مخصص، الرجاء إدخال قيمة صالحة.")
        else:
            # تنفيذ الإرسال لكل بوت محدد
            results = []
            for cfg in selected_configs:
                try:
                    client = TelegramBotClient(cfg)
                except Exception as e:
                    results.append(
                        {
                            "bot": cfg.name,
                            "ok": False,
                            "error": str(e),
                        }
                    )
                    continue

                # تحديد chat_id بناءً على target_mode
                chat_id: Optional[int | str] = None
                if target_mode == "me":
                    chat_id = cfg.me_id
                elif target_mode == "channel":
                    chat_id = cfg.channel_id
                elif target_mode == "group":
                    chat_id = cfg.group_id
                elif target_mode == "custom_chat_id":
                    chat_id = custom_chat_id.strip() if custom_chat_id else None

                if chat_id is None:
                    results.append(
                        {
                            "bot": cfg.name,
                            "ok": False,
                            "error": f"chat_id غير معرّف لهذا البوت في الوضع: {target_mode}",
                        }
                    )
                    continue

                resp = client.send_message(
                    chat_id=chat_id,
                    text=message_text,
                    parse_mode=parse_mode_value,
                    disable_web_page_preview=disable_preview,
                )

                ok = bool(resp.get("ok"))
                error_text = None
                if not ok:
                    error_text = resp.get("description") or resp.get("error") or "Unknown error"

                results.append(
                    {
                        "bot": cfg.name,
                        "ok": ok,
                        "target": str(chat_id),
                        "response": resp,
                        "error": error_text,
                    }
                )

            # عرض النتائج + حفظها في logs
            for r in results:
                status_emoji = "✅" if r["ok"] else "❌"
                st.write(f"{status_emoji} **{r['bot']}** → chat_id = `{r.get('target', '-')}`")
                if r.get("error"):
                    st.code(str(r["error"]), language="bash")
                else:
                    st.json(r["response"])

            # تحديث السجل
            st.session_state["logs"].insert(
                0,
                {
                    "message": message_text,
                    "target_mode": target_mode,
                    "parse_mode": parse_mode_value,
                    "disable_preview": disable_preview,
                    "results": results,
                },
            )

    # عرض السجل
    if st.session_state["logs"]:
        for idx, entry in enumerate(st.session_state["logs"][:10], start=1):
            with st.expander(f"إرسال #{idx} - {entry['target_mode']}"):
                st.write("نص الرسالة:")
                st.code(entry["message"])
                st.write("النتائج:")
                for r in entry["results"]:
                    status_emoji = "✅" if r["ok"] else "❌"
                    st.write(f"{status_emoji} **{r['bot']}** → {r.get('target', '-')}")
                    if r.get("error"):
                        st.code(str(r["error"]), language="bash")
    else:
        st.info("لا يوجد سجلات إرسال بعد.")

if __name__ == "__main__":
    main()
