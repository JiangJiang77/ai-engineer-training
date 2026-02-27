from __future__ import annotations

import sys
from pathlib import Path


TASKS_DIR = Path(__file__).resolve().parent

for task_dir in TASKS_DIR.iterdir():
    src_dir = task_dir / "src"
    if src_dir.is_dir():
        sys.path.insert(0, str(src_dir))
