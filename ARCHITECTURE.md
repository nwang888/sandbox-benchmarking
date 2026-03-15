# ARCHITECTURE.md

This document is the source of truth for repository structure and implementation.

## Project: sandbox-bench

### Goal

Build a reproducible Python benchmark framework for comparing sandbox
providers used for code execution (E2B, Daytona, Docker, etc).

The framework measures raw API latency for sandbox operations
including: - sandbox creation - code execution - stdout streaming - file
operations - sandbox destruction

The system should be provider-agnostic so new sandbox backends can be
added easily.

------------------------------------------------------------------------

# Implementation Contract

The implementation must strictly follow the interfaces and patterns defined below.

Do not invent alternative abstractions unless necessary.

## Provider Interface Contract

All sandbox providers must implement the interface defined in:

providers/base.py

Two classes must exist:

SandboxProvider
Sandbox

SandboxProvider responsibilities:
- create sandbox instances

Sandbox responsibilities:
- execute commands
- stream stdout
- read/write files
- destroy sandbox

Benchmarks must interact only with the Sandbox abstraction.

Benchmarks must never directly reference provider SDKs.

---

## Benchmark Interface Contract

Every benchmark module must expose:

class BenchmarkResult(TypedDict):
    latency: float
    metadata: dict[str, Any]

class Benchmark:
    name: str

    async def run(self, provider: SandboxProvider) -> BenchmarkResult:
        ...

latency is the primary metric used in raw runs
metadata holds benchmark-specific values

The run() method must return a BenchmarkResult; latency is in seconds.

Benchmarks must not contain provider-specific logic.

---

## Provider Loading

The benchmark runner must load providers from providers/registry.py.
Do not dynamically import providers by filename in the runner.

Example CLI:

python runner/run_benchmark.py --provider docker

---

## Docker Implementation

Docker provider implementation:

Use the Docker CLI via subprocess.

Required commands:

docker run
docker exec
docker cp
docker rm -f

Do not require the docker Python SDK.

## Benchmark Discovery

Benchmarks should be discovered by importing modules inside the benchmarks directory.

The runner should execute the following benchmarks:

cold_start
exec
stream
filesystem
command_loop
destroy

---

## Result Storage Contract

Raw results must be written to:

results/raw/

Summary statistics must be written to:

results/summaries/

File naming format:

{provider}_{benchmark}.json

Example:

docker_exec.json
e2b_cold_start.json

---------------------------------------------------------------------

# High-Level Design

Architecture has three layers:

benchmarks → latency scenarios\
providers → sandbox provider adapters\
runner → benchmark orchestration + metrics

Benchmarks interact only with a standardized provider interface.

------------------------------------------------------------------------

# Repository Structure

sandbox-bench/

providers/ **init**.py base.py registry.py docker_local.py e2b.py daytona.py

benchmarks/ **init**.py cold_start.py exec.py stream.py filesystem.py
command_loop.py destroy.py

core/ timer.py metrics.py

runner/ run_benchmark.py

results/ raw/ summaries/

scripts/ summarize_results.py plot_results.py

README.md ARCHITECTURE.md pyproject.toml

------------------------------------------------------------------------

## Repository Structure Rules

The directories listed below must exist and contain the described modules.

Additional files already present in the repository may remain (for example:
pyproject.toml, ARCHITECTURE.md, scripts/, or other utility modules).

Do not remove existing files unless they conflict with the architecture.

Required directories:

providers/
benchmarks/
core/
runner/
results/

These directories must contain the modules described in this document.

------------------------------------------------------------------------

# Provider Interface

providers/base.py

Two main objects:

SandboxProvider\
Sandbox

### SandboxProvider

Responsible for creating sandbox instances.

class SandboxProvider: async def create(self) -\> "Sandbox": ...

### Sandbox

Represents a running sandbox instance.

from collections.abc import AsyncIterator

