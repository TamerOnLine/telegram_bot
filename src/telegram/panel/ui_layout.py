from __future__ import annotations

from typing import Dict, Optional, Callable

from .ui import ResolveTargetFn
from .ui.layout import render_panel as _render_panel

def render_panel(telegram_ids: Dict[str, str], resolve_target: ResolveTargetFn) -> None:
    """
    Simple wrapper to maintain backward compatibility with legacy imports like:
    `from .panel.ui_layout import render_panel`

    Args:
        telegram_ids (Dict[str, str]): Dictionary of Telegram chat identifiers.
        resolve_target (ResolveTargetFn): Function to resolve the chat target.
    """
    _render_panel(telegram_ids, resolve_target)