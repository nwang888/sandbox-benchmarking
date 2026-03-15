"""Teardown benchmark scaffold."""

from core.metrics import BenchmarkReport, MetricSample
from core.scenario import BenchmarkScenario
from core.timer import time_call


def build_scenario() -> BenchmarkScenario:
    def run(provider) -> BenchmarkReport:
        duration, _ = time_call(provider.destroy)
        return BenchmarkReport(
            benchmark="destroy",
            provider=provider.name,
            samples=[MetricSample(name="destroy", value=duration)],
        )

    return BenchmarkScenario(
        name="destroy",
        description="Measure teardown latency for the environment.",
        run=run,
    )
