"""Benchmark scenario definition."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Awaitable, Callable

from providers.base import SandboxProvider


@dataclass(slots=True)
class BenchmarkScenario:
    name: str
    description: str
    run: Callable[[SandboxProvider], Awaitable[dict[str, Any]]]
