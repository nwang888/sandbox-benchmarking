"""Filesystem roundtrip latency benchmark."""

from __future__ import annotations

from typing import Any, TypedDict

from core.timer import elapsed, now
from providers.base import SandboxProvider


class BenchmarkResult(TypedDict):
    latency: float
    metadata: dict[str, Any]


class Benchmark:
    name = "filesystem"

    async def run(self, provider: SandboxProvider) -> BenchmarkResult:
        sandbox = await provider.create()
        path = "/tmp/benchmark_roundtrip.txt"
        payload = "benchmark-roundtrip-content"

        try:
            write_start = now()
            await sandbox.write_file(path, payload)
            write_latency = elapsed(write_start)

            read_start = now()
            content = await sandbox.read_file(path)
            read_latency = elapsed(read_start)
        finally:
            await sandbox.destroy()

        roundtrip_latency = write_latency + read_latency
        return {
            "latency": roundtrip_latency,
            "metadata": {
                "write_latency": write_latency,
                "read_latency": read_latency,
                "bytes": len(content),
                "content_matches": content == payload,
            },
        }
