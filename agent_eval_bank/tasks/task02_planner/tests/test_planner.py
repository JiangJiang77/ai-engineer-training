from src.planner import plan_steps


TOOLS = ["read_file", "summarize", "count_lines"]


def test_plan_read_then_summarize():
    goal = "Read notes.txt then summarize to 3 bullets."
    steps = plan_steps(goal, TOOLS)
    assert steps == [
        {"tool": "read_file", "args": {"path": "notes.txt"}},
        {"tool": "summarize", "args": {"bullets": 3}},
    ]


def test_plan_read_then_count():
    goal = "Read report.md then count lines."
    steps = plan_steps(goal, TOOLS)
    assert steps == [
        {"tool": "read_file", "args": {"path": "report.md"}},
        {"tool": "count_lines", "args": {}},
    ]
