"""Filesystem benchmark scaffold."""

from core.metrics import BenchmarkReport, MetricSample
from core.scenario import BenchmarkScenario
from core.timer import time_call


def build_scenario() -> BenchmarkScenario:
    def run(provider) -> BenchmarkReport:
        write_duration, _ = time_call(
            provider.write_file,
            "/tmp/benchmark.txt",
            "benchmark",
        )
        read_duration, content = time_call(provider.read_file, "/tmp/benchmark.txt")
        return BenchmarkReport(
            benchmark="filesystem",
            provider=provider.name,
            samples=[
                MetricSample(name="write_file", value=write_duration),
                MetricSample(
                    name="read_file",
                    value=read_duration,
                    metadata={"bytes": len(content)},
                ),
            ],
        )

    return BenchmarkScenario(
        name="filesystem",
        description="Measure simple file write and read latency.",
        run=run,
    )
