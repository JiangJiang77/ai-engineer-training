from pathlib import Path

import pytest

from src.safe_paths import safe_join


def test_safe_join_inside(tmp_path: Path):
    base = tmp_path / "workspace"
    base.mkdir()
    out = safe_join(base, "data/file.txt")
    assert str(out).startswith(str(base))


def test_safe_join_traversal(tmp_path: Path):
    base = tmp_path / "workspace"
    base.mkdir()
    with pytest.raises(ValueError):
        safe_join(base, "../secrets.txt")
