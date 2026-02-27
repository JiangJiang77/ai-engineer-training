import pytest

from src.agent import run_agent


def test_sum_and_echo():
    logs = []
    sleeps = []

    def sum_tool(numbers):
        return {"status": "ok", "output": str(sum(numbers))}

    def echo(text):
        return {"status": "ok", "output": text}

    tools = {"sum": sum_tool, "echo": echo}
    out = run_agent(
        messages=[{"role": "user", "content": "hi"}],
        query="sum 2 3 then echo: done",
        tools=tools,
        max_retries=2,
        base_delay=0.1,
        sleep_fn=sleeps.append,
        logger=logs,
    )
    assert out["status"] == "ok"
    assert out["answer"] == "done"
    assert any(line.startswith("plan:") for line in logs)
    assert any("tool:sum" in line for line in logs)
    assert any("tool:echo" in line for line in logs)
    assert sleeps == []


def test_retry_flaky():
    logs = []
    sleeps = []
    calls = {"n": 0}

    def flaky():
        calls["n"] += 1
        if calls["n"] < 2:
            raise RuntimeError("boom")
        return {"status": "ok", "output": "ok"}

    tools = {"flaky": flaky}
    out = run_agent(
        messages=[{"role": "user", "content": "hi"}],
        query="flaky",
        tools=tools,
        max_retries=3,
        base_delay=0.1,
        sleep_fn=sleeps.append,
        logger=logs,
    )
    assert out["status"] == "ok"
    assert out["answer"] == "ok"
    assert sleeps == [0.1]
    assert any("status:error" in line for line in logs)
    assert any("status:ok" in line for line in logs)


def test_repeat_last_user():
    logs = []
    out = run_agent(
        messages=[
            {"role": "user", "content": "first"},
            {"role": "assistant", "content": "ack"},
            {"role": "user", "content": "second"},
        ],
        query="repeat last user",
        tools={},
        max_retries=1,
        base_delay=0.1,
        sleep_fn=lambda _: None,
        logger=logs,
    )
    assert out["status"] == "ok"
    assert out["answer"] == "second"
    assert any(line.startswith("plan:") for line in logs)
