from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Tuple


@dataclass
class HifzGoal:
    surah: str
    start_ayah: int
    end_ayah: int
    days: int
    start_date: str  # ISO format: YYYY-MM-DD

    @property
    def total_ayahs(self) -> int:
        """
        Calculate the total number of ayahs in the goal.

        Returns:
            int: Total ayah count.
        """
        return max(0, self.end_ayah - self.start_ayah + 1)


def compute_today_portion(
    goal: HifzGoal, today: date | None = None
) -> Tuple[int, int, bool]:
    """
    Compute the ayahs to be memorized for today based on the goal.

    Args:
        goal (HifzGoal): The memorization goal.
        today (date | None): The current date. Defaults to today.

    Returns:
        Tuple[int, int, bool]:
            from_ayah (int): Starting ayah for today.
            to_ayah (int): Ending ayah for today.
            finished (bool): True if the goal is completed.
    """
    if today is None:
        today = date.today()

    start = date.fromisoformat(goal.start_date)
    days_passed = (today - start).days
    if days_passed < 0:
        days_passed = 0

    total = goal.total_ayahs
    per_day = max(1, (total + goal.days - 1) // goal.days)  # Ceiling division

    start_offset = days_passed * per_day
    if start_offset >= total:
        return goal.end_ayah + 1, goal.end_ayah + 1, True

    from_ayah = goal.start_ayah + start_offset
    to_ayah = min(goal.end_ayah, from_ayah + per_day - 1)
    finished = to_ayah >= goal.end_ayah and days_passed >= goal.days - 1
    return from_ayah, to_ayah, finished