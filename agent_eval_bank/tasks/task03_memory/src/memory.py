from __future__ import annotations

from typing import Dict, List


Message = Dict[str, str]


def compact_history(messages: List[Message], max_chars: int) -> List[Message]:
    """
    Compact conversation history into a character budget.
    """
    raise NotImplementedError
