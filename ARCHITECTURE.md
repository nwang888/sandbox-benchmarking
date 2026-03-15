# ARCHITECTURE.md

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

# High-Level Design

Architecture has three layers:

benchmarks → latency scenarios\
providers → sandbox provider adapters\
runner → benchmark orchestration + metrics

Benchmarks interact only with a standardized provider interface.

------------------------------------------------------------------------

# Repository Structure

sandbox-bench/

providers/ **init**.py base.py docker_local.py e2b.py daytona.py

benchmarks/ **init**.py cold_start.py exec.py stream.py filesystem.py
command_loop.py destroy.py

core/ timer.py metrics.py

runner/ run_benchmark.py

results/ raw/ summaries/

scripts/ summarize_results.py plot_results.py

requirements.txt README.md ARCHITECTURE.md

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

class Sandbox:

    async def exec(self, cmd: str) -> str:
        '''Execute command and return stdout'''

    async def stream_exec(self, cmd: str):
        '''Execute command and stream output'''

    async def write_file(self, path: str, content: str):
        '''Write file inside sandbox'''

    async def read_file(self, path: str) -> str:
        '''Read file from sandbox'''

    async def destroy(self):
        '''Destroy sandbox'''

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

Responsibilities:

-   load provider
-   load benchmark scenarios
-   run benchmarks N times
-   record raw results
-   compute summary metrics
-   print results to console

Example usage:

python runner/run_benchmark.py --provider e2b --runs 30

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

Example file:

{ "provider": "e2b", "benchmark": "exec", "runs": \[0.82, 0.91, 0.79\] }

Summary results: results/summaries/

------------------------------------------------------------------------

# Providers (Initial)

Docker (baseline) providers/docker_local.py

E2B providers/e2b.py

Daytona providers/daytona.py

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
