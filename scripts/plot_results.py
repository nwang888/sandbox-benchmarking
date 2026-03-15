"""Summarize raw benchmark JSON files."""

from __future__ import annotations

import json
from pathlib import Path


RAW_RESULTS_DIR = Path("results/raw")


def main() -> int:
    files = sorted(RAW_RESULTS_DIR.glob("*.json"))
    if not files:
        print("No raw results found in results/raw.")
        return 0

    for path in files:
        payload = json.loads(path.read_text())
        sample_names = ", ".join(sample["name"] for sample in payload.get("samples", []))
        print(f"{path.name}: {payload['provider']} / {payload['benchmark']} -> {sample_names}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
