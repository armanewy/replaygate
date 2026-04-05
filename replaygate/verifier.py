"""Verification orchestration."""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path

from replaygate import __version__
from replaygate.adapters.base import WorkflowAdapter
from replaygate.adapters.registry import get_adapter
from replaygate.config import ReplayGateConfig, load_config, resolve_from_config
from replaygate.models import (
    ArtifactManifest,
    CompatibilityStatus,
    FailureKind,
    PolicyDecision,
    ReplayCandidate,
    ReplayFailure,
    ReplayResult,
    ReplayRun,
    ReplayStatus,
    ReportProject,
    ReportSource,
    VerificationReport,
    VerificationSettings,
    VerificationSummary,
    WorkflowHistoryArtifact,
    WorkflowIdentifier,
    WorkflowTypeBreakdown,
)
from replaygate.policy import evaluate_policy
from replaygate.reporting.html_report import write_html_report
from replaygate.reporting.json_report import write_json_report
from replaygate.reporting.markdown_report import write_markdown_report
from replaygate.risk import risk_for_result
from replaygate.runtime_metadata import detect_git_sha


@dataclass
class VerificationExecution:
    report: VerificationReport
    exit_code: int
    written_outputs: dict[str, Path] = field(default_factory=dict)


def build_summary(results: list[ReplayResult]) -> VerificationSummary:
    workflow_types = {
        workflow_name_for_result(result)
        for result in results
        if workflow_name_for_result(result) != "unknown-workflow"
    }
    return VerificationSummary(
        total_histories=len(results),
        passed=sum(result.status is ReplayStatus.PASSED for result in results),
        failed=sum(result.status is ReplayStatus.FAILED for result in results),
        skipped=sum(result.status is ReplayStatus.SKIPPED for result in results),
        errored=sum(result.status is ReplayStatus.ERROR for result in results),
        workflow_types=len(workflow_types),
    )


def workflow_name_for_result(result: ReplayResult) -> str:
    if result.workflow_type is not None:
        return result.workflow_type
    if result.artifact.workflow is not None and result.artifact.workflow.workflow_type is not None:
        return result.artifact.workflow.workflow_type
    return "unknown-workflow"


def build_failure_breakdown(results: list[ReplayResult]) -> dict[FailureKind, int]:
    counts = Counter(result.failure.kind for result in results if result.failure is not None)
    return {kind: counts[kind] for kind in sorted(counts, key=lambda item: item.value)}


def risk_rank(level: str) -> int:
    return {"low": 0, "medium": 1, "high": 2, "critical": 3}[level]


def build_workflow_breakdown(results: list[ReplayResult]) -> list[WorkflowTypeBreakdown]:
    grouped: dict[str, list[ReplayResult]] = defaultdict(list)
    for result in results:
        grouped[workflow_name_for_result(result)].append(result)

    rows: list[WorkflowTypeBreakdown] = []
    for workflow_type in sorted(grouped):
        items = grouped[workflow_type]
        failure_counts = Counter(item.failure.kind for item in items if item.failure is not None)
        dominant_failure_kind = None
        notes = "all passed"
        if failure_counts:
            dominant_failure_kind = sorted(
                failure_counts,
                key=lambda kind: (-failure_counts[kind], kind.value),
            )[0]
            notes = f"{dominant_failure_kind.value} detected"

        highest_risk = max(items, key=lambda item: risk_rank(item.risk_level.value)).risk_level
        rows.append(
            WorkflowTypeBreakdown(
                workflow_type=workflow_type,
                checked=len(items),
                passed=sum(item.status is ReplayStatus.PASSED for item in items),
                failed=sum(item.status is ReplayStatus.FAILED for item in items),
                skipped=sum(item.status is ReplayStatus.SKIPPED for item in items),
                errored=sum(item.status is ReplayStatus.ERROR for item in items),
                dominant_failure_kind=dominant_failure_kind,
                risk_level=highest_risk,
                notes=notes,
            )
        )
    return rows


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


def output_paths_for_config(
    config: ReplayGateConfig,
    config_path: Path,
) -> dict[str, Path]:
    output_paths: dict[str, Path] = {}
    json_path = resolve_from_config(config_path, config.verification.outputs.json_path)
    if json_path is not None:
        output_paths["json"] = json_path
    markdown_path = resolve_from_config(config_path, config.verification.outputs.markdown_path)
    if markdown_path is not None:
        output_paths["markdown"] = markdown_path
    html_path = resolve_from_config(config_path, config.verification.outputs.html_path)
    if html_path is not None:
        output_paths["html"] = html_path
    return output_paths


def display_output_path(path: Path | None, base_dir: Path) -> str | None:
    if path is None:
        return None
    try:
        return path.relative_to(base_dir).as_posix()
    except ValueError:
        return path.as_posix()


def build_artifact_manifest(output_paths: dict[str, Path], base_dir: Path) -> ArtifactManifest:
    return ArtifactManifest.model_validate(
        {
            "json": display_output_path(output_paths.get("json"), base_dir),
            "markdown": display_output_path(output_paths.get("markdown"), base_dir),
            "html": display_output_path(output_paths.get("html"), base_dir),
        }
    )


