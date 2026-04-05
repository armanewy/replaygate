"""Normalize Temporal replay failures into Replay Gate failure models."""

from __future__ import annotations

from temporalio.workflow import NondeterminismError

from replaygate.models import DeterminismIssue, FailureKind, ReplayFailure

from .models import TemporalHistoryRecord


def classify_loader_failure(
    record: TemporalHistoryRecord,
    *,
    redact_payloads: bool,
) -> ReplayFailure:
    details: dict[str, str] = {}
    if not redact_payloads and record.loader_error_message is not None:
        details["raw_error"] = record.loader_error_message

    return ReplayFailure(
        kind=record.loader_error_kind or FailureKind.CORRUPTED_HISTORY,
        summary="History artifact could not be decoded.",
        likely_cause=(
            "The file was not valid JSON or did not match the expected "
            "Temporal history envelope format."
        ),
        remediation_hint=(
            "Regenerate the history fixture with the provided script or "
            "repair the artifact format before verifying."
        ),
        exception_type="HistoryDecodeError",
        details=details,
    )


def classify_replay_failure(
    exc: Exception,
    *,
    redact_payloads: bool,
) -> ReplayFailure:
    message = str(exc)
    lower_message = message.lower()
    details: dict[str, str] = {}
    if not redact_payloads:
        details["raw_error"] = message

    if isinstance(exc, NondeterminismError) or "nondeterminism error" in lower_message:
        return ReplayFailure(
            kind=FailureKind.NONDETERMINISM,
            summary="Replay failed due to a command mismatch during replay.",
            likely_cause=(
                "The candidate workflow emitted a different command sequence "
                "than the historical execution."
            ),
            remediation_hint=(
                "Review recent workflow code changes and add Temporal versioning "
                "or patch gates before deploying."
            ),
            exception_type=type(exc).__name__,
            determinism_issue=DeterminismIssue(
                summary="Temporal detected nondeterministic replay behavior.",
                likely_cause=(
                    "A timer, activity, child workflow, or other workflow command "
                    "changed relative to the recorded history."
                ),
                remediation_hint=(
                    "Preserve the old code path for existing histories or add "
                    "explicit workflow versioning."
                ),
            ),
            details=details,
        )

    if "is not registered on this worker" in lower_message or "notfounderror" in lower_message:
        return ReplayFailure(
            kind=FailureKind.UNKNOWN_WORKFLOW_TYPE,
            summary="Workflow type not registered in the verification environment.",
            likely_cause=(
                "The history references a workflow type that was not loaded "
                "from the candidate module."
            ),
            remediation_hint=(
                "Register the missing workflow type in the candidate module or "
                "exclude that history from this verification run."
            ),
            exception_type=type(exc).__name__,
            details=details,
        )

    if "payload" in lower_message and (
        "decode" in lower_message or "codec" in lower_message or "converter" in lower_message
    ):
        return ReplayFailure(
            kind=FailureKind.PAYLOAD_DECODE_ERROR,
            summary="Replay could not decode one or more payloads from the history artifact.",
            likely_cause=(
                "The verification environment is missing a compatible codec or "
                "the history payload encoding differs from local expectations."
            ),
            remediation_hint=(
                "Configure the required payload codec or regenerate fixtures with "
                "plain payloads for local verification."
            ),
            exception_type=type(exc).__name__,
            details=details,
        )

    return ReplayFailure(
        kind=FailureKind.ADAPTER_ERROR,
        summary="Temporal replay failed with an adapter error.",
        likely_cause=(
            "The Temporal SDK raised an unexpected error that Replay Gate "
            "could not classify more specifically."
        ),
        remediation_hint=(
            "Inspect the raw adapter error, then fix the workflow module or "
            "history artifact before relying on this result."
        ),
        exception_type=type(exc).__name__,
        details=details,
    )
