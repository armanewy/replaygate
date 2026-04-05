# Replay Gate Report

- Status: **FAILED**
- Project: `replay-gate-examples`
- Engine: `temporal`
- Histories checked: `2`
- Passed: `1`
- Failed: `1`
- Errors: `0`
- Skipped: `0`

## Policy

- max_failures=0 -> violated (1 observed)
- fail_on=nondeterminism -> violated

## Results

### PaymentWorkflow / `histories/payment_history.json`

- Status: `failed`
- Compatibility: `incompatible`
- Risk: `critical`
- Failure kind: `nondeterminism`
- Summary: Replay failed due to a command mismatch during replay.
- Likely cause: The candidate workflow emitted a different command sequence than the historical execution.
- Remediation: Review recent workflow code changes and add Temporal versioning or patch gates before deploying.

### RefundWorkflow / `histories/refund_history.json`

- Status: `passed`
- Compatibility: `compatible`
- Risk: `low`

## Top Failures

1. `PaymentWorkflow` / `histories/payment_history.json`
   - kind: `nondeterminism`
   - summary: Replay failed due to a command mismatch during replay.
