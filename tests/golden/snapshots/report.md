# Replay Gate Report

- Status: **FAILED**
- Project: `payments-workflows`
- Engine: `temporal`
- Histories checked: `1`
- Passed: `0`
- Failed: `1`
- Errors: `0`
- Skipped: `0`

## Policy

- max_failures=0 -> violated (1 observed)

## Results

### PaymentWorkflow / `histories/payment.json`

- Status: `failed`
- Compatibility: `incompatible`
- Risk: `critical`
- Failure kind: `nondeterminism`
- Summary: command mismatch during replay
- Likely cause: workflow command sequence changed
- Remediation: add Temporal versioning or patch gates

## Top Failures

1. `PaymentWorkflow` / `histories/payment.json`
   - kind: `nondeterminism`
   - summary: command mismatch during replay
