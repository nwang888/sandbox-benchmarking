"""Benchmark scenario definition."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from core.metrics import BenchmarkReport
from providers.base import BenchmarkProvider


@dataclass(slots=True)
class BenchmarkScenario:
    name: str
    description: str
    run: Callable[[BenchmarkProvider], BenchmarkReport]
