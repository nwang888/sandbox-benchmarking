from __future__ import annotations

import argparse
import asyncio
import json
from pathlib import Path
from typing import Any

import pytest

from runner import run_benchmark as runner_module


class FakeProvider:
    name = "fake"
    version = "fake-provider-1.0"


class StableBenchmark:
    def __init__(self, name: str, latency_s: float) -> None:
        self.name = name
        self.latency_s = latency_s
        self.calls = 0

    async def run(self, provider: Any) -> dict[str, Any]:
        _ = provider
        self.calls += 1
        return {
            "latency": self.latency_s,
            "metadata": {"call_number": self.calls},
        }


class FlakyBenchmark:
    name = "flaky"

    def __init__(self) -> None:
        self.calls = 0

    async def run(self, provider: Any) -> dict[str, Any]:
        _ = provider
        self.calls += 1
        if self.calls == 1:
            raise RuntimeError("synthetic failure")
        return {
            "latency": 0.01,
            "metadata": {"call_number": self.calls},
        }


class SlowBenchmark:
    name = "slow"

    async def run(self, provider: Any) -> dict[str, Any]:
        _ = provider
        await asyncio.sleep(0.1)
        return {"latency": 0.1, "metadata": {}}


@pytest.mark.asyncio
async def test_run_benchmark_records_timeouts() -> None:
    latencies, run_metadata, trials = await runner_module.run_benchmark(
        FakeProvider(),
        SlowBenchmark(),
        runs=1,
        warmup_trials=0,
        timeout_seconds=0.001,
    )

    assert latencies == []
    assert run_metadata == []
    assert len(trials) == 1
    assert trials[0]["success"] is False
    assert trials[0]["timeout"] is True
    assert isinstance(trials[0]["error"], str)
    assert "timeout" in trials[0]["error"].lower()


@pytest.mark.asyncio
async def test_run_benchmark_continues_after_failure() -> None:
    latencies, run_metadata, trials = await runner_module.run_benchmark(
        FakeProvider(),
        FlakyBenchmark(),
        runs=2,
        warmup_trials=0,
        timeout_seconds=10.0,
    )

    assert len(trials) == 2
    assert trials[0]["success"] is False
    assert trials[1]["success"] is True
    assert len(latencies) == 1
    assert len(run_metadata) == 1


@pytest.mark.asyncio
async def test_main_async_writes_contract_outputs(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    benchmarks = [
        StableBenchmark(name="bench_alpha", latency_s=0.01),
        StableBenchmark(name="bench_beta", latency_s=0.02),
    ]

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(runner_module, "discover_benchmarks", lambda: benchmarks)
    monkeypatch.setattr(runner_module, "create_provider", lambda _name: FakeProvider())
    monkeypatch.setattr(runner_module, "validate_provider_secrets", lambda _name: None)
    monkeypatch.setattr(runner_module, "load_env_file", lambda _path, strict=False: None)

    args = argparse.Namespace(
        provider="fake",
        runs=2,
        warmup_trials=1,
        timeout_seconds=5.0,
        slo_latency_ms=2000.0,
        env_file=".env",
        no_env_file=True,
    )

    exit_code = await runner_module.main_async(args)
    assert exit_code == 0

    run_dirs = list((tmp_path / "results" / "runs").iterdir())
    assert len(run_dirs) == 1
    run_dir = run_dirs[0]
    assert (run_dir / "metadata.json").exists()
    assert (run_dir / "results.jsonl").exists()

    run_metadata = json.loads((run_dir / "metadata.json").read_text(encoding="utf-8"))
    assert run_metadata["provider"] == "fake"
    assert run_metadata["provider_version"] == "fake-provider-1.0"
    assert run_metadata["number_of_runs"] == 2
    assert run_metadata["warmup_trials"] == 1

    lines = (run_dir / "results.jsonl").read_text(encoding="utf-8").splitlines()
    expected_rows = len(benchmarks) * (args.runs + args.warmup_trials)
    assert len(lines) == expected_rows
    first_row = json.loads(lines[0])
    assert {
        "provider",
        "benchmark",
        "trial_index",
        "run_index",
        "warmup",
        "timestamp",
        "success",
        "timeout",
        "error",
        "latency_s",
        "latency_ms",
        "metadata",
    }.issubset(first_row.keys())

    for benchmark in benchmarks:
        raw_path = tmp_path / "results" / "raw" / f"fake_{benchmark.name}.json"
        summary_path = tmp_path / "results" / "summaries" / f"fake_{benchmark.name}.json"

        assert raw_path.exists()
        assert summary_path.exists()

        raw_payload = json.loads(raw_path.read_text(encoding="utf-8"))
        summary_payload = json.loads(summary_path.read_text(encoding="utf-8"))

        assert len(raw_payload["trials"]) == args.runs + args.warmup_trials
        assert summary_payload["total_trials"] == args.runs
        assert summary_payload["successful_trials"] == args.runs
        assert summary_payload["failed_trials"] == 0
        assert summary_payload["failure_rate"] == 0.0
        assert "timeout_rate" in summary_payload
        assert "slo_violation_rate" in summary_payload
        assert "tail_ratio" in summary_payload
