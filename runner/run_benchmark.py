"""CLI entry point for the benchmark scaffold."""

from __future__ import annotations

import argparse
import importlib
import json
from pathlib import Path


PROVIDERS = {
    "docker_local": ("providers.docker_local", "DockerLocalProvider"),
    "e2b": ("providers.e2b", "E2BProvider"),
    "daytona": ("providers.daytona", "DaytonaProvider"),
}

BENCHMARKS = {
    "cold_start": "benchmarks.cold_start",
    "exec": "benchmarks.exec",
    "stream": "benchmarks.stream",
    "filesystem": "benchmarks.filesystem",
    "destroy": "benchmarks.destroy",
}


def load_provider(name: str):
    module_name, class_name = PROVIDERS[name]
    module = importlib.import_module(module_name)
    return getattr(module, class_name)()


def load_scenario(name: str):
    module = importlib.import_module(BENCHMARKS[name])
    return module.build_scenario()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a benchmark scaffold.")
    parser.add_argument("provider", choices=sorted(PROVIDERS))
    parser.add_argument("benchmark", choices=sorted(BENCHMARKS))
    parser.add_argument(
        "--output",
        default="results/raw/latest.json",
        help="Path for the JSON benchmark report.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    provider = load_provider(args.provider)
    scenario = load_scenario(args.benchmark)
    provider.setup()
    report = scenario.run(provider)

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report.as_dict(), indent=2) + "\n")

    print(json.dumps(report.as_dict(), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
