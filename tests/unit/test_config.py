from __future__ import annotations

from pathlib import Path

from replaygate.config import ReplayGateConfig, default_config_template, load_config
from replaygate.models import WorkflowEngine


def test_default_config_template_parses(tmp_path: Path) -> None:
    config_path = tmp_path / "replaygate.yaml"
    config_path.write_text(default_config_template(), encoding="utf-8")

    loaded = load_config(config_path)

    assert isinstance(loaded, ReplayGateConfig)
    assert loaded.project.engine is WorkflowEngine.TEMPORAL
    assert loaded.temporal is not None
    assert loaded.verification.history_sources[0].glob == "*.json"
    assert loaded.verification.outputs.html_path == "./artifacts/report.html"


def test_relative_output_resolution(tmp_path: Path) -> None:
    from replaygate.config import resolve_from_config

    config_path = tmp_path / "configs" / "replaygate.yaml"
    config_path.parent.mkdir(parents=True)
    config_path.write_text(default_config_template(), encoding="utf-8")

    resolved = resolve_from_config(config_path, "./artifacts/report.json")

    assert resolved == config_path.parent / "artifacts" / "report.json"
