"""CLI entry point for running sandbox benchmarks."""

from __future__ import annotations

import argparse
import asyncio
import importlib
import json
import os
import platform
import pkgutil
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# Support invocation as `python runner/run_benchmark.py`.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import benchmarks
from core.config import load_env_file, validate_provider_secrets
from core.metrics import summarize_trials
from providers.registry import PROVIDER_REGISTRY, create_provider

REQUIRED_BENCHMARKS = (
    "cold_start",
    "exec",
    "stream",
    "filesystem",
    "command_loop",
    "destroy",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run sandbox benchmarks.")
    parser.add_argument("--provider", required=True, choices=sorted(PROVIDER_REGISTRY))
    parser.add_argument("--runs", type=int, default=30)
    parser.add_argument(
        "--warmup-trials",
        type=int,
        default=0,
        help="Warmup runs per benchmark. Warmup trials are executed but excluded from summary metrics.",
    )
    parser.add_argument(
        "--timeout-seconds",
        type=float,
        default=120.0,
        help="Per-trial timeout in seconds. Set to 0 or a negative value to disable.",
    )
    parser.add_argument(
        "--slo-latency-ms",
        type=float,
        default=2000.0,
        help="Latency SLO threshold used to compute `slo_violation_rate`.",
    )
    parser.add_argument(
        "--env-file",
        default=".env",
        help="Path to dotenv file used for credentials (default: .env).",
    )
    parser.add_argument(
        "--no-env-file",
        action="store_true",
        help="Disable dotenv loading and rely only on existing process environment variables.",
    )
    return parser.parse_args()


def detect_region() -> str:
    for key in (
        "SANDBOX_BENCH_REGION",
        "AWS_REGION",
        "AWS_DEFAULT_REGION",
        "GCP_REGION",
        "AZURE_REGION",
    ):
        value = os.getenv(key)
        if value:
            return value
    return "unknown"


def discover_benchmarks() -> list[Any]:
    package_dir = Path(benchmarks.__file__).resolve().parent
    discovered: dict[str, Any] = {}

    for module_info in pkgutil.iter_modules([str(package_dir)]):
        if module_info.name.startswith("_"):
            continue
        module = importlib.import_module(f"benchmarks.{module_info.name}")
        benchmark_cls = getattr(module, "Benchmark", None)
        if benchmark_cls is None:
            continue
        benchmark = benchmark_cls()
        discovered[benchmark.name] = benchmark

    missing = [name for name in REQUIRED_BENCHMARKS if name not in discovered]
    if missing:
        raise RuntimeError(f"Missing required benchmark modules: {', '.join(missing)}")

    return [discovered[name] for name in REQUIRED_BENCHMARKS]


def ensure_output_dirs() -> tuple[Path, Path]:
    raw_dir = Path("results/raw")
    summary_dir = Path("results/summaries")
    raw_dir.mkdir(parents=True, exist_ok=True)
    summary_dir.mkdir(parents=True, exist_ok=True)
    return raw_dir, summary_dir


def create_run_directory(provider_name: str) -> Path:
    run_root = Path("results/runs")
    run_root.mkdir(parents=True, exist_ok=True)
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ")
    run_dir = run_root / f"{run_id}_{provider_name}"
    run_dir.mkdir(parents=True, exist_ok=False)
    return run_dir


def build_common_metadata(provider_name: str, provider_version: str, runs: int) -> dict[str, Any]:
    return {
        "provider": provider_name,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "python_version": platform.python_version(),
        "machine_type": platform.machine() or "unknown",
        "region": detect_region(),
        "provider_version": provider_version,
        "number_of_runs": runs,
    }


async def run_benchmark(
    provider: Any,
    benchmark: Any,
    runs: int,
    *,
    warmup_trials: int,
    timeout_seconds: float | None,
) -> tuple[list[float], list[dict[str, Any]], list[dict[str, Any]]]:
    latencies: list[float] = []
    run_metadata: list[dict[str, Any]] = []
    trial_records: list[dict[str, Any]] = []
    measured_run_index = 0

    total_trials = warmup_trials + runs
    for trial_index in range(1, total_trials + 1):
        is_warmup = trial_index <= warmup_trials
        run_index: int | None = None
        if not is_warmup:
            measured_run_index += 1
            run_index = measured_run_index

        trial_timestamp = datetime.now(timezone.utc).isoformat()
        success = False
        timed_out = False
        error_message: str | None = None
        latency_s: float | None = None
        benchmark_metadata: dict[str, Any] = {}

        try:
            if timeout_seconds is not None and timeout_seconds > 0:
                result = await asyncio.wait_for(benchmark.run(provider), timeout=timeout_seconds)
            else:
                result = await benchmark.run(provider)
            latency_s = float(result["latency"])
            benchmark_metadata = dict(result["metadata"])
            success = True
        except asyncio.TimeoutError:
            timed_out = True
            error_message = f"Trial exceeded timeout of {timeout_seconds:.3f}s"
        except Exception as error:
            error_message = f"{type(error).__name__}: {error}"

        trial_record: dict[str, Any] = {
            "provider": provider.name,
            "benchmark": benchmark.name,
            "trial_index": trial_index,
            "run_index": run_index,
            "warmup": is_warmup,
            "timestamp": trial_timestamp,
            "success": success,
            "timeout": timed_out,
            "error": error_message,
            "latency_s": latency_s,
            "latency_ms": latency_s * 1000.0 if latency_s is not None else None,
            "metadata": benchmark_metadata,
        }
        trial_records.append(trial_record)

        if success and not is_warmup and latency_s is not None:
            latencies.append(latency_s)
            metadata = dict(benchmark_metadata)
            metadata["run_index"] = run_index
            metadata["timestamp"] = trial_timestamp
            run_metadata.append(metadata)

    return latencies, run_metadata, trial_records


async def main_async(args: argparse.Namespace) -> int:
    if args.runs < 1:
        raise ValueError("--runs must be >= 1")
    if args.warmup_trials < 0:
        raise ValueError("--warmup-trials must be >= 0")

    if not args.no_env_file:
        load_env_file(args.env_file, strict=args.env_file != ".env")
    validate_provider_secrets(args.provider)

    provider = create_provider(args.provider)
    benchmark_instances = discover_benchmarks()
    raw_dir, summary_dir = ensure_output_dirs()
    run_dir = create_run_directory(args.provider)
    results_jsonl_path = run_dir / "results.jsonl"
    all_trial_records: list[dict[str, Any]] = []

    for benchmark in benchmark_instances:
        latencies, run_metadata, trial_records = await run_benchmark(
            provider,
            benchmark,
            args.runs,
            warmup_trials=args.warmup_trials,
            timeout_seconds=args.timeout_seconds,
        )
        summary = summarize_trials(
            trial_records,
            include_warmups=False,
            slo_latency_ms=args.slo_latency_ms,
        )
        all_trial_records.extend(trial_records)

        provider_version = str(getattr(provider, "version", "unknown"))
        common_metadata = build_common_metadata(provider.name, provider_version, args.runs)
        benchmark_name = benchmark.name

        raw_payload: dict[str, Any] = {
            **common_metadata,
            "benchmark": benchmark_name,
            "warmup_trials": args.warmup_trials,
            "timeout_seconds": args.timeout_seconds,
            "slo_latency_ms": args.slo_latency_ms,
            "runs": latencies,
            "run_metadata": run_metadata,
            "trials": trial_records,
        }
        summary_payload: dict[str, Any] = {
            **common_metadata,
            "benchmark": benchmark_name,
            **summary,
        }

        raw_path = raw_dir / f"{provider.name}_{benchmark_name}.json"
        summary_path = summary_dir / f"{provider.name}_{benchmark_name}.json"
        raw_path.write_text(json.dumps(raw_payload, indent=2) + "\n", encoding="utf-8")
        summary_path.write_text(json.dumps(summary_payload, indent=2) + "\n", encoding="utf-8")

        mean_value = summary["mean"]
        if isinstance(mean_value, (float, int)):
            mean_text = f"{mean_value:.6f}s"
        else:
            mean_text = "n/a"
        print(
            f"{provider.name}/{benchmark_name}: "
            f"mean={mean_text} "
            f"failure_rate={summary['failure_rate']:.2%} "
            f"slo_violation_rate={summary['slo_violation_rate']:.2%}"
        )

    with results_jsonl_path.open("w", encoding="utf-8") as handle:
        for trial in all_trial_records:
            handle.write(json.dumps(trial) + "\n")

    final_provider_version = str(getattr(provider, "version", "unknown"))
    run_metadata_payload: dict[str, Any] = {
        "provider": args.provider,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "python_version": platform.python_version(),
        "machine_type": platform.machine() or "unknown",
        "region": detect_region(),
        "provider_version": final_provider_version,
        "number_of_runs": args.runs,
        "warmup_trials": args.warmup_trials,
        "timeout_seconds": args.timeout_seconds,
        "slo_latency_ms": args.slo_latency_ms,
        "benchmarks": [benchmark.name for benchmark in benchmark_instances],
    }
    (run_dir / "metadata.json").write_text(
        json.dumps(run_metadata_payload, indent=2) + "\n",
        encoding="utf-8",
    )

    return 0


def main() -> int:
    args = parse_args()
    try:
        return asyncio.run(main_async(args))
    except Exception as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
