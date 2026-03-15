"""Local Docker-backed benchmark provider scaffold."""

from providers.base import Provider


class DockerLocalProvider(Provider):
    name = "docker_local"
