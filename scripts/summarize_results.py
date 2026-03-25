"""Print benchmark summary statistics from summary JSON files."""

from __future__ import annotations

import json
from pathlib import Path


SUMMARY_DIR = Path("results/summaries")


def format_seconds(value: object) -> str:
    if isinstance(value, (float, int)):
        return f"{float(value):.6f}s"
    return "n/a"


def format_ratio(value: object) -> str:
    if isinstance(value, (float, int)):
        return f"{float(value):.2%}"
    return "n/a"


def format_scalar(value: object) -> str:
    if isinstance(value, (float, int)):
        return f"{float(value):.3f}"
    return "n/a"


def main() -> int:
    files = sorted(SUMMARY_DIR.glob("*.json"))
    if not files:
        print("No summary files found in results/summaries.")
        return 0

    for path in files:
        payload = json.loads(path.read_text(encoding="utf-8"))
        print(
            f"{payload['provider']}/{payload['benchmark']}: "
            f"mean={format_seconds(payload.get('mean'))} "
            f"p50={format_seconds(payload.get('p50', payload.get('median')))} "
            f"p95={format_seconds(payload.get('p95'))} "
            f"p99={format_seconds(payload.get('p99'))} "
            f"tail_ratio={format_scalar(payload.get('tail_ratio'))} "
            f"failure_rate={format_ratio(payload.get('failure_rate'))} "
            f"timeout_rate={format_ratio(payload.get('timeout_rate'))} "
            f"slo_violation_rate={format_ratio(payload.get('slo_violation_rate'))}"
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
