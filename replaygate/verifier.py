"""Verification orchestration."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path

from replaygate.adapters.base import WorkflowAdapter
from replaygate.adapters.registry import get_adapter
from replaygate.config import ReplayGateConfig, load_config, resolve_from_config
from replaygate.models import (
    CompatibilityStatus,
    FailureKind,
    PolicyDecision,
    ReplayCandidate,
    ReplayFailure,
    ReplayResult,
    ReplayRun,
    ReplayStatus,
    RiskLevel,
    VerificationReport,
    VerificationSummary,
    WorkflowHistoryArtifact,
    WorkflowIdentifier,
)
from replaygate.policy import evaluate_policy
from replaygate.reporting.json_report import write_json_report
from replaygate.reporting.markdown_report import write_markdown_report


@dataclass
class VerificationExecution:
    report: VerificationReport
    exit_code: int
    written_outputs: dict[str, Path] = field(default_factory=dict)


def build_summary(results: list[ReplayResult]) -> VerificationSummary:
    return VerificationSummary(
        total_histories=len(results),
        passed=sum(result.status is ReplayStatus.PASSED for result in results),
        failed=sum(result.status is ReplayStatus.FAILED for result in results),
        skipped=sum(result.status is ReplayStatus.SKIPPED for result in results),
        errors=sum(result.status is ReplayStatus.ERROR for result in results),
    )


def select_histories(
    config: ReplayGateConfig,
    artifacts: list[WorkflowHistoryArtifact],
) -> list[WorkflowHistoryArtifact]:
    allowed = set(config.verification.workflow_types)
    selected = sorted(artifacts, key=lambda artifact: artifact.path)
    if allowed:
        selected = [
            artifact
            for artifact in selected
            if artifact.workflow is None
            or artifact.workflow.workflow_type is None
            or artifact.workflow.workflow_type in allowed
        ]
    return selected[: config.verification.selection.max_histories]


def risk_for_result(status: ReplayStatus, failure_kind: FailureKind | None) -> RiskLevel:
    if status is ReplayStatus.PASSED:
        return RiskLevel.LOW
    if failure_kind is FailureKind.NONDETERMINISM:
        return RiskLevel.CRITICAL
    if failure_kind in {
        FailureKind.UNKNOWN_WORKFLOW_TYPE,
        FailureKind.ADAPTER_ERROR,
        FailureKind.ENVIRONMENT_ERROR,
        FailureKind.PAYLOAD_DECODE_ERROR,
        FailureKind.MISSING_HISTORY,
    }:
        return RiskLevel.HIGH
    if failure_kind is FailureKind.CORRUPTED_HISTORY:
        return RiskLevel.MEDIUM
    return RiskLevel.HIGH


def build_missing_history_result(config: ReplayGateConfig) -> ReplayResult:
    source_paths = ",".join(source.path for source in config.verification.history_sources)
    failure_kind = FailureKind.MISSING_HISTORY
    return ReplayResult(
        artifact=WorkflowHistoryArtifact(
            engine=config.project.engine,
            path=source_paths or "(no history source configured)",
            source_kind="filesystem",
            checksum_sha256="",
            size_bytes=0,
            workflow=WorkflowIdentifier(workflow_id="missing-history"),
        ),
        workflow_type=None,
        status=ReplayStatus.ERROR,
        compatibility_status=CompatibilityStatus.UNKNOWN,
        risk_level=risk_for_result(ReplayStatus.ERROR, failure_kind),
        failure=ReplayFailure(
            kind=failure_kind,
            summary="No workflow history artifacts matched the configured sources.",
            likely_cause=(
                "The filesystem path or glob did not resolve to any replayable history files."
            ),
            remediation_hint=(
                "Check the configured history source path and glob, "
                "or add sanitized history fixtures before verifying."
            ),
        ),
    )


def build_adapter_error_result(
    artifact: WorkflowHistoryArtifact,
    exc: Exception,
) -> ReplayResult:
    failure_kind = FailureKind.ADAPTER_ERROR
    return ReplayResult(
        artifact=artifact,
        workflow_type=artifact.workflow.workflow_type if artifact.workflow is not None else None,
        status=ReplayStatus.ERROR,
        compatibility_status=CompatibilityStatus.UNKNOWN,
        risk_level=risk_for_result(ReplayStatus.ERROR, failure_kind),
        failure=ReplayFailure(
            kind=failure_kind,
            summary="Replay adapter raised an unexpected error.",
            likely_cause=(
                "The engine-specific adapter failed before it could "
                "produce a normalized replay result."
            ),
            remediation_hint=(
                "Inspect the adapter error details and fix the verification "
                "environment before relying on the result."
            ),
            exception_type=type(exc).__name__,
            details={"message": str(exc)},
        ),
    )


def write_outputs(
    report: VerificationReport,
    config: ReplayGateConfig,
    config_path: Path,
) -> dict[str, Path]:
    written: dict[str, Path] = {}
    json_path = resolve_from_config(config_path, config.verification.outputs.json_path)
    if json_path is not None:
        written["json"] = write_json_report(report, json_path)
    markdown_path = resolve_from_config(config_path, config.verification.outputs.markdown_path)
    if markdown_path is not None:
        written["markdown"] = write_markdown_report(report, markdown_path)
    return written


async def verify_config(
    config_path: Path,
    *,
    adapter: WorkflowAdapter | None = None,
) -> VerificationExecution:
    started_at = datetime.now(tz=UTC)
    config = load_config(config_path)
    resolved_adapter = adapter or get_adapter(config.project.engine)
    candidate: ReplayCandidate = resolved_adapter.load_candidate(config)
    artifacts = resolved_adapter.discover_histories(config)
    selected = select_histories(config, artifacts)

    if not selected:
        results = [build_missing_history_result(config)]
    else:
        results: list[ReplayResult] = []
        for artifact in selected:
            try:
                result = await resolved_adapter.replay_artifact(artifact, candidate, config)
            except Exception as exc:
                result = build_adapter_error_result(artifact, exc)
            results.append(result)
        results.sort(key=lambda result: result.artifact.path)

    finished_at = datetime.now(tz=UTC)
    summary = build_summary(results)
    policy: PolicyDecision = evaluate_policy(config.policy, results)
    report = VerificationReport(
        project_name=config.project.name,
        engine=config.project.engine,
        run=ReplayRun.from_times(
            started_at=started_at,
            finished_at=finished_at,
            config_path=str(config_path),
        ),
        candidate=candidate,
        summary=summary,
        policy=policy,
        results=results,
    )
    written_outputs = write_outputs(report, config, config_path)
    return VerificationExecution(
        report=report,
        exit_code=0 if policy.passed else 1,
        written_outputs=written_outputs,
    )
