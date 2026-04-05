# Replay Gate Report

- Status: **FAILED**
- Project: `replay-gate-examples`
- Engine: `temporal`
- Histories checked: `1`
- Passed: `0`
- Failed: `0`
- Errors: `1`
- Skipped: `0`

## Policy

- max_failures=0 -> violated (1 observed)
- max_unknown=0 -> violated (1 observed)
- fail_on=corrupted_history -> violated

## Results

### unknown-workflow / `histories/corrupted_history.json`

- Status: `error`
- Compatibility: `unknown`
- Risk: `medium`
- Failure kind: `corrupted_history`
- Summary: History artifact could not be decoded.
- Likely cause: The file was not valid JSON or did not match the expected Temporal history envelope format.
- Remediation: Regenerate the history fixture with the provided script or repair the artifact format before verifying.

## Top Failures

1. `unknown-workflow` / `histories/corrupted_history.json`
   - kind: `corrupted_history`
   - summary: History artifact could not be decoded.
