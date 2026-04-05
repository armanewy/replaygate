"""Temporal adapter placeholder implementation."""

from __future__ import annotations

from replaygate.adapters.base import WorkflowAdapter
from replaygate.config import ReplayGateConfig
from replaygate.models import ReplayCandidate, ReplayResult, WorkflowEngine, WorkflowHistoryArtifact


class TemporalAdapter(WorkflowAdapter):
    engine = WorkflowEngine.TEMPORAL

    def load_candidate(self, config: ReplayGateConfig) -> ReplayCandidate:
        if config.temporal is None:
            raise ValueError("Temporal configuration is required")
        return ReplayCandidate(
            engine=self.engine,
            source=config.temporal.workflows_module,
            registered_workflow_types=[],
        )

    def discover_histories(self, config: ReplayGateConfig) -> list[WorkflowHistoryArtifact]:
        raise NotImplementedError("Temporal history discovery arrives in milestone 3")

    async def replay_artifact(
        self,
        artifact: WorkflowHistoryArtifact,
        candidate: ReplayCandidate,
        config: ReplayGateConfig,
    ) -> ReplayResult:
        raise NotImplementedError("Temporal replay arrives in milestone 3")
