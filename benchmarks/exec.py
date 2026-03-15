"""Command execution latency benchmark."""

from __future__ import annotations

from typing import Any, TypedDict

from core.timer import elapsed, now
from providers.base import SandboxProvider


class BenchmarkResult(TypedDict):
    latency: float
    metadata: dict[str, Any]


class Benchmark:
    name = "exec"

    async def run(self, provider: SandboxProvider) -> BenchmarkResult:
        sandbox = await provider.create()
        try:
            start = now()
            output = await sandbox.exec('python -c "print(1)"')
            latency = elapsed(start)
        finally:
            await sandbox.destroy()

        return {
            "latency": latency,
            "metadata": {"output_preview": output.strip()[:80]},
        }
