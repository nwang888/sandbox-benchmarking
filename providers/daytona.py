"""Daytona sandbox provider."""

from __future__ import annotations

import asyncio
import importlib.metadata
import shlex
from collections.abc import AsyncIterator
from pathlib import Path
from uuid import uuid4

from providers.base import Sandbox, SandboxProvider

_DAYTONA_IMPORT_ERROR: Exception | None = None
try:
    from daytona import AsyncDaytona, DaytonaNotFoundError, SessionExecuteRequest
except Exception as error:  # pragma: no cover - handled at runtime.
    _DAYTONA_IMPORT_ERROR = error
    AsyncDaytona = None  # type: ignore[assignment]
    DaytonaNotFoundError = Exception  # type: ignore[assignment]
    SessionExecuteRequest = None  # type: ignore[assignment]


class DaytonaCommandError(RuntimeError):
    """Raised when Daytona command execution fails."""


class DaytonaSandbox(Sandbox):
    """Sandbox wrapper around a Daytona AsyncSandbox instance."""

    def __init__(self, client: AsyncDaytona, sandbox: object) -> None:
        self._client = client
        self._sandbox = sandbox
        self._destroyed = False

    async def exec(self, cmd: str) -> str:
        response = await self._sandbox.process.exec(cmd)
        if response.exit_code != 0:
            output = (response.result or "").strip()
            raise DaytonaCommandError(
                f"Daytona command failed with exit code {response.exit_code}: {output[:200]}"
            )
        return response.result

    async def stream_exec(self, cmd: str) -> AsyncIterator[str]:
        session_id = f"sandbox-bench-{uuid4().hex}"
        session_created = False
        stderr_chunks: list[str] = []
        queue: asyncio.Queue[str | None] = asyncio.Queue()

        try:
            await self._sandbox.process.create_session(session_id)
            session_created = True

            request = SessionExecuteRequest(command=cmd, run_async=True)
            response = await self._sandbox.process.execute_session_command(session_id, request)
            command_id = response.cmd_id

            async def on_stdout(chunk: str) -> None:
                await queue.put(chunk)

            async def on_stderr(chunk: str) -> None:
                stderr_chunks.append(chunk)

            async def stream_logs() -> None:
                try:
                    await self._sandbox.process.get_session_command_logs_async(
                        session_id,
                        command_id,
                        on_stdout,
                        on_stderr,
                    )
                finally:
                    await queue.put(None)

            logs_task = asyncio.create_task(stream_logs())
            try:
                while True:
                    chunk = await queue.get()
                    if chunk is None:
                        break
                    if chunk:
                        yield chunk
            finally:
                await logs_task

            exit_code = await self._wait_for_exit_code(session_id, command_id)
            if exit_code is not None and exit_code != 0:
                stderr_preview = "".join(stderr_chunks).strip()[:200]
                raise DaytonaCommandError(
                    f"Daytona streaming command failed with exit code {exit_code}: {stderr_preview}"
                )
        finally:
            if session_created:
                try:
                    await self._sandbox.process.delete_session(session_id)
                except Exception:
                    pass

    async def write_file(self, path: str, content: str) -> None:
        parent = Path(path).parent.as_posix() or "/"
        await self.exec(f"mkdir -p {shlex.quote(parent)}")
        await self._sandbox.fs.upload_file(content.encode("utf-8"), path)

    async def read_file(self, path: str) -> str:
        content = await self._sandbox.fs.download_file(path)
        if isinstance(content, str):
            return content
        return content.decode("utf-8")

    async def destroy(self) -> None:
        if self._destroyed:
            return
        self._destroyed = True

        delete_error: Exception | None = None
        try:
            await self._sandbox.delete()
        except DaytonaNotFoundError:
            pass
        except Exception as error:
            delete_error = error
        finally:
            await self._client.close()

        if delete_error is not None:
            raise delete_error

    async def _wait_for_exit_code(self, session_id: str, command_id: str) -> int | None:
        for _ in range(100):
            command = await self._sandbox.process.get_session_command(session_id, command_id)
            if command.exit_code is not None:
                return int(command.exit_code)
            await asyncio.sleep(0.1)
        return None


class DaytonaProvider(SandboxProvider):
    """SandboxProvider implementation backed by Daytona."""

    name = "daytona"

    def __init__(self) -> None:
        try:
            self.version = importlib.metadata.version("daytona")
        except importlib.metadata.PackageNotFoundError:
            self.version = "unknown"

    async def create(self) -> Sandbox:
        if _DAYTONA_IMPORT_ERROR is not None:
            raise RuntimeError(
                "Daytona SDK is not available. Install with `uv add daytona` "
                "or `pip install daytona`."
            ) from _DAYTONA_IMPORT_ERROR
        client = AsyncDaytona()
        try:
            sandbox = await client.create()
        except Exception:
            await client.close()
            raise
        return DaytonaSandbox(client=client, sandbox=sandbox)
