"""Policy evaluation for verification results."""

from __future__ import annotations

from replaygate.config import PolicyConfig
from replaygate.models import (
    CompatibilityStatus,
    PolicyDecision,
    PolicyDecisionValue,
    ReplayResult,
    ReplayStatus,
)


def evaluate_policy(policy: PolicyConfig, results: list[ReplayResult]) -> PolicyDecision:
    failures = sum(result.status in {ReplayStatus.FAILED, ReplayStatus.ERROR} for result in results)
    unknown = sum(result.compatibility_status is CompatibilityStatus.UNKNOWN for result in results)

    violated_rules: list[str] = []

    if failures > policy.max_failures:
        violated_rules.append(
            f"max_failures={policy.max_failures} -> violated ({failures} observed)"
        )

    if unknown > policy.max_unknown:
        violated_rules.append(f"max_unknown={policy.max_unknown} -> violated ({unknown} observed)")

    matched_fail_on = sorted(
        {
            result.failure.kind.value
            for result in results
            if result.failure is not None and result.failure.kind in policy.fail_on
        }
    )
    for failure_kind in matched_fail_on:
        violated_rules.append(f"fail_on={failure_kind} -> violated")

    return PolicyDecision(
        passed=not violated_rules,
        decision=PolicyDecisionValue.PASS if not violated_rules else PolicyDecisionValue.FAIL,
        violated_rules=violated_rules,
        observed_failures=failures,
        observed_unknown=unknown,
    )
