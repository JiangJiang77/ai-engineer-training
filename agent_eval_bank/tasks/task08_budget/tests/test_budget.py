from src.budget import trim_plan


def test_trim_plan():
    steps = [
        {"tool": "a", "estimate": 50},
        {"tool": "b", "estimate": 30},
        {"tool": "c", "estimate": 40},
    ]
    out = trim_plan(steps, max_tokens=90)
    assert out == [
        {"tool": "a", "estimate": 50},
        {"tool": "b", "estimate": 30},
    ]
