"""Runtime configuration and secret bootstrap helpers."""

from __future__ import annotations

import os
from pathlib import Path


class ConfigurationError(ValueError):
    """Raised when runtime configuration is invalid."""


def get_secret(name: str) -> str | None:
    """Read a secret value from the active runtime environment.

    This is the single read path for secrets in the benchmark runner.
    It intentionally uses environment variables today so it can be replaced
    later with a dedicated secret manager.
    """
    return os.getenv(name)


def load_env_file(path: str, strict: bool = False) -> None:
    """Load key/value pairs from a dotenv file into ``os.environ``.

    Existing environment values are preserved and are not overwritten.
    """
    env_path = Path(path)
    if not env_path.is_absolute():
        env_path = Path.cwd() / env_path

    if not env_path.exists():
        if strict:
            raise ConfigurationError(f"Environment file not found: {env_path}")
        return

    for line in env_path.read_text(encoding="utf-8").splitlines():
        raw = line.strip()
        if not raw or raw.startswith("#"):
            continue
        if raw.startswith("export "):
            raw = raw[len("export ") :].strip()
        if "=" not in raw:
            continue

        key, value = raw.split("=", 1)
        key = key.strip()
        value = value.strip()
        if not key:
            continue

        if (value.startswith('"') and value.endswith('"')) or (
            value.startswith("'") and value.endswith("'")
        ):
            value = value[1:-1]

        os.environ.setdefault(key, value)


def validate_provider_secrets(provider_name: str) -> None:
    """Ensure provider-specific credentials exist before benchmark execution."""
    if provider_name == "docker":
        return

    if provider_name == "e2b":
        if get_secret("E2B_API_KEY"):
            return
        raise ConfigurationError(
            "Missing E2B credentials. Set E2B_API_KEY in your shell, "
            "or provide it via --env-file."
        )

    if provider_name == "daytona":
        if get_secret("DAYTONA_API_KEY"):
            return

        jwt_token = get_secret("DAYTONA_JWT_TOKEN")
        org_id = get_secret("DAYTONA_ORGANIZATION_ID")
        if jwt_token and org_id:
            return

        raise ConfigurationError(
            "Missing Daytona credentials. Set DAYTONA_API_KEY, or set both "
            "DAYTONA_JWT_TOKEN and DAYTONA_ORGANIZATION_ID."
        )

    raise ConfigurationError(f"No credential validation rule for provider '{provider_name}'")
