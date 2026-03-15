"""Summary metric helpers for benchmark latency samples."""

from __future__ import annotations

import math
import statistics
from collections.abc import Sequence


def percentile(samples: Sequence[float], p: float) -> float:
    """Return percentile ``p`` (0-100) using linear interpolation."""
    if not samples:
        raise ValueError("percentile() requires at least one sample")
    if p < 0 or p > 100:
        raise ValueError("percentile must be between 0 and 100")

    ordered = sorted(samples)
    if len(ordered) == 1:
        return ordered[0]

    rank = (len(ordered) - 1) * (p / 100.0)
    lower_index = math.floor(rank)
    upper_index = math.ceil(rank)

    if lower_index == upper_index:
        return ordered[lower_index]

    lower_value = ordered[lower_index]
    upper_value = ordered[upper_index]
    weight = rank - lower_index
    return lower_value + (upper_value - lower_value) * weight


def summarize(samples: Sequence[float]) -> dict[str, float]:
    """Compute the core summary statistics for benchmark samples."""
    if not samples:
        raise ValueError("summarize() requires at least one sample")

    return {
        "mean": statistics.mean(samples),
        "median": statistics.median(samples),
        "p95": percentile(samples, 95.0),
        "p99": percentile(samples, 99.0),
        "stddev": statistics.stdev(samples) if len(samples) > 1 else 0.0,
    }
