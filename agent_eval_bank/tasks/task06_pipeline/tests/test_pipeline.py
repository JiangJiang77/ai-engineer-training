from src.pipeline import run_pipeline


def test_pipeline_success():
    def t1(x):
        return {"status": "ok", "output": x + 1}

    def t2(x):
        return {"status": "ok", "output": x * 2}

    tools = {"inc": t1, "double": t2}
    steps = [
        {"tool": "inc", "args": {"x": 1}},
        {"tool": "double", "args": {"x": 2}},
    ]
    out = run_pipeline(steps, tools)
    assert out["status"] == "ok"
    assert out["results"] == [2, 4]
    assert len(out["logs"]) == 2


def test_pipeline_error():
    def t1(x):
        return {"status": "ok", "output": x}

    def t2():
        return {"status": "error", "error": "bad"}

    tools = {"echo": t1, "fail": t2}
    steps = [
        {"tool": "echo", "args": {"x": 1}},
        {"tool": "fail", "args": {}},
        {"tool": "echo", "args": {"x": 2}},
    ]
    out = run_pipeline(steps, tools)
    assert out["status"] == "error"
    assert out["results"] == [1]
    assert "bad" in out["logs"][-1]
