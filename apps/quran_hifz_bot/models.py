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
    start_date: str  # ISO: YYYY-MM-DD

    @property
    def total_ayahs(self) -> int:
        return max(0, self.end_ayah - self.start_ayah + 1)


def compute_today_portion(
    goal: HifzGoal, today: date | None = None
) -> Tuple[int, int, bool]:
    """
    يرجع (from_ayah, to_ayah, finished_today)
    finished_today = True إذا انتهى المستخدم من الهدف.
    """
    if today is None:
        today = date.today()

    start = date.fromisoformat(goal.start_date)
    days_passed = (today - start).days
    if days_passed < 0:
        days_passed = 0

    total = goal.total_ayahs
    per_day = max(1, (total + goal.days - 1) // goal.days)  # ceil(total/days)

    start_offset = days_passed * per_day
    if start_offset >= total:
        return goal.end_ayah + 1, goal.end_ayah + 1, True

    from_ayah = goal.start_ayah + start_offset
    to_ayah = min(goal.end_ayah, from_ayah + per_day - 1)
    finished = to_ayah >= goal.end_ayah and days_passed >= goal.days - 1
    return from_ayah, to_ayah, finished
