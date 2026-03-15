"""Docker-based sandbox provider using the Docker CLI via subprocess."""

from __future__ import annotations

import asyncio
import os
import shlex
import tempfile
from collections.abc import AsyncIterator
from pathlib import Path

from providers.base import Sandbox, SandboxProvider


class DockerCommandError(RuntimeError):
    """Raised when a Docker CLI command fails."""


async def _run_docker(*args: str) -> str:
    try:
        process = await asyncio.create_subprocess_exec(
            "docker",
            *args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
    except FileNotFoundError as error:
        raise DockerCommandError("docker CLI not found on PATH") from error
    stdout, stderr = await process.communicate()
    if process.returncode != 0:
        message = stderr.decode("utf-8", errors="replace").strip()
        raise DockerCommandError(f"docker {' '.join(args)} failed: {message}")
    return stdout.decode("utf-8", errors="replace")


async def _docker_cli_version() -> str:
    try:
        return (await _run_docker("--version")).strip()
    except Exception:
        return "unknown"


class DockerSandbox(Sandbox):
    """A running Docker container used as a sandbox."""

    def __init__(self, container_id: str) -> None:
        self.container_id = container_id
        self._destroyed = False

    async def exec(self, cmd: str) -> str:
        return await _run_docker("exec", self.container_id, "sh", "-lc", cmd)

    async def stream_exec(self, cmd: str) -> AsyncIterator[str]:
        process = await asyncio.create_subprocess_exec(
            "docker",
            "exec",
            self.container_id,
            "sh",
            "-lc",
            cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        assert process.stdout is not None
        assert process.stderr is not None

        while True:
            chunk = await process.stdout.readline()
            if not chunk:
                break
            yield chunk.decode("utf-8", errors="replace")

        stderr = (await process.stderr.read()).decode("utf-8", errors="replace").strip()
        return_code = await process.wait()
        if return_code != 0:
            raise DockerCommandError(
                f"docker exec failed for container {self.container_id}: {stderr}"
            )

    async def write_file(self, path: str, content: str) -> None:
        parent = Path(path).parent.as_posix() or "/"
        await self.exec(f"mkdir -p {shlex.quote(parent)}")

        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", delete=False) as handle:
            handle.write(content)
            temp_path = Path(handle.name)

        try:
            await _run_docker("cp", str(temp_path), f"{self.container_id}:{path}")
        finally:
            temp_path.unlink(missing_ok=True)

    async def read_file(self, path: str) -> str:
        with tempfile.NamedTemporaryFile(delete=False) as handle:
            temp_path = Path(handle.name)

        try:
            await _run_docker("cp", f"{self.container_id}:{path}", str(temp_path))
            return temp_path.read_text(encoding="utf-8")
        finally:
            temp_path.unlink(missing_ok=True)

    async def destroy(self) -> None:
        if self._destroyed:
            return
        self._destroyed = True
        try:
            await _run_docker("rm", "-f", self.container_id)
        except DockerCommandError:
            # The container may already be removed.
            pass


class DockerProvider(SandboxProvider):
    """SandboxProvider implementation backed by Docker."""

    name = "docker"

    def __init__(self, image: str | None = None) -> None:
        self.image = image or os.getenv("SANDBOX_BENCH_DOCKER_IMAGE", "python:3.11-slim")
        self.version = "unknown"

    async def create(self) -> Sandbox:
        if self.version == "unknown":
            self.version = await _docker_cli_version()

        output = await _run_docker(
            "run",
            "-d",
            self.image,
            "sh",
            "-lc",
            "while true; do sleep 3600; done",
        )
        container_id = output.strip()
        if not container_id:
            raise DockerCommandError("docker run did not return a container ID")
        return DockerSandbox(container_id=container_id)
