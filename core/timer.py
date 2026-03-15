"""Small timing helpers used across benchmarks."""

from __future__ import annotations

from contextlib import contextmanager
from time import perf_counter
from typing import Generator, TypeVar

T = TypeVar("T")


def time_call(func, *args, **kwargs) -> tuple[float, T]:
    start = perf_counter()
    result = func(*args, **kwargs)
    duration = perf_counter() - start
    return duration, result


@contextmanager
def timer() -> Generator[callable, None, None]:
    start = perf_counter()
    yield lambda: perf_counter() - start
