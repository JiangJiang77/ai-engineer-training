import pytest

from src.state_machine import transition


def test_valid_transitions():
    assert transition("idle", "plan") == "planning"
    assert transition("planning", "execute") == "executing"
    assert transition("executing", "succeed") == "done"
    assert transition("planning", "error") == "failed"
    assert transition("failed", "reset") == "idle"


def test_invalid_transition():
    with pytest.raises(ValueError):
        transition("idle", "execute")
