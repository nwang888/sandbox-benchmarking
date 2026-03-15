"""Print benchmark summary statistics from summary JSON files."""

from __future__ import annotations

import json
from pathlib import Path


SUMMARY_DIR = Path("results/summaries")


def main() -> int:
    files = sorted(SUMMARY_DIR.glob("*.json"))
    if not files:
        print("No summary files found in results/summaries.")
        return 0

    for path in files:
        payload = json.loads(path.read_text(encoding="utf-8"))
        print(
            f"{payload['provider']}/{payload['benchmark']}: "
            f"mean={payload['mean']:.6f}s "
            f"median={payload['median']:.6f}s "
            f"p95={payload['p95']:.6f}s "
            f"p99={payload['p99']:.6f}s "
            f"stddev={payload['stddev']:.6f}s"
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
