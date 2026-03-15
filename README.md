# Sandbox Benchmarking

Scaffold for benchmarking sandbox providers such as local Docker, E2B, and Daytona.

## Layout

```text
providers/
benchmarks/
core/
runner/
results/
scripts/
```

## Run

```bash
python -m runner.run_benchmark docker_local cold_start
python scripts/plot_results.py
```

## Notes

- The provider modules are scaffolds. Each provider still needs concrete implementations for `start`, `exec`, `stream`, filesystem access, and `destroy`.
- Raw benchmark JSON is written to `results/raw/`.
- Summaries or charts can be written to `results/summaries/`.
