from __future__ import annotations

from typing import Dict, List, Optional


def choose_tool(query: str, tools: List[Dict[str, object]]) -> Optional[str]:
    raise NotImplementedError
