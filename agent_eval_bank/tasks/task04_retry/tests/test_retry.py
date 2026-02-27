import pytest

from src.retry import retry_call


def test_retry_success_after_failures():
    attempts = {"count": 0}
    sleeps = []

    def flaky():
        attempts["count"] += 1
        if attempts["count"] < 3:
            raise ValueError("fail")
        return "ok"

    def sleep_fn(delay):
        sleeps.append(delay)

    out = retry_call(flaky, max_attempts=4, base_delay=0.5, sleep_fn=sleep_fn)
    assert out == "ok"
    assert sleeps == [0.5, 1.0]


def test_retry_exhausted():
    def always_fail():
        raise RuntimeError("nope")

    def sleep_fn(_):
        pass

    with pytest.raises(RuntimeError):
        retry_call(always_fail, max_attempts=2, base_delay=1.0, sleep_fn=sleep_fn)
