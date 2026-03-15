"""Streaming output benchmark scaffold."""

from core.metrics import BenchmarkReport, MetricSample
from core.scenario import BenchmarkScenario
from core.timer import timer


def build_scenario() -> BenchmarkScenario:
    def run(provider) -> BenchmarkReport:
        with timer() as elapsed:
            chunks = list(provider.stream("echo benchmark"))
        return BenchmarkReport(
            benchmark="stream",
            provider=provider.name,
            samples=[
                MetricSample(
                    name="stream",
                    value=elapsed(),
                    metadata={"chunks": len(chunks)},
                )
            ],
        )

    return BenchmarkScenario(
        name="stream",
        description="Measure time to collect streamed command output.",
        run=run,
    )
