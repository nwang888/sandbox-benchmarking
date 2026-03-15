# sandbox-bench

Reproducible Python benchmark framework for sandbox providers used for code execution.

## Requirements

- Python 3.11
- Docker CLI available on `PATH` (for `docker` provider)
- Daytona API credentials (for `daytona` provider)

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

Raw and summary output files are written as:

- `results/raw/{provider}_{benchmark}.json`
- `results/summaries/{provider}_{benchmark}.json`

## Inspect Results

```bash
python3.11 scripts/summarize_results.py
python3.11 scripts/plot_results.py
```

## Reproducibility Metadata

Each benchmark result captures:

- timestamp
- Python version
- machine type
- region (from env if available, otherwise `unknown`)
- provider version
- number of runs
