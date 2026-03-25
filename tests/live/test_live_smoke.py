from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

import pytest

from core.config import ConfigurationError, validate_provider_secrets
from providers.registry import PROVIDER_REGISTRY
from runner import run_benchmark as runner_module


def _live_enabled() -> bool:
    return os.getenv("RUN_LIVE_BENCHMARK_TESTS") == "1"


def _live_providers() -> list[str]:
    raw = os.getenv("LIVE_PROVIDERS", "docker")
    providers = [name.strip() for name in raw.split(",") if name.strip()]
    return providers or ["docker"]


@pytest.mark.live
@pytest.mark.asyncio
@pytest.mark.parametrize("provider_name", _live_providers())
async def test_live_provider_smoke(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, provider_name: str) -> None:
    if not _live_enabled():
        pytest.skip("Set RUN_LIVE_BENCHMARK_TESTS=1 to run live provider checks.")

    if provider_name not in PROVIDER_REGISTRY:
        pytest.fail(f"Unknown live provider '{provider_name}'. Expected one of {sorted(PROVIDER_REGISTRY)}.")

    try:
        validate_provider_secrets(provider_name)
    except ConfigurationError as error:
        pytest.skip(f"Skipping {provider_name}: missing credentials ({error}).")

    monkeypatch.chdir(tmp_path)

    runs = int(os.getenv("LIVE_RUNS", "1"))
    warmup_trials = int(os.getenv("LIVE_WARMUP_TRIALS", "0"))
    timeout_seconds = float(os.getenv("LIVE_TIMEOUT_SECONDS", "120"))
    slo_latency_ms = float(os.getenv("LIVE_SLO_LATENCY_MS", "2000"))
    max_failure_rate = float(os.getenv("LIVE_MAX_FAILURE_RATE", "0.05"))
    max_timeout_rate = float(os.getenv("LIVE_MAX_TIMEOUT_RATE", "0.05"))

    args = argparse.Namespace(
        provider=provider_name,
        runs=runs,
        warmup_trials=warmup_trials,
        timeout_seconds=timeout_seconds,
        slo_latency_ms=slo_latency_ms,
        env_file=".env",
        no_env_file=False,
    )

    exit_code = await runner_module.main_async(args)
    assert exit_code == 0

    summary_dir = tmp_path / "results" / "summaries"
    assert summary_dir.exists()
    summary_files = sorted(summary_dir.glob(f"{provider_name}_*.json"))
    assert summary_files, f"No summary files were generated for provider {provider_name}."

    for summary_path in summary_files:
        payload = json.loads(summary_path.read_text(encoding="utf-8"))
        failure_rate = float(payload.get("failure_rate", 0.0))
        timeout_rate = float(payload.get("timeout_rate", 0.0))
        assert failure_rate <= max_failure_rate, (
            f"{provider_name}/{payload['benchmark']} failure_rate={failure_rate:.2%} "
            f"exceeds limit {max_failure_rate:.2%}"
        )
        assert timeout_rate <= max_timeout_rate, (
            f"{provider_name}/{payload['benchmark']} timeout_rate={timeout_rate:.2%} "
            f"exceeds limit {max_timeout_rate:.2%}"
        )
