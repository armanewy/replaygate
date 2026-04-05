"""Internal Temporal adapter models."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from replaygate.models import FailureKind


@dataclass(slots=True)
class TemporalHistoryRecord:
    key: str
    resolved_path: Path
    checksum_sha256: str
    size_bytes: int
    workflow_id: str | None
    run_id: str | None
    workflow_type: str | None
    history_json: dict[str, Any] | None
    event_count: int
    loader_error_kind: FailureKind | None = None
    loader_error_message: str | None = None
