from __future__ import annotations

from datetime import UTC, datetime

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
    WorkflowEngine,
    WorkflowHistoryArtifact,
    WorkflowIdentifier,
)
from replaygate.reporting.console import render_console_summary
from replaygate.reporting.json_report import render_json_report
from replaygate.reporting.markdown_report import render_markdown_report


def sample_report() -> VerificationReport:
    return VerificationReport(
        project_name="payments-workflows",
        engine=WorkflowEngine.TEMPORAL,
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
            errors=0,
        ),
        policy=PolicyDecision(
            passed=False,
            violated_rules=["max_failures=0 -> violated (1 observed)"],
            observed_failures=1,
            observed_unknown=0,
        ),
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
    )


def test_render_json_report_is_stable() -> None:
    rendered = render_json_report(sample_report())

    assert '"project_name": "payments-workflows"' in rendered
    assert '"kind": "nondeterminism"' in rendered


def test_render_markdown_report_contains_failure_details() -> None:
    rendered = render_markdown_report(sample_report())

    assert "# Replay Gate Report" in rendered
    assert "command mismatch during replay" in rendered
    assert "max_failures=0 -> violated (1 observed)" in rendered


def test_render_console_summary_contains_expected_sections() -> None:
    rendered = render_console_summary(sample_report())

    assert "Replay Gate: FAILED" in rendered
    assert "Top failures:" in rendered
    assert "kind: nondeterminism" in rendered
