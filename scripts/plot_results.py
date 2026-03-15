"""Render a simple text plot from benchmark summary files."""

from __future__ import annotations

import json
from pathlib import Path


SUMMARY_DIR = Path("results/summaries")


def main() -> int:
    files = sorted(SUMMARY_DIR.glob("*.json"))
    if not files:
        print("No summary files found in results/summaries.")
        return 0

    rows: list[tuple[str, float]] = []
    for path in files:
        payload = json.loads(path.read_text(encoding="utf-8"))
        label = f"{payload['provider']}/{payload['benchmark']}"
        rows.append((label, float(payload["mean"])))

    max_latency = max(value for _, value in rows) or 1.0
    for label, value in sorted(rows, key=lambda item: item[1]):
        width = max(1, int((value / max_latency) * 40))
        print(f"{label:28} {'#' * width} {value:.6f}s")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
