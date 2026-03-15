"""Streaming time-to-first-output benchmark."""

from __future__ import annotations

from typing import Any, TypedDict

from core.timer import elapsed, now
from providers.base import SandboxProvider


class BenchmarkResult(TypedDict):
    latency: float
    metadata: dict[str, Any]


class Benchmark:
    name = "stream"

    async def run(self, provider: SandboxProvider) -> BenchmarkResult:
        sandbox = await provider.create()
        try:
            command = 'python -c "print(\'start\'); import time; time.sleep(1); print(\'end\')"'
            t1 = now()
            stream = sandbox.stream_exec(command)
            first_output_latency: float | None = None
            chunk_count = 0
            chunks: list[str] = []

            async for chunk in stream:
                chunk_count += 1
                chunks.append(chunk)
                if first_output_latency is None:
                    first_output_latency = elapsed(t1)

            if first_output_latency is None:
                first_output_latency = elapsed(t1)
        finally:
            await sandbox.destroy()

        return {
            "latency": first_output_latency,
            "metadata": {
                "time_to_first_output": first_output_latency,
                "chunks": chunk_count,
                "output_preview": "".join(chunks).strip()[:120],
            },
        }
