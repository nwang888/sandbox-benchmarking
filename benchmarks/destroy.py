"""Sandbox destroy latency benchmark."""

from __future__ import annotations

from typing import Any, TypedDict

from core.timer import elapsed, now
from providers.base import SandboxProvider


class BenchmarkResult(TypedDict):
    latency: float
    metadata: dict[str, Any]


class Benchmark:
    name = "destroy"

    async def run(self, provider: SandboxProvider) -> BenchmarkResult:
        sandbox = await provider.create()
        start = now()
        await sandbox.destroy()
        latency = elapsed(start)
        return {"latency": latency, "metadata": {}}
