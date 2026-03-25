# sandbox-bench

Reproducible Python benchmark framework for sandbox providers used for code execution.

## Requirements

- Python 3.11
- Docker CLI available on `PATH` (for `docker` provider)
- Provider credentials via environment variables or `.env` file

## Implemented Providers

- `docker`: baseline implementation using Docker CLI (`docker run`, `docker exec`, `docker cp`, `docker rm -f`)
- `e2b`: AsyncSandbox-based implementation (`create`, `exec`, `stream_exec`, file read/write, `destroy`)
- `daytona`: AsyncDaytona-based implementation (`create`, `exec`, `stream_exec`, file read/write, `destroy`)

## Benchmarks

The runner executes the full suite:

- `cold_start`
- `exec`
- `stream`
- `filesystem`
- `command_loop`
- `destroy`

## Run Benchmarks

```bash
python3.11 runner/run_benchmark.py --provider docker --runs 30
```

If dependencies are managed with `uv`, run through the project environment:

```bash
uv run python runner/run_benchmark.py --provider docker --runs 30
```

Additional controls:

```bash
uv run python runner/run_benchmark.py \
  --provider docker \
  --runs 30 \
  --warmup-trials 5 \
  --timeout-seconds 120 \
  --slo-latency-ms 2000
```

The runner loads `.env` by default. You can override or disable this:

```bash
uv run python runner/run_benchmark.py --provider e2b --runs 5 --env-file .env
uv run python runner/run_benchmark.py --provider e2b --runs 5 --no-env-file
```

For Daytona:

```bash
export DAYTONA_API_KEY=...
# optional: DAYTONA_API_URL, DAYTONA_TARGET
uv run python runner/run_benchmark.py --provider daytona --runs 5
```

For E2B:

```bash
export E2B_API_KEY=...
# optional: SANDBOX_BENCH_E2B_TEMPLATE, SANDBOX_BENCH_E2B_TIMEOUT
uv run python runner/run_benchmark.py --provider e2b --runs 5
```

## Credential Handling

- Credentials are loaded once in the runner, then validated per provider before execution.
- Secret values are read through one central helper so this can be swapped to a secret manager later.
- `.env` should remain local-only and uncommitted.

Raw and summary output files are written as:

- `results/raw/{provider}_{benchmark}.json`
- `results/summaries/{provider}_{benchmark}.json`
- `results/runs/<timestamp>_<provider>/metadata.json`
- `results/runs/<timestamp>_<provider>/results.jsonl`

## Inspect Results

```bash
python3.11 scripts/summarize_results.py
python3.11 scripts/plot_results.py
```

## Automated Tests

Install dev test dependencies:

```bash
uv sync --group dev
```

Run deterministic contract tests (no live provider required):

```bash
uv run pytest -m "not live"
# or:
./scripts/test_unit.sh
```

Run live provider smoke tests (hits real services):

```bash
RUN_LIVE_BENCHMARK_TESTS=1 \
LIVE_PROVIDERS=docker \
LIVE_RUNS=1 \
LIVE_WARMUP_TRIALS=0 \
LIVE_TIMEOUT_SECONDS=120 \
LIVE_MAX_FAILURE_RATE=0.05 \
LIVE_MAX_TIMEOUT_RATE=0.05 \
uv run pytest -m live
# or:
./scripts/test_live.sh
```

Recommended local setup:

- Put provider credentials and optional live-test vars in `.env`.
- `scripts/test_live.sh` auto-loads `.env` if present.
- Keep live smoke tests small (`LIVE_RUNS=1`) and run them manually or on schedule.

CI defaults:

- `Unit Tests` workflow runs on every PR and on pushes to `main`.
- `Live Smoke Tests` workflow runs nightly and on manual dispatch.
- Live workflow reads provider credentials from repository secrets and optional thresholds from repository variables.

## Reproducibility Metadata

Each benchmark result captures:

- timestamp
- Python version
- machine type
- region (from env if available, otherwise `unknown`)
- provider version
- number of runs

Each JSONL trial record captures:

- trial index and warmup flag
- success/failure + error/timeout info
- latency (`latency_s`, `latency_ms`)
- benchmark-specific metadata for that trial

Summary files now include reliability metrics:

- `failure_rate`
- `timeout_rate`
- `slo_violation_rate`
- `tail_ratio`
