"""Base adapter contracts."""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from replaygate.config import ReplayGateConfig
from replaygate.models import ReplayCandidate, ReplayResult, WorkflowEngine, WorkflowHistoryArtifact


class WorkflowAdapter(ABC):
    """Engine-specific discovery and replay contract."""

    engine: WorkflowEngine

    @abstractmethod
    def load_candidate(self, config: ReplayGateConfig, config_path: Path) -> ReplayCandidate:
        """Load the workflow candidate metadata."""

    @abstractmethod
    def discover_histories(
        self,
        config: ReplayGateConfig,
        config_path: Path,
    ) -> list[WorkflowHistoryArtifact]:
        """Discover replayable workflow history artifacts."""

    @abstractmethod
    async def replay_artifact(
        self,
        artifact: WorkflowHistoryArtifact,
        candidate: ReplayCandidate,
        config: ReplayGateConfig,
        config_path: Path,
    ) -> ReplayResult:
        """Replay a single history artifact against a candidate workflow package."""
