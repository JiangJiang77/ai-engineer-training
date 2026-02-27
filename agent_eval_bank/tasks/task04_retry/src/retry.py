from __future__ import annotations

from typing import Callable, TypeVar


T = TypeVar("T")


def retry_call(
    func: Callable[[], T],
    max_attempts: int,
    base_delay: float,
    sleep_fn: Callable[[float], None],
) -> T:
    raise NotImplementedError
