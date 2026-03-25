"""Summary metric helpers for benchmark latency samples."""

from __future__ import annotations

import math
import statistics
from collections.abc import Sequence
from typing import Any


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


def summarize_trials(
    trials: Sequence[dict[str, Any]],
    *,
    include_warmups: bool = False,
    slo_latency_ms: float | None = None,
) -> dict[str, Any]:
    """Compute latency + reliability metrics from trial records."""
    if include_warmups:
        measured = list(trials)
    else:
        measured = [trial for trial in trials if not bool(trial.get("warmup", False))]

    total_trials = len(measured)
    timeout_count = sum(1 for trial in measured if bool(trial.get("timeout", False)))
    successful_trials = [
        trial
        for trial in measured
        if bool(trial.get("success", False)) and isinstance(trial.get("latency_s"), (float, int))
    ]
    latencies = [float(trial["latency_s"]) for trial in successful_trials]
    failed_trials = total_trials - len(successful_trials)

    if latencies:
        latency_summary: dict[str, float | None] = summarize(latencies)
        p50 = latency_summary["median"]
        p99 = latency_summary["p99"]
    else:
        latency_summary = {
            "mean": None,
            "median": None,
            "p95": None,
            "p99": None,
            "stddev": None,
        }
        p50 = None
        p99 = None

    tail_ratio: float | None = None
    if p50 is not None and p99 is not None and p50 > 0:
        tail_ratio = p99 / p50

    if total_trials == 0:
        failure_rate = 0.0
        timeout_rate = 0.0
        slo_violation_rate = 0.0
    else:
        failure_rate = failed_trials / total_trials
        timeout_rate = timeout_count / total_trials
        if slo_latency_ms is None:
            slo_violation_rate = 0.0
        else:
            threshold_s = slo_latency_ms / 1000.0
            slo_violations = 0
            for trial in measured:
                if not bool(trial.get("success", False)):
                    slo_violations += 1
                    continue
                latency_s = trial.get("latency_s")
                if isinstance(latency_s, (float, int)) and float(latency_s) > threshold_s:
                    slo_violations += 1
            slo_violation_rate = slo_violations / total_trials

    return {
        **latency_summary,
        "p50": p50,
        "tail_ratio": tail_ratio,
        "failure_rate": failure_rate,
        "timeout_rate": timeout_rate,
        "slo_violation_rate": slo_violation_rate,
        "total_trials": total_trials,
        "successful_trials": len(successful_trials),
        "failed_trials": failed_trials,
        "slo_latency_ms": slo_latency_ms,
    }
