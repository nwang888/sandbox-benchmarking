"""Provider registry used by the benchmark runner."""

from __future__ import annotations

from providers.base import SandboxProvider
from providers.daytona import DaytonaProvider
from providers.docker_local import DockerProvider
from providers.e2b import E2BProvider


PROVIDER_REGISTRY: dict[str, type[SandboxProvider]] = {
    "docker": DockerProvider,
    "e2b": E2BProvider,
    "daytona": DaytonaProvider,
}


def create_provider(name: str) -> SandboxProvider:
    try:
        provider_cls = PROVIDER_REGISTRY[name]
    except KeyError as error:
        choices = ", ".join(sorted(PROVIDER_REGISTRY))
        raise ValueError(f"Unknown provider '{name}'. Expected one of: {choices}") from error
    return provider_cls()
