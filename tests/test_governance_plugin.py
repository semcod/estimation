from __future__ import annotations

import subprocess
from pathlib import Path
from types import SimpleNamespace

import wellmanifest_governance as plugin


def test_governance_gate_runs_with_recursion_guard(tmp_path: Path, monkeypatch) -> None:
    (tmp_path / "pyproject.toml").write_text(
        '[tool.wellmanifest]\ngate = "./project/governance-check.sh"\n',
        encoding="utf-8",
    )
    calls = []

    def fake_run(command, **kwargs):
        calls.append((command, kwargs))
        return subprocess.CompletedProcess(command, 0, "GOV-PASS", "")

    monkeypatch.delenv("WELLMANIFEST_GOVERNANCE_ACTIVE", raising=False)
    monkeypatch.setattr(plugin.subprocess, "run", fake_run)
    session = SimpleNamespace(config=SimpleNamespace(rootpath=tmp_path))

    plugin.pytest_sessionstart(session)

    assert calls[0][1]["cwd"] == tmp_path
    assert calls[0][1]["env"]["WELLMANIFEST_GOVERNANCE_ACTIVE"] == "1"


def test_governance_gate_skips_nested_invocation(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("WELLMANIFEST_GOVERNANCE_ACTIVE", "1")

    def unexpected_run(*args, **kwargs):
        raise AssertionError("nested gate must not execute")

    monkeypatch.setattr(plugin.subprocess, "run", unexpected_run)
    session = SimpleNamespace(config=SimpleNamespace(rootpath=tmp_path))
    plugin.pytest_sessionstart(session)
