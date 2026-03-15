"""Base provider interface for benchmark targets."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable


class Provider:
    """Minimal provider contract used by the benchmark scenarios."""

    name = "base"

    def __init__(self, config: dict | None = None) -> None:
        self.config = config or {}

    def setup(self) -> None:
        """Optional hook for provider-specific initialization."""

    def start(self) -> str:
        raise NotImplementedError(f"{self.name} does not implement start().")

    def exec(self, command: str) -> str:
        raise NotImplementedError(f"{self.name} does not implement exec().")

    def stream(self, command: str) -> Iterable[str]:
        raise NotImplementedError(f"{self.name} does not implement stream().")

    def write_file(self, path: str | Path, content: str) -> None:
        raise NotImplementedError(f"{self.name} does not implement write_file().")

    def read_file(self, path: str | Path) -> str:
        raise NotImplementedError(f"{self.name} does not implement read_file().")

    def destroy(self) -> None:
        raise NotImplementedError(f"{self.name} does not implement destroy().")
