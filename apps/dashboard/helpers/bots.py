# apps/dashboard/helpers/bots.py
from __future__ import annotations

from pathlib import Path
from typing import Dict, List

from dotenv import dotenv_values

from apps.dashboard.helpers.paths import get_apps_dir


def discover_bots() -> List[Dict[str, str]]:
    """
    يبحث عن كل البوتات داخل apps/* التي تحتوي على:
      - bot.py
      - .env فيه TELEGRAM_BOT_TOKEN

    ويقرأ من .env (اختياريًا):
      BOT_NAME, BOT_USERNAME, BOT_DESCRIPTION, SERVICE_NAME
    """
    bots: List[Dict[str, str]] = []

    apps_dir: Path = get_apps_dir()
    if not apps_dir.exists():
        return bots

    for bot_dir in sorted(apps_dir.iterdir()):
        if not bot_dir.is_dir():
            continue

        bot_file = bot_dir / "bot.py"
        env_file = bot_dir / ".env"

        if not bot_file.exists() or not env_file.exists():
            continue

        env_data = dotenv_values(env_file)

        token = env_data.get("TELEGRAM_BOT_TOKEN", "")
        if not token:
            # بدون توكن لا نعتبره بوت جاهز
            continue

        bots.append(
            {
                "folder": bot_dir.name,
                "env_path": str(env_file),
                "bot_name": env_data.get("BOT_NAME", bot_dir.name),
                "bot_username": env_data.get("BOT_USERNAME", ""),
                "bot_description": env_data.get("BOT_DESCRIPTION", ""),
                "token": token,
                "service_name": env_data.get("SERVICE_NAME", ""),  # اختياري
            }
        )

    return bots
