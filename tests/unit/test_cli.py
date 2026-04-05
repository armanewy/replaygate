from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from replaygate.cli import app
from replaygate.runtime import ensure_supported_python


def test_init_writes_default_config(tmp_path: Path) -> None:
    runner = CliRunner()
    output = tmp_path / "replaygate.yaml"

    result = runner.invoke(app, ["init", "--output", str(output)])

    assert result.exit_code == 0
    assert output.exists()
    assert "engine: temporal" in output.read_text(encoding="utf-8")
    assert (tmp_path / "artifacts").exists()
    assert (tmp_path / "histories").exists()


def test_python_version_guard_rejects_314() -> None:
    try:
        ensure_supported_python((3, 14, 0))
    except SystemExit as exc:
        message = str(exc)
    else:  # pragma: no cover - defensive
        raise AssertionError("Expected unsupported Python version to raise SystemExit")

    assert "supports Python 3.11-3.13" in message
    assert "Detected 3.14" in message
