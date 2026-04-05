"""Filesystem discovery for Temporal history artifacts."""

from __future__ import annotations

import hashlib
import json
from fnmatch import fnmatch
from pathlib import Path
from typing import Any

from replaygate.config import ReplayGateConfig, resolve_from_config
from replaygate.models import (
    FailureKind,
    WorkflowEngine,
    WorkflowHistoryArtifact,
    WorkflowIdentifier,
)

from .models import TemporalHistoryRecord


def discover_histories(
    config: ReplayGateConfig,
    config_path: Path,
) -> tuple[list[WorkflowHistoryArtifact], dict[str, TemporalHistoryRecord]]:
    discovered: list[WorkflowHistoryArtifact] = []
    records: dict[str, TemporalHistoryRecord] = {}

    for source in config.verification.history_sources:
        resolved_source = resolve_from_config(config_path, source.path)
        if resolved_source is None or not resolved_source.exists():
            continue

        if resolved_source.is_file():
            candidates = [resolved_source] if fnmatch(resolved_source.name, source.glob) else []
        else:
            candidates = sorted(
                path for path in resolved_source.glob(source.glob) if path.is_file()
            )

        for candidate in candidates:
            record = load_history_record(candidate, config_path.parent)
            records[record.key] = record
            discovered.append(build_artifact(record))

    discovered.sort(key=lambda artifact: artifact.path)
    return discovered, records


def load_history_record(path: Path, base_dir: Path) -> TemporalHistoryRecord:
    raw_bytes = path.read_bytes()
    checksum = hashlib.sha256(raw_bytes).hexdigest()
    key = to_record_key(path)
    display_path = to_display_path(path, base_dir)

    try:
        parsed = json.loads(raw_bytes.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        return TemporalHistoryRecord(
            key=key,
            display_path=display_path,
            resolved_path=path,
            checksum_sha256=checksum,
            size_bytes=len(raw_bytes),
            workflow_id=None,
            run_id=None,
            workflow_type=None,
            history_json=None,
            event_count=0,
            loader_error_kind=FailureKind.CORRUPTED_HISTORY,
            loader_error_message=str(exc),
        )

    workflow_id, run_id, workflow_type, history_json = unwrap_history_envelope(parsed)
    event_count = len(history_json.get("events", [])) if history_json is not None else 0

    loader_error_kind: FailureKind | None = None
    loader_error_message: str | None = None
    if history_json is None or workflow_id is None:
        loader_error_kind = FailureKind.CORRUPTED_HISTORY
        loader_error_message = (
            "Expected a Temporal history envelope with `workflow_id` and `history` keys."
        )

    record = TemporalHistoryRecord(
        key=key,
        display_path=display_path,
        resolved_path=path,
        checksum_sha256=checksum,
        size_bytes=len(raw_bytes),
        workflow_id=workflow_id,
        run_id=run_id,
        workflow_type=workflow_type,
        history_json=history_json,
        event_count=event_count,
        loader_error_kind=loader_error_kind,
        loader_error_message=loader_error_message,
    )
    return record


def build_artifact(record: TemporalHistoryRecord) -> WorkflowHistoryArtifact:
    workflow = None
    if record.workflow_id is not None:
        workflow = WorkflowIdentifier(
            workflow_id=record.workflow_id,
            workflow_type=record.workflow_type,
            run_id=record.run_id,
        )

    return WorkflowHistoryArtifact(
        engine=WorkflowEngine.TEMPORAL,
        path=record.display_path,
        source_kind="filesystem",
        checksum_sha256=record.checksum_sha256,
        size_bytes=record.size_bytes,
        workflow=workflow,
        metadata={
            "event_count": record.event_count,
            "record_key": record.key,
        },
    )


def unwrap_history_envelope(
    parsed: Any,
) -> tuple[str | None, str | None, str | None, dict[str, Any] | None]:
    if not isinstance(parsed, dict):
        return None, None, None, None

    if "history" in parsed:
        history_json = parsed.get("history")
        workflow_id = parsed.get("workflow_id")
        run_id = parsed.get("run_id")
        explicit_type = parsed.get("workflow_type")
        if not isinstance(history_json, dict) or not isinstance(workflow_id, str):
            return None, None, None, None
        workflow_type = (
            explicit_type if isinstance(explicit_type, str) else extract_workflow_type(history_json)
        )
        return workflow_id, run_id if isinstance(run_id, str) else None, workflow_type, history_json

    if "events" in parsed and isinstance(parsed.get("workflow_id"), str):
        workflow_type = extract_workflow_type(parsed)
        run_id = parsed.get("run_id")
        workflow_id = parsed["workflow_id"]
        return workflow_id, run_id if isinstance(run_id, str) else None, workflow_type, parsed

    return None, None, None, None


def extract_workflow_type(history_json: dict[str, Any]) -> str | None:
    events = history_json.get("events")
    if not isinstance(events, list):
        return None
    for event in events:
        if not isinstance(event, dict):
            continue
        attrs = event.get("workflowExecutionStartedEventAttributes") or event.get(
            "workflow_execution_started_event_attributes"
        )
        if not isinstance(attrs, dict):
            continue
        workflow_type = attrs.get("workflowType") or attrs.get("workflow_type")
        if isinstance(workflow_type, dict):
            name = workflow_type.get("name")
            if isinstance(name, str):
                return name
        if isinstance(workflow_type, str):
            return workflow_type
    return None


def to_display_path(path: Path, base_dir: Path) -> str:
    try:
        return path.relative_to(base_dir).as_posix()
    except ValueError:
        return path.resolve().as_posix()


def to_record_key(path: Path) -> str:
    return path.resolve().as_posix()
