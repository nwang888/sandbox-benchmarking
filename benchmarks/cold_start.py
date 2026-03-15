"""Cold start latency benchmark."""

from __future__ import annotations

from typing import Any, TypedDict

from core.timer import elapsed, now
from providers.base import SandboxProvider


class BenchmarkResult(TypedDict):
    latency: float
    metadata: dict[str, Any]


class Benchmark:
    name = "cold_start"

    async def run(self, provider: SandboxProvider) -> BenchmarkResult:
        start = now()
        sandbox = await provider.create()
        latency = elapsed(start)
        await sandbox.destroy()
        return {"latency": latency, "metadata": {}}
