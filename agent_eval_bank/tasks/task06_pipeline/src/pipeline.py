from __future__ import annotations

from typing import Any, Callable, Dict, List


def run_pipeline(
    steps: List[Dict[str, Any]],
    tools: Dict[str, Callable[..., Dict[str, Any]]],
) -> Dict[str, Any]:
    raise NotImplementedError
