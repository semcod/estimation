from __future__ import annotations

from pathlib import Path
import subprocess
import sys
import tomllib

import estimation


def test_runtime_and_cli_versions_match_package_metadata() -> None:
    metadata = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))
    expected = metadata["project"]["version"]

    assert estimation.__version__ == expected
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            "from estimation.cli import main; main(['--version'])",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    assert result.stdout.strip() == f"estimation {expected}"
