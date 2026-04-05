"""Adapter lookup helpers."""

from __future__ import annotations

from replaygate.adapters.base import WorkflowAdapter
from replaygate.models import WorkflowEngine


def get_adapter(engine: WorkflowEngine) -> WorkflowAdapter:
    if engine is WorkflowEngine.TEMPORAL:
        from replaygate.adapters.temporal import TemporalAdapter

        return TemporalAdapter()
    raise ValueError(f"Unsupported workflow engine: {engine.value}")
