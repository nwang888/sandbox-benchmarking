"""E2B provider placeholder."""

from __future__ import annotations

from providers.base import Sandbox, SandboxProvider


class E2BProvider(SandboxProvider):
    """Placeholder provider until E2B integration is implemented."""

    name = "e2b"
    version = "placeholder"

    async def create(self) -> Sandbox:
        raise NotImplementedError("E2B provider is a placeholder and is not implemented yet.")
