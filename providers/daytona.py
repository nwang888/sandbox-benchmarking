"""Daytona provider placeholder."""

from __future__ import annotations

from providers.base import Sandbox, SandboxProvider


class DaytonaProvider(SandboxProvider):
    """Placeholder provider until Daytona integration is implemented."""

    name = "daytona"
    version = "placeholder"

    async def create(self) -> Sandbox:
        raise NotImplementedError(
            "Daytona provider is a placeholder and is not implemented yet."
        )