class Sandbox:
    async def exec(self, cmd: str) -> str:
        """Execute a command and return complete stdout."""

    async def stream_exec(self, cmd: str) -> AsyncIterator[str]:
        """Execute a command and yield stdout chunks as they arrive. Streaming latency is measured as:
        T1 = immediately before calling stream_exec(...)
        T2 = when the first stdout chunk is yielded
        time_to_first_output = T2 - T1"""

    async def write_file(self, path: str, content: str) -> None:
        """Write a file inside the sandbox."""

    async def read_file(self, path: str) -> str:
        """Read a file inside the sandbox."""

    async def destroy(self) -> None:
        """Destroy the sandbox."""


------------------------------------------------------------------------

# Benchmarks (MVP)

The MVP suite measures several latency dimensions relevant to sandbox
execution used by AI agents.

## Cold Start

Measures sandbox creation latency.

Steps: - create sandbox - record latency - destroy sandbox

File: benchmarks/cold_start.py

------------------------------------------------------------------------

## Exec Latency

Measures time to execute a simple command.

Command:

python -c "print(1)"

Steps: - create sandbox - execute command - destroy sandbox

File: benchmarks/exec.py

------------------------------------------------------------------------

## Streaming Latency

Measures time until the first stdout output appears.

Example command:

python -c "print('start'); import time; time.sleep(1); print('end')"

Metric:

time_to_first_output

File: benchmarks/stream.py

------------------------------------------------------------------------

## Filesystem Latency

Measures file roundtrip latency.

Steps: - write file inside sandbox - read file back

File: benchmarks/filesystem.py

------------------------------------------------------------------------

## Command Loop Latency

Simulates repeated command execution within a single sandbox session,
which mimics how AI agents iteratively run code.

Steps:

-   create sandbox
-   run a command repeatedly (e.g. 20 times)
-   measure total execution time
-   compute mean per-command latency
-   destroy sandbox

Example command:

python -c "print(1)"

Metrics:

-   total_loop_time
-   mean_command_latency
-   p95_command_latency

File:

benchmarks/command_loop.py

This benchmark helps reveal hidden per-command overhead such as:

-   API gateway latency
-   proxy layers
-   container exec overhead
-   shell spawning costs

------------------------------------------------------------------------

## Destroy Latency

Measures sandbox teardown time.

Steps:

-   create sandbox
-   destroy sandbox

File: benchmarks/destroy.py

------------------------------------------------------------------------

# Benchmark Runner

runner/run_benchmark.py

CLI behavior:

python runner/run_benchmark.py --provider docker --runs 30

This command runs all registered benchmarks for the selected provider.

Behavior:

1. Load the specified provider.
2. Discover all benchmarks in the benchmarks/ directory.
3. Execute each benchmark sequentially.
4. Run each benchmark N times.
5. Write raw results.
6. Compute summary statistics.

------------------------------------------------------------------------

# Timing Utility

core/timer.py

Use time.perf_counter for accurate latency measurement.

------------------------------------------------------------------------

# Metrics

core/metrics.py

Compute:

-   mean
-   median
-   p95
-   p99
-   stddev

------------------------------------------------------------------------

# Results

Raw results: results/raw/

File names:
Raw results: results/raw/{provider}_{benchmark}.json
Summary results: results/summaries/{provider}_{benchmark}.json

Example file:

{ "provider": "e2b", "benchmark": "exec", "runs": \[0.82, 0.91, 0.79\] }


Summary results: results/summaries/

------------------------------------------------------------------------

# Providers (Initial)

Docker (baseline) providers/docker_local.py

E2B providers/e2b.py

Daytona providers/daytona.py

------------------------------------------------------------------------

Providers must be registered in providers/registry.py.

The benchmark runner must load providers from this registry rather than dynamically importing modules.

------------------------------------------------------------------------

# Reproducibility Metadata

Each run should capture:

-   timestamp
-   python version
-   machine type
-   region
-   provider version
-   number of runs

------------------------------------------------------------------------

# Future Extensions

-   concurrent sandbox startup
-   warm sandbox reuse
-   dependency installation timing
-   snapshot / restore
-   agent loop latency beyond simple command loops
