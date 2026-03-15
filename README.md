# sandbox-bench

Reproducible Python benchmark framework for sandbox providers used for code execution.

## Requirements

- Python 3.11
- Docker CLI available on `PATH` (for `docker` provider)

## Implemented Providers

- `docker`: baseline implementation using Docker CLI (`docker run`, `docker exec`, `docker cp`, `docker rm -f`)
- `e2b`: placeholder stub
- `daytona`: placeholder stub

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
