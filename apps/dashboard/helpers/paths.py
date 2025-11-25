# apps/dashboard/helpers/paths.py
from __future__ import annotations

import sys
from functools import lru_cache
from pathlib import Path


@lru_cache(maxsize=1)
def get_project_root() -> Path:
    """
    يرجع جذر المشروع telegram_bot.

    هذا الملف موجود في:
      apps/dashboard/helpers/paths.py

    parents[0] -> helpers
    parents[1] -> dashboard
    parents[2] -> apps
    parents[3] -> telegram_bot  ✅
    """
    return Path(__file__).resolve().parents[3]


@lru_cache(maxsize=1)
def get_apps_dir() -> Path:
    """مسار مجلد apps/."""
    return get_project_root() / "apps"


@lru_cache(maxsize=1)
def get_dashboard_dir() -> Path:
    """مسار مجلد dashboard/."""
    return get_project_root() / "apps" / "dashboard"


def ensure_project_root_on_sys_path() -> None:
    """
    يضيف جذر المشروع إلى sys.path
    حتى نستطيع استيراد core.* و apps.* من أي ملف داخل dashboard.
    """
    root = str(get_project_root())
    if root not in sys.path:
        sys.path.insert(0, root)


# ✅ نستدعيها مباشرة عند الاستيراد
ensure_project_root_on_sys_path()
