from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from replaygate.cli import app


def test_init_writes_default_config(tmp_path: Path) -> None:
    runner = CliRunner()
    output = tmp_path / "replaygate.yaml"

    result = runner.invoke(app, ["init", "--output", str(output)])

    assert result.exit_code == 0
    assert output.exists()
    assert "engine: temporal" in output.read_text(encoding="utf-8")
