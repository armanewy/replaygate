from __future__ import annotations

from datetime import UTC, datetime

from replaygate.models import (
    ArtifactManifest,
    CompatibilityStatus,
    FailureKind,
    PolicyDecision,
    PolicyDecisionValue,
    ReplayCandidate,
    ReplayFailure,
    ReplayResult,
    ReplayRun,
    ReplayStatus,
    ReportProject,
    ReportSource,
    RiskLevel,
    VerificationReport,
    VerificationSettings,
    VerificationSummary,
    WorkflowEngine,
    WorkflowHistoryArtifact,
    WorkflowIdentifier,
    WorkflowTypeBreakdown,
)


def sample_report() -> VerificationReport:
    return VerificationReport(
        tool_version="0.1.0",
        generated_at=datetime(2026, 1, 1, 12, 0, 0, tzinfo=UTC),
        project=ReportProject(
            name="payments-workflows",
            engine=WorkflowEngine.TEMPORAL,
        ),
        source=ReportSource(
            config_path="examples/temporal/replaygate.yaml",
            git_sha="abc123",
        ),
        run=ReplayRun.from_times(
            datetime(2026, 1, 1, tzinfo=UTC),
            datetime(2026, 1, 1, tzinfo=UTC),
            config_path="examples/temporal/replaygate.yaml",
        ),
        candidate=ReplayCandidate(
            engine=WorkflowEngine.TEMPORAL,
            source="examples.temporal.workflows",
            registered_workflow_types=["PaymentWorkflow"],
        ),
        summary=VerificationSummary(
            total_histories=1,
            passed=0,
            failed=1,
            skipped=0,
            errored=0,
            workflow_types=1,
        ),
        policy=PolicyDecision(
            passed=False,
            decision=PolicyDecisionValue.FAIL,
            violated_rules=["max_failures=0 -> violated (1 observed)"],
            observed_failures=1,
            observed_unknown=0,
        ),
        failure_breakdown={FailureKind.NONDETERMINISM: 1},
        workflow_breakdown=[
            WorkflowTypeBreakdown(
                workflow_type="PaymentWorkflow",
                checked=1,
                passed=0,
                failed=1,
                skipped=0,
                errored=0,
                dominant_failure_kind=FailureKind.NONDETERMINISM,
                risk_level=RiskLevel.CRITICAL,
                notes="nondeterminism detected",
            )
        ],
        results=[
            ReplayResult(
                artifact=WorkflowHistoryArtifact(
                    engine=WorkflowEngine.TEMPORAL,
                    path="histories/payment.json",
                    source_kind="filesystem",
                    checksum_sha256="abc",
                    size_bytes=42,
                    workflow=WorkflowIdentifier(
                        workflow_id="payment-1",
                        workflow_type="PaymentWorkflow",
                        run_id="run-1",
                    ),
                ),
                workflow_type="PaymentWorkflow",
                status=ReplayStatus.FAILED,
                compatibility_status=CompatibilityStatus.INCOMPATIBLE,
                risk_level=RiskLevel.CRITICAL,
                failure=ReplayFailure(
                    kind=FailureKind.NONDETERMINISM,
                    summary="command mismatch during replay",
                    likely_cause="workflow command sequence changed",
                    remediation_hint="add Temporal versioning or patch gates",
                ),
            )
        ],
        artifacts=ArtifactManifest(
            json_report="artifacts/report.json",
            markdown_report="artifacts/report.md",
            html_report="artifacts/report.html",
        ),
        settings=VerificationSettings(
            selection_strategy="all",
            max_histories=50,
            redact_payloads_in_reports=True,
            adapter_mode="local_module",
        ),
    )
