"""Repeated command execution benchmark for agent-like loops."""

from __future__ import annotations

from typing import Any, TypedDict

from core.metrics import percentile
from core.timer import elapsed, now
from providers.base import SandboxProvider


class BenchmarkResult(TypedDict):
    latency: float
    metadata: dict[str, Any]


class Benchmark:
    name = "command_loop"

    def __init__(self, iterations: int = 20) -> None:
        self.iterations = iterations

    async def run(self, provider: SandboxProvider) -> BenchmarkResult:
        sandbox = await provider.create()
        per_command_latencies: list[float] = []

        try:
            total_start = now()
            for _ in range(self.iterations):
                start = now()
                await sandbox.exec('python -c "print(1)"')
                per_command_latencies.append(elapsed(start))
            total_loop_time = elapsed(total_start)
        finally:
            await sandbox.destroy()

        mean_command_latency = total_loop_time / self.iterations
        p95_command_latency = percentile(per_command_latencies, 95.0)

        return {
            "latency": mean_command_latency,
            "metadata": {
                "iterations": self.iterations,
                "total_loop_time": total_loop_time,
                "mean_command_latency": mean_command_latency,
                "p95_command_latency": p95_command_latency,
            },
        }
