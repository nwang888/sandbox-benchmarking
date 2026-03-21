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
from core.metrics import summarize
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


async def run_benchmark(provider: Any, benchmark: Any, runs: int) -> tuple[list[float], list[dict[str, Any]]]:
    latencies: list[float] = []
    run_metadata: list[dict[str, Any]] = []

    for run_index in range(1, runs + 1):
        result = await benchmark.run(provider)
        latencies.append(float(result["latency"]))
        metadata = dict(result["metadata"])
        metadata["run_index"] = run_index
        metadata["timestamp"] = datetime.now(timezone.utc).isoformat()
        run_metadata.append(metadata)

    return latencies, run_metadata


async def main_async(args: argparse.Namespace) -> int:
    if args.runs < 1:
        raise ValueError("--runs must be >= 1")

    if not args.no_env_file:
        load_env_file(args.env_file, strict=args.env_file != ".env")
    validate_provider_secrets(args.provider)

    provider = create_provider(args.provider)
    benchmark_instances = discover_benchmarks()
    raw_dir, summary_dir = ensure_output_dirs()

    for benchmark in benchmark_instances:
        latencies, run_metadata = await run_benchmark(provider, benchmark, args.runs)
        summary = summarize(latencies)

        provider_version = str(getattr(provider, "version", "unknown"))
        common_metadata = build_common_metadata(provider.name, provider_version, args.runs)
        benchmark_name = benchmark.name

        raw_payload: dict[str, Any] = {
            **common_metadata,
            "benchmark": benchmark_name,
            "runs": latencies,
            "run_metadata": run_metadata,
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
        print(f"{provider.name}/{benchmark_name}: mean={summary['mean']:.6f}s")

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
