"""Engine-agnostic domain models for Replay Gate."""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class WorkflowEngine(StrEnum):
    TEMPORAL = "temporal"


class ReplayStatus(StrEnum):
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    ERROR = "error"


class CompatibilityStatus(StrEnum):
    COMPATIBLE = "compatible"
    INCOMPATIBLE = "incompatible"
    UNKNOWN = "unknown"


class RiskLevel(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class FailureKind(StrEnum):
    NONDETERMINISM = "nondeterminism"
    UNKNOWN_WORKFLOW_TYPE = "unknown_workflow_type"
    MISSING_HISTORY = "missing_history"
    CORRUPTED_HISTORY = "corrupted_history"
    ADAPTER_ERROR = "adapter_error"
    PAYLOAD_DECODE_ERROR = "payload_decode_error"
    POLICY_FAILURE = "policy_failure"
    ENVIRONMENT_ERROR = "environment_error"


class WorkflowIdentifier(BaseModel):
    model_config = ConfigDict(extra="forbid")

    workflow_id: str
    workflow_type: str | None = None
    run_id: str | None = None


class WorkflowHistoryArtifact(BaseModel):
    model_config = ConfigDict(extra="forbid")

    engine: WorkflowEngine
    path: str
    source_kind: str
    checksum_sha256: str
    size_bytes: int
    workflow: WorkflowIdentifier | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class ReplayCandidate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    engine: WorkflowEngine
    source: str
    registered_workflow_types: list[str]
    metadata: dict[str, Any] = Field(default_factory=dict)


class DeterminismIssue(BaseModel):
    model_config = ConfigDict(extra="forbid")

    summary: str
    likely_cause: str
    remediation_hint: str
    details: dict[str, Any] = Field(default_factory=dict)


class ReplayFailure(BaseModel):
    model_config = ConfigDict(extra="forbid")

    kind: FailureKind
    summary: str
    likely_cause: str
    remediation_hint: str
    exception_type: str | None = None
    determinism_issue: DeterminismIssue | None = None
    details: dict[str, Any] = Field(default_factory=dict)


class ReplayResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    artifact: WorkflowHistoryArtifact
    status: ReplayStatus
    compatibility_status: CompatibilityStatus
    risk_level: RiskLevel
    workflow_type: str | None = None
    duration_ms: float | None = None
    failure: ReplayFailure | None = None


class PolicyDecision(BaseModel):
    model_config = ConfigDict(extra="forbid")

    passed: bool
    violated_rules: list[str] = Field(default_factory=list)
    observed_failures: int = 0
    observed_unknown: int = 0


class VerificationSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    total_histories: int
    passed: int
    failed: int
    skipped: int
    errors: int


class ReplayRun(BaseModel):
    model_config = ConfigDict(extra="forbid")

    started_at: datetime
    finished_at: datetime
    duration_ms: int
    config_path: str | None = None

    @classmethod
    def from_times(
        cls,
        started_at: datetime,
        finished_at: datetime,
        config_path: str | None = None,
    ) -> ReplayRun:
        duration_ms = int((finished_at - started_at).total_seconds() * 1000)
        return cls(
            started_at=started_at,
            finished_at=finished_at,
            duration_ms=duration_ms,
            config_path=config_path,
        )

    @classmethod
    def now(cls) -> ReplayRun:
        current = datetime.now(tz=UTC)
        return cls.from_times(current, current)


class VerificationReport(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: str = "1"
    project_name: str
    engine: WorkflowEngine
    run: ReplayRun
    candidate: ReplayCandidate
    summary: VerificationSummary
    policy: PolicyDecision
    results: list[ReplayResult]
