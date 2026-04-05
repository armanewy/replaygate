"""Shared compatibility and risk mapping."""

from __future__ import annotations

from replaygate.models import CompatibilityStatus, FailureKind, ReplayStatus, RiskLevel


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


def compatibility_for_failure(failure_kind: FailureKind) -> CompatibilityStatus:
    if failure_kind is FailureKind.NONDETERMINISM:
        return CompatibilityStatus.INCOMPATIBLE
    return CompatibilityStatus.UNKNOWN
