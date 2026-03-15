"""Base interfaces for sandbox providers and sandbox instances."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator


class Sandbox(ABC):
    """Represents a running sandbox instance."""

    @abstractmethod
    async def exec(self, cmd: str) -> str:
        """Execute a command and return full stdout."""

    @abstractmethod
    async def stream_exec(self, cmd: str) -> AsyncIterator[str]:
        """Execute a command and yield stdout chunks as they are produced."""

    @abstractmethod
    async def write_file(self, path: str, content: str) -> None:
        """Write a file inside the sandbox."""

    @abstractmethod
    async def read_file(self, path: str) -> str:
        """Read a file from inside the sandbox."""

    @abstractmethod
    async def destroy(self) -> None:
        """Destroy the sandbox."""


class SandboxProvider(ABC):
    """Creates sandbox instances for benchmarks."""

    name = "base"
    version = "unknown"

    @abstractmethod
    async def create(self) -> Sandbox:
        """Create and return a new sandbox."""
