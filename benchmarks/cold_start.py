"""Cold-start benchmark scaffold."""

from core.metrics import BenchmarkReport, MetricSample
from core.scenario import BenchmarkScenario
from core.timer import time_call


def build_scenario() -> BenchmarkScenario:
    def run(provider) -> BenchmarkReport:
        duration, _ = time_call(provider.start)
        return BenchmarkReport(
            benchmark="cold_start",
            provider=provider.name,
            samples=[MetricSample(name="cold_start", value=duration)],
        )

    return BenchmarkScenario(
        name="cold_start",
        description="Measure time to start a fresh environment.",
        run=run,
    )
