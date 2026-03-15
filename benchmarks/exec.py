"""Command execution benchmark scaffold."""

from core.metrics import BenchmarkReport, MetricSample
from core.scenario import BenchmarkScenario
from core.timer import time_call


def build_scenario() -> BenchmarkScenario:
    def run(provider) -> BenchmarkReport:
        duration, output = time_call(provider.exec, "echo benchmark")
        return BenchmarkReport(
            benchmark="exec",
            provider=provider.name,
            samples=[
                MetricSample(
                    name="exec",
                    value=duration,
                    metadata={"output_preview": str(output)[:80]},
                )
            ],
        )

    return BenchmarkScenario(
        name="exec",
        description="Measure single-command execution latency.",
        run=run,
    )
