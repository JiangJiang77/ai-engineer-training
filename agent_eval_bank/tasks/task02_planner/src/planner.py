from __future__ import annotations

from typing import Any, Iterable


def plan_steps(goal: str, tools: Iterable[str]) -> list[dict[str, Any]]:
    """
    Convert a goal into an ordered list of steps.
    """
    raise NotImplementedError
