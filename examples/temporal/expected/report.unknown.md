# Replay Gate Report

- Status: **FAILED**
- Project: `replay-gate-examples`
- Engine: `temporal`
- Histories checked: `1`
- Passed: `0`
- Failed: `1`
- Errors: `0`
- Skipped: `0`

## Policy

- max_failures=0 -> violated (1 observed)
- max_unknown=0 -> violated (1 observed)
- fail_on=unknown_workflow_type -> violated

## Results

### LegacyWorkflow / `histories/legacy_history.json`

- Status: `failed`
- Compatibility: `unknown`
- Risk: `high`
- Failure kind: `unknown_workflow_type`
- Summary: Workflow type not registered in the verification environment.
- Likely cause: The history references a workflow type that was not loaded from the candidate module.
- Remediation: Register the missing workflow type in the candidate module or exclude that history from this verification run.

## Top Failures

1. `LegacyWorkflow` / `histories/legacy_history.json`
   - kind: `unknown_workflow_type`
   - summary: Workflow type not registered in the verification environment.
