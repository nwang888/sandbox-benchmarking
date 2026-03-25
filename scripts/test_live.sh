#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

if [ -f .env ]; then
  set -a
  # shellcheck source=/dev/null
  . ./.env
  set +a
fi

: "${RUN_LIVE_BENCHMARK_TESTS:=1}"
: "${LIVE_PROVIDERS:=docker}"
: "${LIVE_RUNS:=1}"
: "${LIVE_WARMUP_TRIALS:=0}"
: "${LIVE_TIMEOUT_SECONDS:=120}"
: "${LIVE_SLO_LATENCY_MS:=2000}"
: "${LIVE_MAX_FAILURE_RATE:=0.05}"
: "${LIVE_MAX_TIMEOUT_RATE:=0.05}"

export RUN_LIVE_BENCHMARK_TESTS
export LIVE_PROVIDERS
export LIVE_RUNS
export LIVE_WARMUP_TRIALS
export LIVE_TIMEOUT_SECONDS
export LIVE_SLO_LATENCY_MS
export LIVE_MAX_FAILURE_RATE
export LIVE_MAX_TIMEOUT_RATE

uv sync --group dev
uv run pytest -m live "$@"
