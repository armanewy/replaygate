from __future__ import annotations

from replaygate.config import PolicyConfig
from replaygate.models import (
    CompatibilityStatus,
    FailureKind,
    ReplayFailure,
    ReplayResult,
    ReplayStatus,
    RiskLevel,
    WorkflowEngine,
    WorkflowHistoryArtifact,
    WorkflowIdentifier,
)
from replaygate.policy import evaluate_policy


def make_result(
    *,
    status: ReplayStatus,
    compatibility: CompatibilityStatus,
    failure_kind: FailureKind | None = None,
) -> ReplayResult:
    return ReplayResult(
        artifact=WorkflowHistoryArtifact(
            engine=WorkflowEngine.TEMPORAL,
            path="histories/sample.json",
            source_kind="filesystem",
            checksum_sha256="abc",
            size_bytes=10,
            workflow=WorkflowIdentifier(workflow_id="wf-1", workflow_type="PaymentWorkflow"),
        ),
        workflow_type="PaymentWorkflow",
        status=status,
        compatibility_status=compatibility,
        risk_level=RiskLevel.HIGH,
        failure=(
            ReplayFailure(
                kind=failure_kind,
                summary="failure",
                likely_cause="cause",
                remediation_hint="hint",
            )
            if failure_kind is not None
            else None
        ),
    )


def test_policy_passes_when_thresholds_not_exceeded() -> None:
    decision = evaluate_policy(
        PolicyConfig(fail_on=[], max_unknown=1, max_failures=1),
        [
            make_result(
                status=ReplayStatus.PASSED,
                compatibility=CompatibilityStatus.COMPATIBLE,
            )
        ],
    )

    assert decision.passed is True
    assert decision.violated_rules == []


def test_policy_fails_on_failure_kind_and_thresholds() -> None:
    decision = evaluate_policy(
        PolicyConfig(
            fail_on=[FailureKind.NONDETERMINISM],
            max_unknown=0,
            max_failures=0,
        ),
        [
            make_result(
                status=ReplayStatus.FAILED,
                compatibility=CompatibilityStatus.INCOMPATIBLE,
                failure_kind=FailureKind.NONDETERMINISM,
            ),
            make_result(
                status=ReplayStatus.ERROR,
                compatibility=CompatibilityStatus.UNKNOWN,
                failure_kind=FailureKind.CORRUPTED_HISTORY,
            ),
        ],
    )

    assert decision.passed is False
    assert "max_failures=0 -> violated (2 observed)" in decision.violated_rules
    assert "max_unknown=0 -> violated (1 observed)" in decision.violated_rules
    assert "fail_on=nondeterminism -> violated" in decision.violated_rules
