"""Workflow loading and replay helpers for Temporal."""

from __future__ import annotations

import importlib
import inspect
import logging
from collections.abc import Iterator
from contextlib import contextmanager

from temporalio.client import WorkflowHistory
from temporalio.runtime import Runtime
from temporalio.worker import Replayer
from temporalio.workflow import _Definition

from .models import TemporalHistoryRecord


def load_workflow_definitions(module_name: str) -> tuple[list[type], list[str]]:
    module = importlib.import_module(module_name)
    workflows_by_name: dict[str, type] = {}
    for _, member in inspect.getmembers(module, inspect.isclass):
        if not hasattr(member, "__temporal_workflow_definition"):
            continue
        definition = _Definition.must_from_class(member)
        if definition.name is None:
            raise ValueError(f"Dynamic workflows are not supported in module {module_name}")
        workflows_by_name[definition.name] = member

    if not workflows_by_name:
        raise ValueError(f"No Temporal workflows found in module {module_name}")

    workflow_names = sorted(workflows_by_name)
    workflows = [workflows_by_name[name] for name in workflow_names]
    return workflows, workflow_names


async def replay_history(
    record: TemporalHistoryRecord,
    workflows: list[type],
    runtime: Runtime | None = None,
) -> Exception | None:
    if record.workflow_id is None or record.history_json is None:
        raise ValueError("History record is missing required workflow metadata")
    history = WorkflowHistory.from_json(record.workflow_id, record.history_json)
    replayer = Replayer(workflows=workflows, runtime=runtime)
    with suppress_temporal_workflow_logs():
        result = await replayer.replay_workflow(history, raise_on_replay_failure=False)
    return result.replay_failure


@contextmanager
def suppress_temporal_workflow_logs() -> Iterator[None]:
    logger = logging.getLogger("temporalio.worker._workflow")
    previous_disabled = logger.disabled
    logger.disabled = True
    try:
        yield
    finally:
        logger.disabled = previous_disabled
