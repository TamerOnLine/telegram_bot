from __future__ import annotations
import json
from typing import Any, Dict
from .config import DATA_FILE, logger


def load_data() -> Dict[str, Any]:
    if not DATA_FILE.exists():
        return {}
    try:
        with DATA_FILE.open("r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as exc:
        logger.error("Failed to load data.json: %s", exc)
        return {}


def save_data(data: Dict[str, Any]) -> None:
    try:
        with DATA_FILE.open("w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as exc:
        logger.error("Failed to save data.json: %s", exc)


def get_user_record(user_id: int) -> Dict[str, Any]:
    data = load_data()
    key = str(user_id)
    if key not in data:
        data[key] = {
            "role": "student",
            "goal": None,
            "today_memorized": [],
        }
        save_data(data)
    return data[key]


def update_user_record(user_id: int, updates: Dict[str, Any]) -> None:
    data = load_data()
    key = str(user_id)
    rec = data.get(key, {})
    rec.update(updates)
    data[key] = rec
    save_data(data)
