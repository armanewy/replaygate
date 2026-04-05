"""Configuration models and YAML loading for Replay Gate."""

from __future__ import annotations

from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field

from replaygate.models import FailureKind, WorkflowEngine


class ProjectConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    engine: WorkflowEngine


class FilesystemHistorySourceConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: Literal["filesystem"]
    path: str
    glob: str = "*.json"


class SelectionConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    max_histories: int = Field(default=50, ge=1)
    strategy: Literal["all"] = "all"


class OutputConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    json_path: str | None = Field(default=None, alias="json")
    markdown_path: str | None = Field(default=None, alias="markdown")
    html_path: str | None = Field(default=None, alias="html")


class VerificationConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    workflow_types: list[str] = Field(default_factory=list)
    history_sources: list[FilesystemHistorySourceConfig]
    selection: SelectionConfig = Field(default_factory=SelectionConfig)
    outputs: OutputConfig = Field(default_factory=OutputConfig)


class PolicyConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    fail_on: list[FailureKind] = Field(default_factory=list)
    max_unknown: int = Field(default=0, ge=0)
    max_failures: int = Field(default=0, ge=0)


class PrivacyConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    redact_payloads_in_reports: bool = True


class TemporalConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    import_mode: Literal["local_module"] = "local_module"
    workflows_module: str
    payload_codec: Literal["none"] = "none"


class ReplayGateConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    project: ProjectConfig
    verification: VerificationConfig
    policy: PolicyConfig = Field(default_factory=PolicyConfig)
    privacy: PrivacyConfig = Field(default_factory=PrivacyConfig)
    temporal: TemporalConfig | None = None


def load_config(config_path: Path) -> ReplayGateConfig:
    raw = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    config = ReplayGateConfig.model_validate(raw)
    if config.project.engine is WorkflowEngine.TEMPORAL and config.temporal is None:
        raise ValueError("Temporal engine requires a `temporal` config section")
    return config


def resolve_from_config(config_path: Path, value: str | None) -> Path | None:
    if value is None:
        return None
    path = Path(value)
    if path.is_absolute():
        return path
    return config_path.parent / path


def default_config_template() -> str:
    return """project:
  name: replay-gate-demo
  engine: temporal

verification:
  workflow_types:
    - PaymentWorkflow
    - RefundWorkflow
  history_sources:
    - type: filesystem
      path: ./histories
      glob: "*.json"
  selection:
    max_histories: 50
    strategy: all
  outputs:
    json: ./artifacts/report.json
    markdown: ./artifacts/report.md
    html: ./artifacts/report.html

policy:
  fail_on:
    - nondeterminism
    - unknown_workflow_type
    - adapter_error
  max_unknown: 0
  max_failures: 0

privacy:
  redact_payloads_in_reports: true

temporal:
  import_mode: local_module
  workflows_module: examples.temporal.workflows
  payload_codec: none
"""
