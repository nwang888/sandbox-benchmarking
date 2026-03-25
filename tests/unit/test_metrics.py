from __future__ import annotations

import pytest

from core.metrics import summarize_trials


def test_summarize_trials_excludes_warmups_and_computes_rates() -> None:
    trials = [
        {
            "warmup": True,
            "success": True,
            "timeout": False,
            "latency_s": 10.0,
        },
        {
            "warmup": False,
            "success": True,
            "timeout": False,
            "latency_s": 1.0,
        },
        {
            "warmup": False,
            "success": True,
            "timeout": False,
            "latency_s": 3.0,
        },
        {
            "warmup": False,
            "success": False,
            "timeout": True,
            "latency_s": None,
        },
    ]

    summary = summarize_trials(trials, slo_latency_ms=2000.0)

    assert summary["total_trials"] == 3
    assert summary["successful_trials"] == 2
    assert summary["failed_trials"] == 1
    assert summary["mean"] == pytest.approx(2.0)
    assert summary["median"] == pytest.approx(2.0)
    assert summary["p50"] == pytest.approx(2.0)
    assert summary["p95"] == pytest.approx(2.9)
    assert summary["p99"] == pytest.approx(2.98)
    assert summary["tail_ratio"] == pytest.approx(2.98 / 2.0)
    assert summary["failure_rate"] == pytest.approx(1.0 / 3.0)
    assert summary["timeout_rate"] == pytest.approx(1.0 / 3.0)
    assert summary["slo_violation_rate"] == pytest.approx(2.0 / 3.0)


def test_summarize_trials_handles_all_failed_trials() -> None:
    trials = [
        {
            "warmup": False,
            "success": False,
            "timeout": True,
            "latency_s": None,
        },
        {
            "warmup": False,
            "success": False,
            "timeout": False,
            "latency_s": None,
        },
    ]

    summary = summarize_trials(trials, slo_latency_ms=2000.0)

    assert summary["total_trials"] == 2
    assert summary["successful_trials"] == 0
    assert summary["failed_trials"] == 2
    assert summary["mean"] is None
    assert summary["median"] is None
    assert summary["p95"] is None
    assert summary["p99"] is None
    assert summary["stddev"] is None
    assert summary["p50"] is None
    assert summary["tail_ratio"] is None
    assert summary["failure_rate"] == 1.0
    assert summary["timeout_rate"] == 0.5
    assert summary["slo_violation_rate"] == 1.0
