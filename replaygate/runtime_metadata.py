"""Runtime metadata helpers."""

from __future__ import annotations

import subprocess
from pathlib import Path


def detect_git_sha(start_path: Path) -> str | None:
    try:
        result = subprocess.run(
            ["git", "-C", str(start_path), "rev-parse", "--short", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
        )
    except (FileNotFoundError, subprocess.CalledProcessError):
        return None
    value = result.stdout.strip()
    return value or None
