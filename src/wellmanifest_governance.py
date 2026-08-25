"""Pytest bridge for the repository's adopted wellmanifest governance gate."""

from __future__ import annotations

import os
import subprocess
import tomllib
from pathlib import Path
from typing import Any

import pytest


_ACTIVE_ENV = "WELLMANIFEST_GOVERNANCE_ACTIVE"
_TIMEOUT_SECONDS = 120


def _gate_command(root: Path, configured_gate: str) -> list[str]:
    gate = (root / configured_gate).resolve()
    if os.name == "nt":
        if gate.suffix == ".sh":
            windows_gate = gate.with_suffix(".bat")
            if windows_gate.is_file():
                gate = windows_gate
        return ["cmd", "/c", str(gate)]
    if gate.suffix == ".sh":
        return ["bash", str(gate)]
    return [str(gate)]


def _configured_gate(root: Path) -> str | None:
    pyproject = root / "pyproject.toml"
    if not pyproject.is_file():
        return None
    with pyproject.open("rb") as handle:
        document = tomllib.load(handle)
    value: Any = document.get("tool", {}).get("wellmanifest", {}).get("gate")
    return str(value) if value else None


def pytest_sessionstart(session: pytest.Session) -> None:
    """Run the configured governance gate once before executing tests."""

    if os.environ.get(_ACTIVE_ENV) == "1":
        return
    root = Path(session.config.rootpath).resolve()
    configured_gate = _configured_gate(root)
    if not configured_gate:
        raise pytest.UsageError("tool.wellmanifest.gate is not configured")

    environment = os.environ.copy()
    environment[_ACTIVE_ENV] = "1"
    try:
        result = subprocess.run(
            _gate_command(root, configured_gate),
            cwd=root,
            env=environment,
            capture_output=True,
            text=True,
            timeout=_TIMEOUT_SECONDS,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        raise pytest.UsageError(f"wellmanifest governance gate unavailable: {error}") from error

    if result.returncode != 0:
        output = (result.stdout + result.stderr)[-4000:].strip()
        raise pytest.UsageError(
            f"wellmanifest governance gate failed with exit {result.returncode}:\n{output}"
        )
