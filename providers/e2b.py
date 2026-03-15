"""E2B sandbox provider."""

from __future__ import annotations

import asyncio
import importlib.metadata
import os
from collections.abc import AsyncIterator

from providers.base import Sandbox, SandboxProvider

_E2B_IMPORT_ERROR: Exception | None = None
try:
    from e2b import AsyncSandbox as E2BAsyncSandbox
    from e2b import CommandExitException
except Exception as error:  # pragma: no cover - handled at runtime.
    _E2B_IMPORT_ERROR = error
    E2BAsyncSandbox = None  # type: ignore[assignment]
    CommandExitException = Exception  # type: ignore[assignment]


class E2BCommandError(RuntimeError):
    """Raised when E2B command execution fails."""


class E2BSandbox(Sandbox):
    """Sandbox wrapper around E2B AsyncSandbox."""

    def __init__(self, sandbox: E2BAsyncSandbox) -> None:
        self._sandbox = sandbox
        self._destroyed = False

    async def exec(self, cmd: str) -> str:
        try:
            result = await self._sandbox.commands.run(cmd)
        except CommandExitException as error:
            preview = (error.stderr or error.stdout or "").strip()[:200]
            raise E2BCommandError(
                f"E2B command failed with exit code {error.exit_code}: {preview}"
            ) from error
        return result.stdout

    async def stream_exec(self, cmd: str) -> AsyncIterator[str]:
        queue: asyncio.Queue[str | None] = asyncio.Queue()
        stderr_chunks: list[str] = []
        run_error: Exception | None = None

        async def on_stdout(chunk: str) -> None:
            await queue.put(chunk)

        async def on_stderr(chunk: str) -> None:
            stderr_chunks.append(chunk)

        handle = await self._sandbox.commands.run(
            cmd,
            background=True,
            on_stdout=on_stdout,
            on_stderr=on_stderr,
        )

        async def wait_for_command() -> None:
            nonlocal run_error
            try:
                await handle.wait()
            except CommandExitException as error:
                stderr_preview = (error.stderr or "".join(stderr_chunks)).strip()[:200]
                run_error = E2BCommandError(
                    f"E2B streaming command failed with exit code {error.exit_code}: "
                    f"{stderr_preview}"
                )
            except Exception as error:
                run_error = error
            finally:
                await queue.put(None)

        wait_task = asyncio.create_task(wait_for_command())
        try:
            while True:
                chunk = await queue.get()
                if chunk is None:
                    break
                if chunk:
                    yield chunk
        finally:
            await wait_task

        if run_error is not None:
            raise run_error

    async def write_file(self, path: str, content: str) -> None:
        await self._sandbox.files.write(path, content)

    async def read_file(self, path: str) -> str:
        content = await self._sandbox.files.read(path, format="text")
        if isinstance(content, str):
            return content
        return bytes(content).decode("utf-8")

    async def destroy(self) -> None:
        if self._destroyed:
            return
        self._destroyed = True
        await self._sandbox.kill()


class E2BProvider(SandboxProvider):
    """SandboxProvider implementation backed by E2B."""

    name = "e2b"

    def __init__(self) -> None:
        try:
            self.version = importlib.metadata.version("e2b")
        except importlib.metadata.PackageNotFoundError:
            self.version = "unknown"

        self.template = os.getenv("SANDBOX_BENCH_E2B_TEMPLATE")
        timeout_value = os.getenv("SANDBOX_BENCH_E2B_TIMEOUT")
        self.timeout = int(timeout_value) if timeout_value else None

    async def create(self) -> Sandbox:
        if _E2B_IMPORT_ERROR is not None:
            raise RuntimeError(
                "E2B SDK is not available. Install with `uv add e2b` or `pip install e2b`."
            ) from _E2B_IMPORT_ERROR

        create_kwargs: dict[str, object] = {}
        if self.template:
            create_kwargs["template"] = self.template
        if self.timeout is not None:
            create_kwargs["timeout"] = self.timeout

        sandbox = await E2BAsyncSandbox.create(**create_kwargs)
        return E2BSandbox(sandbox)
