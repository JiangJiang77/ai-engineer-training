from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from typing import Iterable


ALLOWLIST = {"echo_tool", "sum_tool"}


def route_tool(tool_name: str, args: Iterable[str], tools_dir: Path) -> str:
    """
    Execute a tool by name and return stdout as a string.
    """
    raise NotImplementedError
