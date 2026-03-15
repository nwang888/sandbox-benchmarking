"""Benchmark scenario definition."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from core.metrics import BenchmarkReport
from providers.base import Provider


@dataclass(slots=True)
class BenchmarkScenario:
    name: str
    description: str
    run: Callable[[Provider], BenchmarkReport]
