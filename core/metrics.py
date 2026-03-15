"""Data structures for raw benchmark output and summaries."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class MetricSample:
    name: str
    value: float
    unit: str = "seconds"
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class BenchmarkReport:
    benchmark: str
    provider: str
    samples: list[MetricSample]

    def as_dict(self) -> dict[str, Any]:
        return {
            "benchmark": self.benchmark,
            "provider": self.provider,
            "samples": [
                {
                    "name": sample.name,
                    "value": sample.value,
                    "unit": sample.unit,
                    "metadata": sample.metadata,
                }
                for sample in self.samples
            ],
        }
