"""Temporal adapter implementation."""

from __future__ import annotations

from pathlib import Path
from time import perf_counter

from temporalio.runtime import LoggingConfig, Runtime, TelemetryConfig, TelemetryFilter

from replaygate.adapters.base import WorkflowAdapter
from replaygate.config import ReplayGateConfig
from replaygate.models import (
    CompatibilityStatus,
    ReplayCandidate,
    ReplayResult,
    ReplayStatus,
    WorkflowEngine,
    WorkflowHistoryArtifact,
)
from replaygate.risk import compatibility_for_failure, risk_for_result

from .classifier import classify_loader_failure, classify_replay_failure
from .loader import discover_histories as discover_temporal_histories
from .models import TemporalHistoryRecord
from .replayer import load_workflow_definitions, replay_history


class TemporalAdapter(WorkflowAdapter):
    engine = WorkflowEngine.TEMPORAL

    def __init__(self) -> None:
        self._workflows: list[type] = []
        self._history_records: dict[str, TemporalHistoryRecord] = {}
        self._runtime = Runtime(
            telemetry=TelemetryConfig(
                logging=LoggingConfig(
                    filter=TelemetryFilter(core_level="ERROR", other_level="ERROR")
                )
            )
        )

    def load_candidate(self, config: ReplayGateConfig, config_path: Path) -> ReplayCandidate:
        if config.temporal is None:
            raise ValueError("Temporal configuration is required")
        workflows, workflow_names = load_workflow_definitions(config.temporal.workflows_module)
        self._workflows = workflows
        return ReplayCandidate(
            engine=self.engine,
            source=config.temporal.workflows_module,
            registered_workflow_types=workflow_names,
        )

    def discover_histories(
        self,
        config: ReplayGateConfig,
        config_path: Path,
    ) -> list[WorkflowHistoryArtifact]:
        artifacts, records = discover_temporal_histories(config, config_path)
        self._history_records = records
        return artifacts

    async def replay_artifact(
        self,
        artifact: WorkflowHistoryArtifact,
        candidate: ReplayCandidate,
        config: ReplayGateConfig,
        config_path: Path,
    ) -> ReplayResult:
        if not self._workflows:
            raise ValueError("Temporal candidate workflows have not been loaded")

        record = self._history_records.get(artifact.path)
        if record is None:
            raise FileNotFoundError(f"History artifact {artifact.path} was not discovered")

        started = perf_counter()
        if record.loader_error_kind is not None:
            failure = classify_loader_failure(
                record,
                redact_payloads=config.privacy.redact_payloads_in_reports,
            )
            status = ReplayStatus.ERROR
            compatibility = compatibility_for_failure(failure.kind)
        else:
            replay_failure = await replay_history(record, self._workflows, runtime=self._runtime)
            if replay_failure is None:
                duration_ms = round((perf_counter() - started) * 1000, 3)
                return ReplayResult(
                    artifact=artifact,
                    workflow_type=record.workflow_type,
                    status=ReplayStatus.PASSED,
                    compatibility_status=CompatibilityStatus.COMPATIBLE,
                    risk_level=risk_for_result(ReplayStatus.PASSED, None),
                    duration_ms=duration_ms,
                )

            failure = classify_replay_failure(
                replay_failure,
                redact_payloads=config.privacy.redact_payloads_in_reports,
            )
            status = ReplayStatus.FAILED
            compatibility = compatibility_for_failure(failure.kind)

        duration_ms = round((perf_counter() - started) * 1000, 3)
        workflow_type = record.workflow_type
        if workflow_type is None and artifact.workflow is not None:
            workflow_type = artifact.workflow.workflow_type
        return ReplayResult(
            artifact=artifact,
            workflow_type=workflow_type,
            status=status,
            compatibility_status=compatibility,
            risk_level=risk_for_result(status, failure.kind),
            duration_ms=duration_ms,
            failure=failure,
        )
