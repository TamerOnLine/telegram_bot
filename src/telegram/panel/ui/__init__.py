from __future__ import annotations

from typing import Callable, Optional

# Type alias for a function that resolves the final chat_id.
# This function takes two arguments:
# - a required `str` (possibly a user ID or identifier),
# - an optional `str` (possibly a context or namespace),
# and returns an optional `str` (the resolved chat_id).
ResolveTargetFn = Callable[[str, Optional[str]], Optional[str]]