def write_outputs(report: VerificationReport, output_paths: dict[str, Path]) -> dict[str, Path]:
    written: dict[str, Path] = {}
    json_path = output_paths.get("json")
    if json_path is not None:
        written["json"] = write_json_report(report, json_path)
    markdown_path = output_paths.get("markdown")
    if markdown_path is not None:
        written["markdown"] = write_markdown_report(report, markdown_path)
    html_path = output_paths.get("html")
    if html_path is not None:
        written["html"] = write_html_report(report, html_path)
    return written


def build_report(
    config: ReplayGateConfig,
    config_path: Path,
    run: ReplayRun,
    candidate: ReplayCandidate,
    results: list[ReplayResult],
    artifact_manifest: ArtifactManifest,
) -> VerificationReport:
    return VerificationReport(
        tool_version=__version__,
        generated_at=run.finished_at,
        project=ReportProject(
            name=config.project.name,
            engine=config.project.engine,
        ),
        source=ReportSource(
            config_path=config_path.as_posix(),
            git_sha=detect_git_sha(config_path.parent.resolve()),
        ),
        run=run,
        candidate=candidate,
        summary=build_summary(results),
        policy=evaluate_policy(config.policy, results),
        failure_breakdown=build_failure_breakdown(results),
        workflow_breakdown=build_workflow_breakdown(results),
        results=results,
        artifacts=artifact_manifest,
        settings=VerificationSettings(
            selection_strategy=config.verification.selection.strategy,
            max_histories=config.verification.selection.max_histories,
            redact_payloads_in_reports=config.privacy.redact_payloads_in_reports,
            adapter_mode=config.temporal.import_mode if config.temporal is not None else "unknown",
        ),
    )


def build_environment_error_report(
    config: ReplayGateConfig,
    config_path: Path,
    exc: Exception,
) -> VerificationExecution:
    output_paths = output_paths_for_config(config, config_path)
    artifact_manifest = build_artifact_manifest(output_paths, config_path.parent)
    failure_kind = FailureKind.ENVIRONMENT_ERROR
    result = ReplayResult(
        artifact=WorkflowHistoryArtifact(
            engine=config.project.engine,
            path=str(config_path),
            source_kind="config",
            checksum_sha256="",
            size_bytes=0,
            workflow=WorkflowIdentifier(workflow_id="verification-environment"),
        ),
        status=ReplayStatus.ERROR,
        compatibility_status=CompatibilityStatus.UNKNOWN,
        risk_level=risk_for_result(ReplayStatus.ERROR, failure_kind),
        failure=ReplayFailure(
            kind=failure_kind,
            summary="Verification could not initialize the adapter environment.",
            likely_cause=(
                "The candidate workflow module or history discovery step failed "
                "before replay execution began."
            ),
            remediation_hint=(
                "Fix the adapter configuration or candidate module import error "
                "and rerun verification."
            ),
            exception_type=type(exc).__name__,
            details={"message": str(exc)},
        ),
    )
    report = build_report(
        config=config,
        config_path=config_path,
        run=ReplayRun.now(),
        candidate=ReplayCandidate(
            engine=config.project.engine,
            source="unavailable",
            registered_workflow_types=[],
        ),
        results=[result],
        artifact_manifest=artifact_manifest,
    )
    written_outputs = write_outputs(report, output_paths)
    return VerificationExecution(
        report=report,
        exit_code=3,
        written_outputs=written_outputs,
    )


async def verify_config(
    config_path: Path,
    *,
    adapter: WorkflowAdapter | None = None,
) -> VerificationExecution:
    started_at = datetime.now(tz=UTC)
    config = load_config(config_path)
    output_paths = output_paths_for_config(config, config_path)
    artifact_manifest = build_artifact_manifest(output_paths, config_path.parent)
    resolved_adapter = adapter or get_adapter(config.project.engine)
    try:
        candidate: ReplayCandidate = resolved_adapter.load_candidate(config, config_path)
        artifacts = resolved_adapter.discover_histories(config, config_path)
    except Exception as exc:
        return build_environment_error_report(config, config_path, exc)
    selected = select_histories(config, artifacts)
    results: list[ReplayResult]

    if not selected:
        results = [build_missing_history_result(config)]
    else:
        results = []
        for artifact in selected:
            try:
                result = await resolved_adapter.replay_artifact(
                    artifact,
                    candidate,
                    config,
                    config_path,
                )
            except Exception as exc:
                result = build_adapter_error_result(artifact, exc)
            results.append(result)
        results.sort(key=lambda result: result.artifact.path)

    finished_at = datetime.now(tz=UTC)
    report = build_report(
        config=config,
        config_path=config_path,
        run=ReplayRun.from_times(
            started_at=started_at,
            finished_at=finished_at,
            config_path=str(config_path),
        ),
        candidate=candidate,
        results=results,
        artifact_manifest=artifact_manifest,
    )
    policy: PolicyDecision = report.policy
    written_outputs = write_outputs(report, output_paths)
    return VerificationExecution(
        report=report,
        exit_code=0 if policy.passed else 1,
        written_outputs=written_outputs,
    )
