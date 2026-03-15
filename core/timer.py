"""Timing utilities based on ``time.perf_counter``."""

from __future__ import annotations

from time import perf_counter


def now() -> float:
    """Return the current high-resolution timestamp."""
    return perf_counter()


def elapsed(start_time: float) -> float:
    """Return elapsed seconds since ``start_time``."""
    return perf_counter() - start_time
