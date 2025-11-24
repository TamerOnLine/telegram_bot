from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Optional

from .config import GOALS_FILE
from .models import HifzGoal


def _load_all_goals() -> Dict[str, Any]:
    """
    Load all saved Hifz goals from the goals file.

    Returns:
        Dict[str, Any]: Dictionary of user IDs to goal data.
    """
    if not GOALS_FILE.exists():
        return {}
    try:
        return json.loads(GOALS_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _save_all_goals(data: Dict[str, Any]) -> None:
    """
    Save all Hifz goals to the goals file.

    Args:
        data (Dict[str, Any]): Dictionary of user goals to be saved.
    """
    GOALS_FILE.write_text(
        json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def save_goal(user_id: int, goal: HifzGoal) -> None:
    """
    Save a user's Hifz goal.

    Args:
        user_id (int): Telegram user ID.
        goal (HifzGoal): Goal object to save.
    """
    data = _load_all_goals()
    data[str(user_id)] = {
        "surah": goal.surah,
        "start_ayah": goal.start_ayah,
        "end_ayah": goal.end_ayah,
        "days": goal.days,
        "start_date": goal.start_date,
    }
    _save_all_goals(data)


def load_goal(user_id: int) -> Optional[HifzGoal]:
    """
    Load a user's saved Hifz goal.

    Args:
        user_id (int): Telegram user ID.

    Returns:
        Optional[HifzGoal]: The loaded goal or None if not found.
    """
    data = _load_all_goals()
    raw = data.get(str(user_id))
    if not raw:
        return None
    return HifzGoal(**raw)
