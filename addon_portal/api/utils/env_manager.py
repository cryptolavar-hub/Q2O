"""Helpers for reading and updating environment variables stored in .env files."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from dotenv import dotenv_values


def read_env_value(key: str, env_path: Path) -> Optional[str]:
    """Return the deserialized value for the specified environment key.

    Args:
        key: Environment key to look up.
        env_path: Path to the `.env` file.

    Returns:
        The deserialized value if present, otherwise :data:`None`.
    """

    if not env_path.exists():
        return None

    raw_value = dotenv_values(env_path).get(key)
    if raw_value is None:
        return None

    try:
        return json.loads(raw_value)
    except json.JSONDecodeError:
        return raw_value


def write_env_value(key: str, value: str, env_path: Path) -> None:
    """Persist the given value into the .env file using JSON string encoding.

    Args:
        key: Environment variable key.
        value: Value to persist.
        env_path: Path to the `.env` file.
    """

    serialized = json.dumps(value)
    lines = []
    replaced = False

    if env_path.exists():
        for line in env_path.read_text(encoding='utf-8').splitlines():
            if line.startswith(f"{key}="):
                lines.append(f"{key}={serialized}")
                replaced = True
            else:
                lines.append(line)

    if not replaced:
        lines.append(f"{key}={serialized}")

    env_path.write_text("\n".join(lines) + "\n", encoding='utf-8')
