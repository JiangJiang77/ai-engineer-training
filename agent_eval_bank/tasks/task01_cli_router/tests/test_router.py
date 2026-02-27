from pathlib import Path

import pytest

from src.router import route_tool


TOOLS_DIR = Path(__file__).resolve().parents[1] / "tools"


def test_echo_tool():
    out = route_tool("echo_tool", ["hello", "world"], TOOLS_DIR)
    assert out == "hello world"


def test_sum_tool():
    out = route_tool("sum_tool", ["2", "3", "5"], TOOLS_DIR)
    assert out == "10"


def test_unknown_tool():
    with pytest.raises(ValueError):
        route_tool("rm_rf", [], TOOLS_DIR)
