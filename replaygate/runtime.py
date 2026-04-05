"""Runtime guards for Replay Gate."""

from __future__ import annotations

import sys


def ensure_supported_python(
    version_info: tuple[int, int, int] | tuple[int, int] | None = None,
) -> None:
    """Fail fast with a clear message on unsupported interpreter versions."""
    major, minor = (version_info or sys.version_info)[:2]
    if (major, minor) < (3, 11) or (major, minor) >= (3, 14):
        raise SystemExit(
            "Replay Gate currently supports Python 3.11-3.13. "
            f"Detected {major}.{minor}. "
            "Create the virtual environment with `py -3.12 -m venv .venv` and reinstall."
        )
