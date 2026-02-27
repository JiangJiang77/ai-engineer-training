from __future__ import annotations

from typing import Any, Callable, Dict, List


def run_agent(
    messages: List[Dict[str, str]],
    query: str,
    tools: Dict[str, Callable[..., Dict[str, Any]]],
    max_retries: int,
    base_delay: float,
    sleep_fn: Callable[[float], None],
    logger: List[str],
) -> Dict[str, Any]:
    raise NotImplementedError
