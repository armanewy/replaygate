"""Shared display helpers for report renderers."""

from __future__ import annotations

import json
from dataclasses import dataclass

from replaygate.models import (
    ArtifactManifest,
    FailureKind,
    PolicyDecisionValue,
    ReplayFailure,
    ReplayResult,
    VerificationReport,
    WorkflowTypeBreakdown,
)
from replaygate.risk import risk_rank


@dataclass(frozen=True)
class BreakdownItem:
    label: str
    count: int


@dataclass(frozen=True)
class ArtifactItem:
    label: str
    path: str


@dataclass(frozen=True)
class ResultView:
    path: str
    history_id: str
    workflow_type: str
    status: str
    compatibility: str
    risk_level: str
    duration: str
    failure_kind: str | None
    summary: str
    likely_cause: str | None
    remediation_hint: str | None
    raw_details: str | None


@dataclass(frozen=True)
class ReportView:
    tool_version: str
    generated_at: str
    project_name: str
    engine: str
    config_path: str
    git_sha: str | None
    verdict: str
    policy_decision: str
    policy_summary: str
    selection_strategy: str
    max_histories: int
    redact_payloads_in_reports: bool
    adapter_mode: str
    histories_checked: int
    passed: int
    failed: int
    skipped: int
    errored: int
    workflow_types: int
    failure_breakdown: tuple[BreakdownItem, ...]
    workflow_breakdown: tuple[WorkflowTypeBreakdown, ...]
    top_failures: tuple[ResultView, ...]
    results: tuple[ResultView, ...]
    artifacts: tuple[ArtifactItem, ...]
    violations: tuple[str, ...]


def build_report_view(report: VerificationReport, *, top_failures_limit: int = 5) -> ReportView:
    results = tuple(build_result_view(result) for result in report.results)
    top_failures = tuple(
        sorted(
            (result for result in results if result.failure_kind is not None),
            key=lambda item: (
                -risk_rank(item.risk_level),
                item.failure_kind or "",
                item.workflow_type,
                item.path,
            ),
        )[:top_failures_limit]
    )

    return ReportView(
        tool_version=report.tool_version,
        generated_at=report.generated_at.isoformat(),
        project_name=report.project.name,
        engine=report.project.engine.value,
        config_path=report.source.config_path,
        git_sha=report.source.git_sha,
        verdict=verdict_for_report(report),
        policy_decision=report.policy.decision.value,
        policy_summary=policy_summary_for_report(report),
        selection_strategy=report.settings.selection_strategy,
        max_histories=report.settings.max_histories,
        redact_payloads_in_reports=report.settings.redact_payloads_in_reports,
        adapter_mode=report.settings.adapter_mode,
        histories_checked=report.summary.total_histories,
        passed=report.summary.passed,
        failed=report.summary.failed,
        skipped=report.summary.skipped,
        errored=report.summary.errored,
        workflow_types=report.summary.workflow_types,
        failure_breakdown=tuple(build_failure_breakdown_items(report)),
        workflow_breakdown=tuple(report.workflow_breakdown),
        top_failures=top_failures,
        results=results,
        artifacts=tuple(build_artifact_items(report.artifacts)),
        violations=tuple(report.policy.violated_rules),
    )


def verdict_for_report(report: VerificationReport) -> str:
    if any(
        result.failure is not None and result.failure.kind is FailureKind.ENVIRONMENT_ERROR
        for result in report.results
    ):
        return "ERROR"
    if report.policy.decision is PolicyDecisionValue.PASS:
        return "PASSED"
    if report.summary.failed == 0 and report.summary.errored > 0:
        return "ERROR"
    return "FAILED"


def policy_summary_for_report(report: VerificationReport) -> str:
    if report.policy.decision is PolicyDecisionValue.PASS:
        return "This change passes replay safety policy."
    return "This change fails replay safety policy."


def build_failure_breakdown_items(report: VerificationReport) -> list[BreakdownItem]:
    items = [
        BreakdownItem(label=kind.value, count=count)
        for kind, count in report.failure_breakdown.items()
        if count > 0
    ]
    items.sort(
        key=lambda item: (
            -item.count,
            item.label,
        )
    )
    return items


def build_artifact_items(artifacts: ArtifactManifest) -> list[ArtifactItem]:
    items: list[ArtifactItem] = []
    if artifacts.json_report is not None:
        items.append(ArtifactItem(label="JSON", path=artifacts.json_report))
    if artifacts.markdown_report is not None:
        items.append(ArtifactItem(label="Markdown", path=artifacts.markdown_report))
    if artifacts.html_report is not None:
        items.append(ArtifactItem(label="HTML", path=artifacts.html_report))
    return items


def build_result_view(result: ReplayResult) -> ResultView:
    failure = result.failure
    return ResultView(
        path=result.artifact.path,
        history_id=result.artifact.workflow.workflow_id
        if result.artifact.workflow is not None
        else result.artifact.path,
        workflow_type=result.workflow_type
        or (
            result.artifact.workflow.workflow_type
            if (
                result.artifact.workflow is not None
                and result.artifact.workflow.workflow_type is not None
            )
            else "unknown-workflow"
        ),
        status=result.status.value,
        compatibility=result.compatibility_status.value,
        risk_level=result.risk_level.value,
        duration=format_duration(result.duration_ms),
        failure_kind=failure.kind.value if failure is not None else None,
        summary=failure.summary if failure is not None else "Replay passed.",
        likely_cause=failure.likely_cause if failure is not None else None,
        remediation_hint=failure.remediation_hint if failure is not None else None,
        raw_details=serialize_failure_details(failure),
    )


def serialize_failure_details(failure: ReplayFailure | None) -> str | None:
    if failure is None:
        return None
    payload: dict[str, object] = {
        "exception_type": failure.exception_type,
        "details": failure.details,
    }
    if failure.determinism_issue is not None:
        payload["determinism_issue"] = failure.determinism_issue.model_dump(
            mode="json",
            exclude_none=True,
        )
    return json.dumps(payload, indent=2, sort_keys=True)


def format_duration(duration_ms: float | None) -> str:
    if duration_ms is None:
        return "-"
    return f"{duration_ms:.1f} ms"
