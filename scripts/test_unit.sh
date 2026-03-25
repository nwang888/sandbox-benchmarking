#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

uv sync --group dev
uv run pytest -m "not live" "$@"
