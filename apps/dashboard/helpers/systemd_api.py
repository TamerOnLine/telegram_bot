# apps/dashboard/helpers/systemd_api.py
from __future__ import annotations

import subprocess
from typing import Tuple


def run_systemctl(service: str, action: str) -> Tuple[bool, str]:
    """
    يشغّل أو يوقف أو يعيد تشغيل خدمة systemd.
    action ∈ {status, start, stop, restart}
    يعمل فقط على لينكس ويحتاج صلاحيات مناسبة.
    """
    if not service:
        return False, "❌ لم يتم تعريف SERVICE_NAME في ملف .env لهذا البوت."

    try:
        result = subprocess.run(
            ["sudo", "/usr/bin/systemctl", action, service],
            check=False,
            capture_output=True,
            text=True,
        )
    except FileNotFoundError:
        return False, "❌ systemctl غير متوفر (غالباً تعمل على ويندوز أو نظام بدون systemd)."

    out = (result.stdout or "") + (result.stderr or "")
    ok = result.returncode == 0
    return ok, out.strip() or "(لا يوجد مخرجات)"


def tail_journal(service: str, lines: int = 50) -> Tuple[bool, str]:
    """
    يجلب آخر N سطر من journalctl لهذه الخدمة.
    """
    if not service:
        return False, "❌ لم يتم تعريف SERVICE_NAME في ملف .env لهذا البوت."

    try:
        result = subprocess.run(
            ["journalctl", "-u", service, "--no-pager", f"-n{lines}"],
            check=False,
            capture_output=True,
            text=True,
        )
    except FileNotFoundError:
        return False, "❌ journalctl غير متوفر على هذا النظام."

    out = (result.stdout or "") + (result.stderr or "")
    ok = result.returncode == 0
    return ok, out.strip() or "(لا يوجد لوجات)"
