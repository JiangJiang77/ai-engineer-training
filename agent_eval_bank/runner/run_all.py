#!/usr/bin/env python3
"""
Run all tasks with pytest and print a concise summary.

Usage:
  python runner/run_all.py
  python runner/run_all.py --task task01_cli_router
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TASKS_DIR = ROOT / "tasks"


def _run_pytest(task_dir: Path) -> int:
    cmd = ["pytest", "-q", str(task_dir / "tests")]
    result = subprocess.run(cmd, cwd=ROOT)
    return result.returncode


def main() -> int:
    parser = argparse.ArgumentParser(description="Run all agent eval tasks.")
    parser.add_argument("--task", default=None, help="Run a single task by folder name")
    args = parser.parse_args()

    tasks = sorted([p for p in TASKS_DIR.iterdir() if p.is_dir()])
    if args.task:
        tasks = [p for p in tasks if p.name == args.task]
        if not tasks:
            print(f"Task not found: {args.task}")
            return 2

    failures = []
    for task_dir in tasks:
        code = _run_pytest(task_dir)
        if code != 0:
            failures.append(task_dir.name)

    if failures:
        print("Failed:", ", ".join(failures))
        return 1
    print("All tasks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
